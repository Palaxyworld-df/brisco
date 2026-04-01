import streamlit as st
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import tempfile
from datetime import datetime

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
# DATABASE SETUP
# ---------------------------
conn = sqlite3.connect("brisco.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS scores (
    timestamp TEXT,
    user_id TEXT,
    rater_id TEXT,
    case_id TEXT,
    segmentation_method TEXT,

    scan_excluded TEXT,
    exclusion_reason TEXT,
    fat_suppression TEXT,
    fat_suppression_quality INTEGER,

    single_lesion TEXT,
    mass_enhancement TEXT,
    non_mass_enhancement TEXT,
    satellite_lesions TEXT,
    num_satellites INTEGER,
    nodular_unclear TEXT,
    necrosis TEXT,

    strong_bpe TEXT,

    satellite_included_omitted TEXT,
    num_satellites_included INTEGER,
    required_additions INTEGER,
    required_deletions INTEGER,
    complex_corrections TEXT,
    overall_quality INTEGER,

    fp_vessels INTEGER,
    fp_nodes INTEGER,
    fp_nodular INTEGER,
    fp_shape INTEGER,
    fp_skin INTEGER,
    fp_nipple INTEGER,
    fp_nme INTEGER,
    fp_satellites INTEGER,

    fn_necrosis TEXT
)
""")

conn.commit()

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
# SAVE TO DATABASE
# ---------------------------
if submitted:
    cursor.execute("""
    INSERT INTO scores VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(),
        user_id,
        rater_id,
        case_id,
        segmentation_method,

        scan_excluded,
        exclusion_reason,
        fat_suppression,
        fat_suppression_quality,

        single_lesion,
        mass_enhancement,
        non_mass_enhancement,
        satellite_lesions,
        num_satellites,
        nodular_unclear,
        necrosis,

        strong_bpe,

        satellite_included_omitted,
        num_satellites_included,
        required_additions,
        required_deletions,
        complex_corrections,
        overall_quality,

        int(fp_vessels),
        int(fp_nodes),
        int(fp_nodular),
        int(fp_shape),
        int(fp_skin),
        int(fp_nipple),
        int(fp_nme),
        int(fp_satellites),

        fn_necrosis
    ))

    conn.commit()

    st.success("✅ Assessment saved successfully!")