import streamlit as st
import nibabel as nib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="BRISCO", layout="wide")

# ------- Supabase ---------- 
url = st.secrets["SUPABASE_URL"] 
key = st.secrets["SUPABASE_KEY"] 
supabase = create_client(url, key)

# ---------------------------
# AUTH CHECK
# ---------------------------
if "user_id" not in st.session_state:
    st.warning("Please login from the home page")
    st.stop()

user_id = st.session_state.user_id

st.title("BRISCO Form")

# ---------------------------
# FILE LOADER
# ---------------------------
@st.cache_data
def load_nifti(uploaded_file):
    suffix = ".nii.gz" if uploaded_file.name.endswith(".gz") else ".nii"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    img = nib.load(tmp_path)
    return img.get_fdata()

def overlay_slice(image, mask, slice_idx, alpha):
    fig, ax = plt.subplots(figsize=(8, 8))  # larger figure
    ax.imshow(image[:, :, slice_idx], cmap="gray")
    if mask is not None:
        ax.imshow(mask[:, :, slice_idx], cmap="jet", alpha=alpha)
    ax.axis("off")
    return fig

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.header("Session Info")
st.sidebar.write(f"**User ID:** {user_id}")

rater_id = st.sidebar.text_input("Rater ID")
case_id = st.sidebar.text_input("Case ID")

segmentation_options = ["Manual"]

# Dropdown for predefined methods (in sidebar)
selected_method = st.sidebar.selectbox(
    "Segmentation Method",
    options=segmentation_options + ["Other"]  # Add "Other" option
)

# If user selects "Other", show text input (also in sidebar)
if selected_method == "Other":
    custom_method = st.sidebar.text_input("Enter your segmentation method")
    segmentation_method = custom_method if custom_method else None
else:
    segmentation_method = selected_method

st.sidebar.write(f"Selected segmentation method: {segmentation_method}")

# ---------------------------
# FILE UPLOAD
# ---------------------------
st.header("Upload MRI scan and its segmentation mask")

col_upload_mri, col_upload_mask = st.columns(2)

with col_upload_mri:
    mri_file = st.file_uploader("Upload MRI scan (.nii / .nii.gz allowed)", type=["nii", "nii.gz"])

with col_upload_mask:
    mask_file = st.file_uploader("Upload mask (.nii / .nii.gz allowed)", type=["nii", "nii.gz"])

mri = load_nifti(mri_file) if mri_file else None
mask = load_nifti(mask_file) if mask_file else None

# ---------------------------
# SIDE-BY-SIDE VIEWER AND FORM
# ---------------------------
col1, col2 = st.columns([1, 1])  # equal width

with col1:
    if mri is not None:
        st.subheader("MRI Viewer")
        slice_idx = st.slider("Slice index", 0, mri.shape[2] - 1, mri.shape[2] // 2)
        alpha = st.slider("Mask Opacity", 0.0, 1.0, 0.4)
        fig = overlay_slice(mri, mask, slice_idx, alpha)
        st.pyplot(fig)

with col2:
    with st.expander("Fill QC / Segmentation Assessment Form", expanded=True):
        with st.form("qc_form"):
            st.subheader("Scan eligibility and image quality")
            scan_excluded = st.radio("Scan excluded", ["No", "Yes"])
            exclusion_reason = st.text_area("Reason for exclusion")
            fat_suppression = st.radio("Fat suppression applied", ["Yes", "No"])
            fat_suppression_quality = st.select_slider(
                "Fat suppression quality",
                options=[0, 1, 2, 3],
                format_func=lambda x: ["None", "Minor Failure", "Moderate Failure", "Major Failure"][x]
            )

            st.subheader("Tumour morphology")
            single_lesion = st.radio("Single contiguous lesion", ["Yes", "No"])
            mass_enhancement = st.radio("Mass enhancement present", ["Yes", "No"])
            non_mass_enhancement = st.radio("Non-mass enhancement present", ["Yes", "No"])
            satellite_lesions = st.radio("Satellite lesions present", ["Yes", "No"])
            num_satellites = st.number_input("Number of satellite lesions", min_value=0, step=1)
            nodular_unclear = st.radio("Nodular enhancement of unclear significance", ["Yes", "No"])
            necrosis = st.radio("Intratumoural necrosis present", ["Yes", "No"])

            st.subheader("Background breast tissue")
            strong_bpe = st.radio(
                "Strong or Patchy Background Parenchymal Enhancement (BPE) as per ACR BPE 3–4",
                ["Yes", "No"]
            )

            st.subheader("Segmentation quality assessment")
            satellite_included_omitted = st.radio(
                "Satellite lesions included or omitted",
                ["Included", "Omitted"]
            )
            num_satellites_included = st.number_input(
                "Number of satellite lesions included",
                min_value=0,
                step=1
            )
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
            complex_corrections = st.radio(
                "Low-volume but complex corrections required",
                ["Yes", "No"]
            )
            overall_quality = st.select_slider(
                "Overall segmentation quality",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: [
                    "Acceptable",
                    "Minor issues",
                    "Moderate issues",
                    "Major issues",
                    "Not acceptable"
                ][x - 1]
            )

            st.subheader("Causes for false positives segmentation")
            fp_vessels = st.checkbox("Blood vessels")
            fp_nodes = st.checkbox("Lymph nodes")
            fp_nodular = st.checkbox("Nodular enhancement")
            fp_shape = st.checkbox("Complex lesion shape")
            fp_skin = st.checkbox("Skin")
            fp_nipple = st.checkbox("Nipple–areolar complex")
            fp_nme = st.checkbox("Non-mass enhancement")
            fp_satellites = st.checkbox("Satellite lesions")
            fp_additional = st.text_input("Other causes for false positives (optional)")

            st.subheader("Causes for false negative segmentation")
            fn_necrosis = st.radio("Necrosis / fibrosis", ["Yes", "No"])
            fn_additional = st.text_input("Other causes for false negatives (optional)")

            submitted = st.form_submit_button("Click me to save your assessment")

# ---------------------------
# SAVE
# ---------------------------
if submitted:
    if case_id.strip() == "" or rater_id.strip() == "":
        st.warning("Please fill Case ID and Rater ID")
        st.stop()

    try:
        supabase.table("scores").insert({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "rater_id": rater_id,
            "case_id": case_id,
            "segmentation_method": segmentation_method,
            "scan_excluded": scan_excluded,
            "fat_suppression": fat_suppression,
            "fat_suppression_quality": fat_suppression_quality,
            "overall_quality": overall_quality
        }).execute()
        st.success("✅ Assessment saved successfully!")
    except Exception as e:
        st.error("❌ Failed to save data")

# ---------------------------
# LOAD USER DATA
# ---------------------------
st.subheader("My Previous Assessments")

try:
    response = supabase.table("scores")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()

    df = pd.DataFrame(response.data if response.data else [])

    if not df.empty:
        st.dataframe(df)
        csv = df.to_csv(index=False)
        st.download_button(
            "Download My Data",
            csv,
            "my_scores.csv",
            "text/csv"
        )
    else:
        st.info("No data yet")
except:
    st.error("❌ Failed to load data")
