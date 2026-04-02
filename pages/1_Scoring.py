import streamlit as st
import nibabel as nib
import matplotlib.pyplot as plt
import tempfile
from datetime import datetime
from supabase import create_client
import numpy as np
from PIL import Image
import numpy as np
import streamlit as st

st.set_page_config(page_title="BRISCO", layout="wide")

# --- Supabase connection ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

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
# MRI Viewer with fixed aspect ratio
# -------------------------
import streamlit as st
import numpy as np

def overlay_slice_to_rgb(image, mask=None, slice_idx=0, alpha=0.4):
    """Return an RGB image of the MRI slice with optional mask overlay"""
    slice_gray = image[:, :, slice_idx]
    # Normalize to 0-255
    slice_gray = (255 * (slice_gray - slice_gray.min()) / (slice_gray.ptp() + 1e-8)).astype(np.uint8)
    slice_rgb = np.stack([slice_gray]*3, axis=-1)

    if mask is not None:
        mask_slice = mask[:, :, slice_idx]
        # Create a red overlay
        mask_rgb = np.zeros_like(slice_rgb)
        mask_rgb[..., 0] = (mask_slice * 255).astype(np.uint8)  # red channel
        slice_rgb = ((1-alpha)*slice_rgb + alpha*mask_rgb).astype(np.uint8)

    return slice_rgb

# Example MRI and mask
mri = np.random.rand(180, 180, 60)
mask = np.random.randint(0,2,(180,180,60))

slice_idx = 30
mri_rgb = overlay_slice_to_rgb(mri, mask, slice_idx, alpha=0.4)

# Display in Streamlit with fixed width
st.image(mri_rgb, width=400)  # width in pixels; adjust as needed

# -------------------------
# Sidebar session info
# -------------------------
st.sidebar.header("Session Info")
st.sidebar.write(f"**User ID:** {user_id}")
rater_id = st.sidebar.text_input("Rater ID")
case_id = st.sidebar.text_input("Case ID")

segmentation_options = ["Manual", "Model A", "Model B"]
selected_method = st.sidebar.selectbox("Segmentation Method", segmentation_options + ["Other"])
if selected_method == "Other":
    segmentation_method = st.sidebar.text_input("Enter your segmentation method")
else:
    segmentation_method = selected_method

st.sidebar.write(f"Selected segmentation method: {segmentation_method}")

# -------------------------
# Form split into expanders (no vertical scrolling)
# -------------------------
with st.form("qc_form"):
    # Section 1
    with st.expander("Scan eligibility and image quality", expanded=True):
        scan_excluded = st.radio("Scan excluded", ["No", "Yes"])
        exclusion_reason = st.text_area("Reason for exclusion")
        fat_suppression = st.radio("Fat suppression applied", ["Yes", "No"])
        fat_suppression_quality = st.select_slider(
            "Fat suppression quality",
            options=[0, 1, 2, 3],
            format_func=lambda x: ["None", "Minor Failure", "Moderate Failure", "Major Failure"][x]
        )

    # Section 2
    with st.expander("Tumour morphology", expanded=True):
        single_lesion = st.radio("Single contiguous lesion", ["Yes", "No"])
        mass_enhancement = st.radio("Mass enhancement present", ["Yes", "No"])
        non_mass_enhancement = st.radio("Non-mass enhancement present", ["Yes", "No"])
        satellite_lesions = st.radio("Satellite lesions present", ["Yes", "No"])
        num_satellites = st.number_input("Number of satellite lesions", min_value=0, step=1)
        nodular_unclear = st.radio("Nodular enhancement of unclear significance", ["Yes", "No"])
        necrosis = st.radio("Intratumoural necrosis present", ["Yes", "No"])

    # Section 3
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

    # Section 4
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

    # Section 5
    with st.expander("Causes for false negatives", expanded=True):
        fn_necrosis = st.radio("Necrosis / fibrosis", ["Yes", "No"])
        fn_additional = st.text_input("Other causes for false negatives (optional)")

    submitted = st.form_submit_button("Save Assessment")
