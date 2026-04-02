import streamlit as st
import pandas as pd
from supabase import create_client

st.title("Analytics Dashboard")

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# Load data
scores = pd.DataFrame(
    supabase.table("scores").select("*").execute().data
)

users = pd.DataFrame(
    supabase.table("users").select("*").execute().data
)

# ---------------------------
# METRICS
# ---------------------------
st.subheader("Overview")

st.write(f"Total users: {len(users)}")
st.write(f"Total assessments: {len(scores)}")

# ---------------------------
# COUNTRY DISTRIBUTION
# ---------------------------
if not users.empty:
    st.subheader("Users by Country")
    st.bar_chart(users["country"].value_counts())

# ---------------------------
# QUALITY DISTRIBUTION
# ---------------------------
if not scores.empty:
    st.subheader("Segmentation Quality")
    st.bar_chart(scores["overall_quality"].value_counts())