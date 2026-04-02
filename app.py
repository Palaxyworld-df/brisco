import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime

st.set_page_config(page_title="BRISCo", layout="centered")

# -------supabase----------
from supabase import create_client

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# ---------------------------
# DATABASE SETUP
# ---------------------------
conn = sqlite3.connect("brisco.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS scores")  # TEMPORARY

cursor.execute("""
CREATE TABLE scores (
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    profession TEXT,
    country TEXT,
    created_at TEXT
)
""")

conn.commit()

# Load users
users_df = pd.read_sql_query("SELECT * FROM users", conn)

# ---------------------------
# UI: WELCOME PAGE
# ---------------------------
st.title("Welcome to BRISCo App")

st.markdown("""
### Breast MRI Segmentation Scoring Platform

This tool is designed for structured evaluation of breast MRI segmentations.

---

### Acknowledgment

This work has been developed at **Dr. D. Y. Patil University (DPU)**.

The BRISCo framework supports:
- Evaluation of segmentation quality
- Benchmarking AI models
- Radiology research workflows

---

### Citation

If you use this tool, please cite:

**BRISCo: Breast MRI Segmentation Scoring Framework (DPU)**

---

### Disclaimer

For research use only. Not intended for clinical decision-making.
""")

# ---------------------------
# STATS
# ---------------------------
st.subheader("Platform Statistics")

st.write(f"**Total registered users:** {len(users_df)}")

if len(users_df) > 0:
    st.write("**Users by country:**")
    st.write(users_df["country"].value_counts())

st.divider()

# ---------------------------
# NAVIGATION STATE
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# ---------------------------
# BUTTONS
# ---------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("Existing User"):
        st.session_state.page = "login"

with col2:
    if st.button("New User"):
        st.session_state.page = "register"

# ---------------------------
# LOGIN
# ---------------------------
if st.session_state.page == "login":
    st.subheader("Login")

    user_id = st.text_input("Enter your User ID")

    if st.button("Login"):
        if user_id in users_df["user_id"].values:
            st.session_state.user_id = user_id
            st.success("Login successful")
            st.switch_page("pages/1_Scoring.py")
        else:
            st.error("User not found")

# ---------------------------
# REGISTER
# ---------------------------
if st.session_state.page == "register":
    st.subheader("Create New User")

    profession = st.text_input("Profession")
    country = st.text_input("Country")

    if st.button("Generate User ID"):
        user_id = str(uuid.uuid4())[:8]

        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?)",
            (user_id, profession, country, datetime.now().isoformat())
        )
        conn.commit()

        st.success(f"Your User ID: {user_id}")
        st.warning("⚠️ Save this ID for future login")

        st.session_state.user_id = user_id
        st.switch_page("pages/1_Scoring.py")
