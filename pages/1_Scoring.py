import streamlit as st
import nibabel as nib
import tempfile
from supabase import create_client
import numpy as np
from PIL import Image

st.set_page_config(page_title="BRISCO", layout="wide")

# -------------------------
# AUTH CHECK
# -------------------------
if "user_id" not in st.session_state:
    st.warning("Please login from the home page")
    st.stop()

user_id = st.session_state.user_id
st.title("BRISCO Form")

# -------------------------
# FILE UPLOADER
# -------------------------
mri_file = st.file_uploader("Upload MRI scan (.nii / .nii.gz allowed)", type=["nii", "nii.gz"])
mask_file = st.file_uploader("Upload segmentation mask (.nii / .nii.gz allowed)", type=["nii", "nii.gz"])

@st.cache_data
def load_nifti(uploaded_file):
    suffix = ".nii.gz" if uploaded_file.name.endswith(".gz") else ".nii"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name
    img = nib.load(tmp_path)
    return img.get_fdata()

mri = load_nifti(mri_file) if mri_file else None
mask = load_nifti(mask_file) if mask_file else None

# -------------------------
# IMAGE PROCESSING
# -------------------------
def get_slice_rgb(image, mask=None, slice_idx=0, alpha=0.4):
    slice_gray = image[:, :, slice_idx]
    slice_gray = np.nan_to_num(slice_gray, nan=0.0)
    min_val = slice_gray.min()
    max_val = slice_gray.max()
    if max_val - min_val == 0:
        max_val = min_val + 1e-8
    slice_gray = ((slice_gray - min_val) / (max_val - min_val) * 255).astype(np.uint8)
    slice_rgb = np.stack([slice_gray]*3, axis=-1)

    if mask is not None:
        try:
            mask_slice = mask[:, :, slice_idx]
            mask_slice = np.nan_to_num(mask_slice, nan=0.0)
            mask_rgb = np.zeros_like(slice_rgb)
            mask_rgb[..., 0] = (mask_slice * 255).astype(np.uint8)
            slice_rgb = ((1-alpha)*slice_rgb + alpha*mask_rgb).astype(np.uint8)
        except:
            pass
    return Image.fromarray(slice_rgb)

# -------------------------
# MAIN LAYOUT WITH COLUMNS
# -------------------------
col1, col2 = st.columns([1, 2])  # left 1/3, right 2/3

# --- Left column: MRI viewer (large image) ---
with col1:
    if mri is not None:
        st.subheader("MRI Viewer")
        slice_idx = st.slider(
            "Slice index",
            0,
            mri.shape[2]-1,
            mri.shape[2]//2,
            key="slice_slider"
        )
        alpha = st.slider(
            "Mask opacity",
            0.0,
            1.0,
            0.4,
            key="alpha_slider"
        )
        pil_img = get_slice_rgb(mri, mask, slice_idx, alpha)
        # 🔥 Make image bigger by using column width and enlarging DPI
        st.image(pil_img, use_column_width=True, output_format="PNG")

# --- Right column: FORM ---
with col2:
    with st.form("qc_form"):
        # -----------------------
        # Section 1
        # -----------------------
        with st.expander("Scan eligibility and image quality", expanded=True):
            scan_excluded = st.radio("Scan excluded", ["No", "Yes"])
            exclusion_reason = st.text_area("Reason for exclusion")
            fat_suppression = st.radio("Fat suppression applied", ["Yes", "No"])
            fat_suppression_quality = st.select_slider(
                "Fat suppression quality",
                options=[0, 1, 2, 3],
                format_func=lambda x: ["None", "Minor Failure", "Moderate Failure", "Major Failure"][x]
            )

        # -----------------------
        # Section 2
        # -----------------------
        with st.expander("Tumour morphology", expanded=True):
            single_lesion = st.radio("Single contiguous lesion", ["Yes", "No"])
            mass_enhancement = st.radio("Mass enhancement present", ["Yes", "No"])
            non_mass_enhancement = st.radio("Non-mass enhancement present", ["Yes", "No"])
            satellite_lesions = st.radio("Satellite lesions present", ["Yes", "No"])
            num_satellites = st.number_input("Number of satellite lesions", min_value=0, step=1)
            nodular_unclear = st.radio("Nodular enhancement of unclear significance", ["Yes", "No"])
            necrosis = st.radio("Intratumoural necrosis present", ["Yes", "No"])

        # -----------------------
        # Section 3
        # -----------------------
        with st.expander("Segmentation quality assessment", expanded=True):
            satellite_included_omitted = st.radio("Satellite lesions included or omitted", ["Included", "Omitted"])
            num_satellites_included = st.number_input("Number of satellite lesions included", min_value=0, step=1)
            required_additions = st.select_slider(
                "Required additions (under-segmentation)",
                options=[0, 1, 2, 3, 4],
                format_func=lambda x: [
                    "Acceptable - No deletion required",
                    "Minor correction (≤25% of volume to be deleted)",
                    "Intermediate correction (25–≤50% of volume to be deleted)",
                    "Major correction (50–≤75% of volume to be deleted)",
                    "Not acceptable (>75% of volume to be deleted)"
                ][x]
            )
            required_deletions = st.select_slider(
                "Required deletions (over-segmentation)",
                options=[0, 1, 2, 3, 4],
                format_func=lambda x: [
                    "Acceptable - No addition required",
                    "Minor correction (≤25% of volume to be added)",
                    "Intermediate correction (25–≤50% to be added)",
                    "Major correction (50–≤75% to be added)",
                    "Not acceptable (>75% to be added)"
                ][x]
            )
            complex_corrections = st.radio("Low-volume but complex corrections required", ["Yes", "No"])
            overall_quality = st.select_slider(
                "Overall segmentation quality",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: ["Acceptable", "Minor issues", "Moderate issues", "Major issues", "Not acceptable"][x-1]
            )

        # -----------------------
        # Section 4
        # -----------------------
        with st.expander("Causes for false positives", expanded=True):
            fp_vessels = st.checkbox("Blood vessels")
            fp_nodes = st.checkbox("Lymph nodes")
            fp_nodular = st.checkbox("Nodular enhancement")
            fp_shape = st.checkbox("Complex lesion shape")
            fp_skin = st.checkbox("Skin")
            fp_nipple = st.checkbox("Nipple–areolar complex")
            fp_nme = st.checkbox("Non-mass enhancement")
            fp_satellites = st.checkbox("Satellite lesions")
            fp_additional = st.text_input("Other causes for false positives (optional)")

        # -----------------------
        # Section 5
        # -----------------------
        with st.expander("Causes for false negatives", expanded=True):
            fn_necrosis = st.radio("Necrosis / fibrosis", ["Yes", "No"])
            fn_additional = st.text_input("Other causes for false negatives (optional)")

        submitted = st.form_submit_button("Save Assessment")

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.header("Session Info")
st.sidebar.write(f"**User ID:** {user_id}")
rater_id = st.sidebar.text_input("Rater ID")
case_id = st.sidebar.text_input("Case ID")
segmentation_options = ["Manual"]
selected_method = st.sidebar.selectbox("Segmentation Method", segmentation_options + ["Other"])
if selected_method == "Other":
    segmentation_method = st.sidebar.text_input("Enter the name of your segmentation method")
else:
    segmentation_method = selected_method
st.sidebar.write(f"Selected segmentation method: {segmentation_method}")
