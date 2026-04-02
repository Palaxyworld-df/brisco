# ---------------------------
# Scoring form
# ---------------------------
st.header("Form")

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
    "Strong or Patchy Background Parenchymal Enhancement (BPE) as per [American College of Radiology (ACR) BPE 3–4](https://breastrads.com/wp-content/uploads/2022/02/BIRADS-Reference-Card.pdf)",
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
        format_func=lambda x: ["Acceptable - No deletion required", "Minor correction (≤25% of volume to be deleted)", "Intermediate correction (25–≤50% of volume to be deleted)", "Major correction (50–≤75% of volume to be deleted)", "Not acceptable (>75% of volume to be deleted)"][x]
    )

    required_deletions = st.select_slider(
        "Required deletions (over-segmentation)",
        options=[0, 1, 2, 3, 4],
        format_func=lambda x: ["Acceptable - No addition required", "Minor correction (≤25% of volume to be added)", "Intermediate correction (25–≤50% to be added)", "Major correction (50–≤75% to be added)", "Not acceptable (>75% to be added)"][x]
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

    st.subheader("Causes for False Positives Segmentation")

    fp_vessels = st.checkbox("Blood vessels")
    fp_nodes = st.checkbox("Lymph nodes")
    fp_nodular = st.checkbox("Nodular enhancement")
    fp_shape = st.checkbox("Complex lesion shape")
    fp_skin = st.checkbox("Skin")
    fp_nipple = st.checkbox("Nipple–areolar complex")
    fp_nme = st.checkbox("Non-mass enhancement")
    fp_satellites = st.checkbox("Satellite lesions")

    st.subheader("Causes for False Positives Segmentation")

    fn_necrosis = st.radio("Necrosis / fibrosis", ["Yes", "No"])

    submitted = st.form_submit_button("Click me to save your assessment")
