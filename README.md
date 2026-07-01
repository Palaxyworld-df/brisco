# BRISCO  
**Breast MRI Segmentation Scoring Interface**

BRISCO (**B**reast **MRI** **S**egmentation **CO**ring) is a Streamlit-based web app for standardized evaluation of breast MRI lesion segmentations. It supports MRI + mask visualization, structured scoring, and secure storage of assessments.

---

## 🌐 Live Demo
https://triesbrisco.streamlit.app/

---

## ✨ Features

| Left | Right |
|------|-------|
| 🔐 User registration | 🧠 Interactive MRI slice viewer |
| 🎨 Mask overlay visualization | 📂 Supports `.nii` / `.nii.gz` |
| 📝 BRISCO scoring form | 💾 Secure assessment storage |
| 📊 Analytics dashboard | 📥 Export results as CSV |

---

## 🧰 Tech Stack

| Python | Streamlit | NumPy |
|--------|-----------|------|
| Pandas | NiBabel | Pillow |
| Supabase |  |  |

---

## 📁 Project Structure

```text
BRISCO/
├── app.py
├── pages/
│   ├── 1_Scoring.py
│   └── 2_Analytics.py
├── requirements.txt
└── README.md
