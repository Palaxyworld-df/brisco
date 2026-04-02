import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="BRISCo", layout="centered")

# -------supabase----------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# ---------------------------
# LOAD USERS
# ---------------------------
response = supabase.table("users").select("*").execute()
users_df = pd.DataFrame(response.data)

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
st.subheader("Platform Stats")

st.write(f"Total users: {len(users_df)}")

if len(users_df) > 0:
    st.write("Users by country:")
    st.write(users_df["country"].value_counts())

# ---------------------------
# NAV
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

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

    user_id = st.text_input("Enter User ID")

    if st.button("Login"):
        if user_id in users_df["user_id"].values:
            st.session_state.user_id = user_id
            st.switch_page("pages/1_Scoring.py")
        else:
            st.error("User not found")

# ---------------------------
# REGISTER
# ---------------------------
if st.session_state.page == "register":
    st.subheader("Register")

    profession = st.text_input("Profession")
    country = st.text_input("Country")

    if st.button("Create User"):
        user_id = str(uuid.uuid4())[:8]

        supabase.table("users").insert({
            "user_id": user_id,
            "profession": profession,
            "country": country,
            "created_at": datetime.now().isoformat()
        }).execute()

        st.success(f"Your User ID: {user_id}")
        st.session_state.user_id = user_id
        st.switch_page("pages/1_Scoring.py")
