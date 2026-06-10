# 🕐 HR Attendance Analyzer

A Streamlit app that analyzes employee attendance sheets, detects late arrivals, calculates discounted days, identifies absences, and accounts for Egyptian public holidays and the Sunday–Thursday work week.

---

## ✨ Features

- **Upload any month's attendance Excel file** — no configuration needed
- **First check-in only** — employees who sign in multiple times per day are handled correctly; only the earliest session counts
- **Late detection** — flags employees who arrive more than 1.5 hours after the 9:00 AM start time
- **Day discount rule** — any day with lateness > 1.5h is marked as discounted (deducted), mission days are exempt
- **Missing days** — calculates absent working days per employee based on the actual calendar
- **Egyptian work week** — Sunday to Thursday only; Friday and Saturday are always off
- **Public holidays** — pre-loaded with Egypt's official holidays for 2026, fully editable from the sidebar
- **Holiday manager** — add, edit, or delete holidays at runtime; accounts for dates that shift when holidays fall on weekends
- **Color-coded table** — green / orange / red indicators for late and missing day counts
- **CSV export** — download the full summary with all dates listed

---

## 📋 Expected Excel Format

The uploaded `.xlsx` file should contain these columns (column names are flexible, the app detects them automatically):

| Column | Description |
|---|---|
| `Employee` | Employee full name |
| `Check In` | Check-in datetime |
| `Check Out` | Check-out datetime |
| `Worked hours` | Hours worked in that session |
| `Open Check-in location in Google Maps` | Google Maps URL for check-in location (optional) |
| `Open Check-out location in Google Maps` | Google Maps URL for check-out location (optional) |
| `Attendance Reason` | Notes such as mission, client visit, or auto-checkout (optional) |

---

## 🚀 Running Locally

**1. Clone the repository**
```bash
git clone https://github.com/your-username/attendance-analyzer.git
cd attendance-analyzer
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the app**
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## ☁️ Deploying on Streamlit Cloud

1. Push this repository to GitHub (must be public)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app**
4. Set:
   - **Repository:** `your-username/attendance-analyzer`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Click **Deploy**

Your app will be live at a URL like `https://your-username-attendance-analyzer-app-xxxx.streamlit.app`

> **Note:** Free tier apps sleep after ~7 days of inactivity. The first visit after sleep takes ~30 seconds to wake up.

---

## 📦 Requirements

```
streamlit
pandas
openpyxl
requests
```

---

## 🏖️ Managing Public Holidays

The sidebar includes a full holiday manager. Egyptian public holidays sometimes shift when they fall on a Friday or Saturday — the government announces the actual observed substitute day. You can update dates directly in the sidebar without touching any code:

- **✏️ Edit** — change the date or name of any existing holiday
- **🗑️ Delete** — remove a holiday that doesn't apply
- **➕ Add** — add a new holiday or a government-announced substitute date
- **↺ Reset** — restore all defaults

Dates must be entered in `YYYY-MM-DD` format.

---

## 📊 Output Columns

| Column | Description |
|---|---|
| Employee | Employee name |
| Attendance Days | Number of days the employee checked in |
| Late / Disc. Days | Days discounted due to lateness > 1.5h |
| Late Day Dates | List of each discounted day's date |
| Missing Days | Working days with no check-in at all |
| Missing Day Dates | List of each absent working day |

---

## ⚙️ Business Rules

| Rule | Value |
|---|---|
| Work week | Sunday – Thursday |
| Work start time | 09:00 AM |
| Late threshold | 1.5 hours |
| Discount trigger | First check-in > 1.5h after 09:00 |
| Mission days | Exempt from discounting regardless of lateness |
| Multiple sessions | Only the first check-in of the day is used |

E.md           # This file
```
