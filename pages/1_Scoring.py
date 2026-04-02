import streamlit as st
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import tempfile
from datetime import datetime

# -------supabase----------
from supabase import create_client

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

st.set_page_config(page_title="BRISCo Scoring", layout="wide")
st.title("BRISCo - Breast MRI Segmentation Scoring")

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
    fig, ax = plt.subplots()
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
segmentation_method = st.sidebar.selectbox(
    "Segmentation Method",
    ["Manual", "Model A", "Model B"]
)
case_id = st.sidebar.text_input("Case ID")

# ---------------------------
# FILE UPLOAD
# ---------------------------
st.header("Upload MRI & Segmentation")

col1, col2 = st.columns(2)

with col1:
    mri_file = st.file_uploader("Upload MRI (.nii / .nii.gz)", type=["nii", "nii.gz"])

with col2:
    mask_file = st.file_uploader("Upload Mask (.nii / .nii.gz)", type=["nii", "nii.gz"])

mri = load_nifti(mri_file) if mri_file else None
mask = load_nifti(mask_file) if mask_file else None

# ---------------------------
# VIEWER
# ---------------------------
if mri is not None:
    st.subheader("MRI Viewer")

    slice_idx = st.slider("Slice Index", 0, mri.shape[2] - 1, mri.shape[2] // 2)
    alpha = st.slider("Mask Opacity", 0.0, 1.0, 0.4)

    fig = overlay_slice(mri, mask, slice_idx, alpha)
    st.pyplot(fig)

# ---------------------------
# SCORING FORM
# ---------------------------
st.header("Scoring Form")

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
    num_satellites = st.number_input("Number of satellite lesions", min_value=0)

    nodular_unclear = st.radio("Nodular enhancement unclear", ["Yes", "No"])
    necrosis = st.radio("Intratumoural necrosis", ["Yes", "No"])

    st.subheader("Background tissue")

    strong_bpe = st.radio("Strong BPE present", ["Yes", "No"])

    st.subheader("Segmentation quality")

    satellite_included_omitted = st.radio(
        "Satellite lesions",
        ["Included", "Omitted"]
    )

    num_satellites_included = st.number_input("Satellites included", min_value=0)

    required_additions = st.slider("Under-segmentation (additions)", 0, 4)
    required_deletions = st.slider("Over-segmentation (deletions)", 0, 4)

    complex_corrections = st.radio("Complex corrections needed", ["Yes", "No"])

    overall_quality = st.slider("Overall quality", 1, 5)

    st.subheader("False positives")

    fp_vessels = st.checkbox("Blood vessels")
    fp_nodes = st.checkbox("Lymph nodes")
    fp_nodular = st.checkbox("Nodular enhancement")
    fp_shape = st.checkbox("Complex shape")
    fp_skin = st.checkbox("Skin")
    fp_nipple = st.checkbox("Nipple")
    fp_nme = st.checkbox("Non-mass enhancement")
    fp_satellites = st.checkbox("Satellite lesions")

    st.subheader("False negatives")

    fn_necrosis = st.radio("Missed necrosis", ["Yes", "No"])

    submitted = st.form_submit_button("Save Assessment")

# ---------------------------
# SAVE
# ---------------------------
if submitted:

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

    st.success("Saved!")

# ---------------------------
# LOAD USER DATA
# ---------------------------
st.subheader("My Previous Assessments")

response = supabase.table("scores")\
    .select("*")\
    .eq("user_id", user_id)\
    .execute()

df = pd.DataFrame(response.data)

if not df.empty:
    st.dataframe(df)

    # CSV DOWNLOAD
    csv = df.to_csv(index=False)

    st.download_button(
        "Download My Data",
        csv,
        "my_scores.csv",
        "text/csv"
    )
else:
    st.info("No data yet")
