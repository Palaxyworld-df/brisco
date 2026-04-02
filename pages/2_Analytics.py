import streamlit as st
import pandas as pd
from supabase import create_client

st.title("Analytics Dashboard")

# Connect to Supabase
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
# USERS BY PROFESSION
# ---------------------------
if not users.empty and "profession" in users.columns:
    st.subheader("Users by Profession")
    st.bar_chart(users["profession"].value_counts())

# ---------------------------
# USERS BY COUNTRY
# ---------------------------
if not users.empty and "country" in users.columns:
    st.subheader("Users by Country")
    st.bar_chart(users["country"].value_counts())
