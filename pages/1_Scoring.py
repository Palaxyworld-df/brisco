import streamlit as st
import nibabel as nib
import tempfile
import numpy as np
import pandas as pd
from PIL import Image
from datetime import datetime
from supabase import create_client

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="BRISCO", layout="wide")

# -------------------------
# SUPABASE SETUP
# -------------------------
# -------supabase---------- 
url = st.secrets["SUPABASE_URL"] 
key = st.secrets["SUPABASE_KEY"] 
supabase = create_client(url, key)


# -------------------------
# AUTH CHECK
# -------------------------
if "user_id" not in st.session_state:
    st.warning("Please login from the home page")
    st.stop()

user_id = st.session_state.user_id
st.title("BRISCO Form (Stepper)")

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
# INITIALIZE STATE
# -------------------------
if "step" not in st.session_state:
    st.session_state.step = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}

# -------------------------
# FORM STEPS
# -------------------------
def step_0():
    st.header("Step 1: Scan eligibility and image quality")
    st.session_state.answers["scan_excluded"] = st.radio("Scan excluded", ["No", "Yes"])
    st.session_state.answers["exclusion_reason"] = st.text_area("Reason for exclusion")
    st.session_state.answers["fat_suppression"] = st.radio("Fat suppression applied", ["Yes", "No"])
    st.session_state.answers["fat_suppression_quality"] = st.select_slider(
        "Fat suppression quality",
        options=[0,1,2,3],
        format_func=lambda x: ["None","Minor Failure","Moderate Failure","Major Failure"][x]
    )

def step_1():
    st.header("Step 2: Tumour morphology")
    st.session_state.answers["single_lesion"] = st.radio("Single contiguous lesion", ["Yes","No"])
    st.session_state.answers["mass_enhancement"] = st.radio("Mass enhancement present", ["Yes","No"])
    st.session_state.answers["non_mass_enhancement"] = st.radio("Non-mass enhancement present", ["Yes","No"])
    st.session_state.answers["satellite_lesions"] = st.radio("Satellite lesions present", ["Yes","No"])
    st.session_state.answers["num_satellites"] = st.number_input("Number of satellite lesions", min_value=0, step=1)
    st.session_state.answers["nodular_unclear"] = st.radio("Nodular enhancement of unclear significance", ["Yes","No"])
    st.session_state.answers["necrosis"] = st.radio("Intratumoural necrosis present", ["Yes","No"])

def step_2():
    st.header("Step 3: Segmentation quality assessment")
    st.session_state.answers["satellite_included_omitted"] = st.radio("Satellite lesions included or omitted", ["Included","Omitted"])
    st.session_state.answers["num_satellites_included"] = st.number_input("Number of satellite lesions included", min_value=0, step=1)
    st.session_state.answers["required_additions"] = st.select_slider(
        "Required additions (under-segmentation)", options=[0,1,2,3,4],
        format_func=lambda x: ["Acceptable","Minor correction","Intermediate correction","Major correction","Not acceptable"][x]
    )
    st.session_state.answers["required_deletions"] = st.select_slider(
        "Required deletions (over-segmentation)", options=[0,1,2,3,4],
        format_func=lambda x: ["Acceptable","Minor correction","Intermediate correction","Major correction","Not acceptable"][x]
    )
    st.session_state.answers["complex_corrections"] = st.radio("Low-volume but complex corrections required", ["Yes","No"])
    st.session_state.answers["overall_quality"] = st.select_slider(
        "Overall segmentation quality", options=[1,2,3,4,5],
        format_func=lambda x: ["Acceptable","Minor issues","Moderate issues","Major issues","Not acceptable"][x-1]
    )

def step_3():
    st.header("Step 4: Causes for false positives")
    st.session_state.answers["fp_vessels"] = st.checkbox("Blood vessels")
    st.session_state.answers["fp_nodes"] = st.checkbox("Lymph nodes")
    st.session_state.answers["fp_nodular"] = st.checkbox("Nodular enhancement")
    st.session_state.answers["fp_shape"] = st.checkbox("Complex lesion shape")
    st.session_state.answers["fp_skin"] = st.checkbox("Skin")
    st.session_state.answers["fp_nipple"] = st.checkbox("Nipple–areolar complex")
    st.session_state.answers["fp_nme"] = st.checkbox("Non-mass enhancement")
    st.session_state.answers["fp_satellites"] = st.checkbox("Satellite lesions")
    st.session_state.answers["fp_additional"] = st.text_input("Other causes for false positives (optional)")

def step_4():
    st.header("Step 5: Causes for false negatives")
    st.session_state.answers["fn_necrosis"] = st.radio("Necrosis / fibrosis", ["Yes","No"])
    st.session_state.answers["fn_additional"] = st.text_input("Other causes for false negatives (optional)")

steps = [step_0, step_1, step_2, step_3, step_4]

# -------------------------
# LAYOUT: MRI | FORM
# -------------------------
col1, col2 = st.columns([1,1], gap="medium")

with col1:
    st.subheader("MRI Viewer")
    if mri is not None:
        slice_idx = st.slider("Slice index", 0, mri.shape[2]-1, mri.shape[2]//2)
        alpha = st.slider("Mask opacity", 0.0, 1.0, 0.4)
        pil_img = get_slice_rgb(mri, mask, slice_idx, alpha)
        target_h = 800
        scale_factor = target_h / pil_img.size[1]
        target_w = int(pil_img.size[0] * scale_factor)
        pil_img_resized = pil_img.resize((target_w, target_h))
        st.image(pil_img_resized, use_column_width=False)

with col2:
    # Metadata inputs
    rater_id = st.text_input("Rater ID", key="rater_id")
    case_id = st.text_input("Case ID", key="case_id")
    segmentation_options = ["Manual"]
    selected_method = st.selectbox("Segmentation Method", segmentation_options + ["Other"])
    if selected_method == "Other":
        segmentation_method = st.text_input("Enter the name of your segmentation method")
    else:
        segmentation_method = selected_method

    # Render current step
    steps[st.session_state.step]()

    # Navigation buttons
    col_prev, col_next = st.columns([1,1])
    with col_prev:
        if st.session_state.step > 0:
            if st.button("Previous"):
                st.session_state.step -= 1
    with col_next:
        if st.session_state.step < len(steps)-1:
            if st.button("Next"):
                st.session_state.step += 1
        else:
            if st.button("Submit"):
                # ---------------------------
                # SAVE TO SUPABASE
                # ---------------------------
                if rater_id.strip() == "" or case_id.strip() == "":
                    st.warning("Please fill Case ID and Rater ID")
                    st.stop()
                try:
                    # Merge answers + metadata
                    data_to_save = st.session_state.answers.copy()
                    data_to_save.update({
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user_id,
                        "rater_id": rater_id,
                        "case_id": case_id,
                        "segmentation_method": segmentation_method
                    })
                    supabase.table("scores").insert(data_to_save).execute()
                    st.success("✅ Assessment saved successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to save data: {e}")

# -------------------------
# LOAD PREVIOUS ASSESSMENTS
# -------------------------
st.subheader("My Previous Assessments")
try:
    response = supabase.table("scores").select("*").eq("user_id", user_id).execute()
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
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
