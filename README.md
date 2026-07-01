# BRISCO

> **Breast MRI Segmentation Scoring Interface**

BRISCO (**B**reast **MRI** **S**egmentation S**CO**ring) is a web-based application developed using **Streamlit** for standardized evaluation of breast MRI lesion segmentations.

The platform enables radiologists and researchers to upload breast MRI scans along with their corresponding segmentation masks, visually inspect the segmentation, complete a structured quality assessment, and securely store the evaluation for future analysis.

BRISCO was designed to provide a consistent, reproducible, and user-friendly framework for assessing both manual and AI-generated breast MRI segmentations.

---

## 🌐 Live Demo

**https://triesbrisco.streamlit.app/**

---

# Features

- 🔐 User registration and authentication
- 🧠 Interactive MRI slice viewer
- 🎨 Segmentation mask overlay visualization
- 📂 Support for `.nii` and `.nii.gz` files
- 📝 Standardized BRISCO scoring form
- 💾 Secure storage of submitted assessments
- 📊 Analytics dashboard
- 📥 Export previous scoring results as CSV

---

# Technology Stack

- Python
- Streamlit
- NumPy
- Pandas
- NiBabel
- Pillow
- Supabase

---

# Project Structure

```text
BRISCO/
│
├── app.py                  # Landing page, authentication
├── pages/
│   ├── 1_Scoring.py        # Main BRISCO scoring interface
│   └── 2_Analytics.py      # Analytics dashboard
│
├── requirements.txt
└── README.md
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/BRISCO.git

cd BRISCO
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

---

# Configuration

BRISCO uses **Supabase** as the backend for user authentication and storing submitted assessments.

Create the following file:

```
.streamlit/secrets.toml
```

and add your own credentials:

```toml
SUPABASE_URL="YOUR_SUPABASE_URL"

SUPABASE_KEY="YOUR_SUPABASE_KEY"
```

> **Note:** The production database structure and deployment credentials are intentionally not included in this repository.

---

# Input Requirements

BRISCO accepts:

- MRI Volume (`.nii` or `.nii.gz`)
- Corresponding Segmentation Mask (`.nii` or `.nii.gz`)

Both files should have identical dimensions.

---

# Workflow

1. Register a new account.
2. Log into BRISCO.
3. Upload the MRI scan.
4. Upload the corresponding segmentation mask.
5. Inspect the segmentation using the interactive viewer.
6. Complete the BRISCO scoring form.
7. Submit the evaluation.
8. Download your previous assessments if needed.
9. Explore platform usage through the Analytics page.

---

# Analytics

The analytics dashboard provides a simple overview of platform usage, including:

- Total registered users
- Total completed assessments
- User distribution by profession
- User distribution by country

---

# Repository Includes

- Complete Streamlit application
- Authentication workflow
- Interactive visualization interface
- BRISCO scoring workflow
- Analytics dashboard

---

# Repository Does Not Include

- Production database
- Deployment credentials
- Supabase configuration
- Private clinical datasets
- MRI datasets used during development

---

# Citation

If you use BRISCO in your research, please cite the associated publication once it becomes available.

---

# License

This project is intended for research and educational purposes.

For redistribution or commercial use, please contact the project authors.
