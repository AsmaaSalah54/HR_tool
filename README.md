# HR Attendance Analyzer

A simple tool that takes your monthly attendance Excel file and tells you — for each employee — how many days they were late, which days they missed, and how many days should be deducted.

Built for Egyptian companies running a Sunday–Thursday work week.

---

## What it does

Upload your attendance sheet and you get a table showing every employee with:

- Total days they showed up
- How many days were late enough to count as a deduction (over 1.5 hours late)
- The exact dates of those late days
- How many working days they were completely absent
- The exact dates of those absences

Public holidays are already accounted for, so if someone was absent on Sham El Nessim it won't show up as a missing day.

---

## How to use it

1. Open the app
2. Upload your `.xlsx` attendance file
3. That's it — the table builds automatically

If a holiday date changes (which happens in Egypt when the official day falls on a weekend), just update it from the sidebar. No code needed.

---

## Running it yourself

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Deploy on Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set `app.py` as the main file
4. Hit Deploy

---

## Requirements

```
streamlit
pandas
openpyxl
requests
```
