import streamlit as st
import pandas as pd
import re, math
from datetime import datetime, time, date as date_type
from pandas.tseries.offsets import CustomBusinessDay

st.set_page_config(page_title="Attendance Analyzer", layout="wide")

# ── Egyptian public holidays (actual observed dates) ──────────────────────────
DEFAULT_HOLIDAYS = [
    ("2026-01-07", "Coptic Christmas"),
    ("2026-01-29", "Revolution Day Jan 25 (observed)"),
    ("2026-03-19", "Eid al-Fitr Holiday"),
    ("2026-03-20", "Eid al-Fitr"),
    ("2026-03-22", "Eid al-Fitr Day 3"),
    ("2026-03-23", "Eid al-Fitr Day 4"),
    ("2026-04-12", "Coptic Easter"),
    ("2026-04-13", "Sham El Nessim"),
    ("2026-04-25", "Sinai Liberation Day"),
    ("2026-05-01", "Labour Day"),
    ("2026-06-16", "El Hijra (Islamic New Year)"),
    ("2026-06-30", "Revolution Day June 30"),
    ("2026-07-23", "National Day"),
    ("2026-08-25", "Prophet's Birthday"),
    ("2026-10-09", "Armed Forces Day"),
]

WORK_START  = time(9, 0)
LATE_THRESH = 1.5

# ── helpers ───────────────────────────────────────────────────────────────────
def get_working_days(start, end, holiday_dates):
    cbd = CustomBusinessDay(weekmask='Sun Mon Tue Wed Thu', holidays=holiday_dates)
    return pd.bdate_range(start, end, freq=cbd).date.tolist()

def parse_date_safe(s):
    try:
        return pd.to_datetime(s).date()
    except:
        return None

# ── session state init (runs once) ────────────────────────────────────────────
def reset_holidays():
    # use a plain list of [id, date, name] — id is stable UUID-like int
    st.session_state.h_rows   = [[i, d, n] for i, (d, n) in enumerate(DEFAULT_HOLIDAYS)]
    st.session_state.h_nextid = len(DEFAULT_HOLIDAYS)
    st.session_state.h_edit   = None   # id of row being edited, or None

if 'h_rows' not in st.session_state:
    reset_holidays()

# ── on_click callbacks (execute BEFORE re-render) ─────────────────────────────
def cb_delete(row_id):
    st.session_state.h_rows = [r for r in st.session_state.h_rows if r[0] != row_id]
    if st.session_state.h_edit == row_id:
        st.session_state.h_edit = None

def cb_start_edit(row_id):
    st.session_state.h_edit = row_id

def cb_cancel_edit():
    st.session_state.h_edit = None

def cb_save_edit(row_id):
    new_d = st.session_state.get(f'inp_d_{row_id}', '').strip()
    new_n = st.session_state.get(f'inp_n_{row_id}', '').strip()
    if parse_date_safe(new_d) and new_n:
        for r in st.session_state.h_rows:
            if r[0] == row_id:
                r[1], r[2] = new_d, new_n
        st.session_state.h_edit = None
    else:
        st.session_state.h_save_err = "Invalid date or empty name."

def cb_add():
    new_d = st.session_state.get('add_d', '').strip()
    new_n = st.session_state.get('add_n', '').strip()
    if parse_date_safe(new_d) and new_n:
        nid = st.session_state.h_nextid
        st.session_state.h_rows.append([nid, new_d, new_n])
        st.session_state.h_nextid += 1
        st.session_state['add_d'] = ''
        st.session_state['add_n'] = ''
        st.session_state.h_add_err = None
    else:
        st.session_state.h_add_err = "Enter a valid date (YYYY-MM-DD) and a name."

if 'h_save_err' not in st.session_state: st.session_state.h_save_err = None
if 'h_add_err'  not in st.session_state: st.session_state.h_add_err  = None

# ── process attendance ─────────────────────────────────────────────────────────
def process(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()
    rename = {}
    for c in df.columns:
        cl = c.lower()
        if cl == 'employee':                             rename[c] = 'Employee'
        elif 'check in' in cl and 'location' not in cl: rename[c] = 'Check In'
        elif 'check-in' in cl and 'location' in cl:     rename[c] = 'CI_URL'
        elif 'reason' in cl:                             rename[c] = 'Reason'
    df.rename(columns=rename, inplace=True)
    df['Check In'] = pd.to_datetime(df['Check In'], errors='coerce')
    df['Date']     = df['Check In'].dt.date
    df['Reason']   = df.get('Reason', pd.Series([''] * len(df))).fillna('')
    if 'CI_URL' not in df.columns: df['CI_URL'] = None

    first = df.sort_values('Check In').groupby(['Employee', 'Date'], sort=False).first().reset_index()
    rows = []
    for _, r in first.iterrows():
        emp, d, fi = r['Employee'], r['Date'], r['Check In']
        late_h = 0.0
        if pd.notna(fi):
            late_h = max(0.0, (datetime.combine(d, fi.time()) -
                               datetime.combine(d, WORK_START)).total_seconds() / 3600)
        is_mission = bool(re.search(r'mission|client|visit|field|off.?site',
                                    str(r.get('Reason', '')).lower()))

        discounted = False if is_mission else (late_h > LATE_THRESH)
        rows.append({'Employee': emp, 'Date': d, 'Late Hours': round(late_h, 2),
                     'Discounted': discounted})
    return pd.DataFrame(rows)

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🏖️ Public Holidays")
    st.caption("Actual observed dates — already adjusted for weekend shifts.")

    for row in st.session_state.h_rows:
        rid, hdate, hname = row[0], row[1], row[2]

        if st.session_state.h_edit == rid:
            # ── edit mode ─────────────────────────────────────────────────
            st.text_input("Date (YYYY-MM-DD)", value=hdate, key=f'inp_d_{rid}')
            st.text_input("Name",              value=hname, key=f'inp_n_{rid}')
            if st.session_state.h_save_err:
                st.error(st.session_state.h_save_err)
                st.session_state.h_save_err = None
            c1, c2 = st.columns(2)
            c1.button("💾 Save", key=f'sv_{rid}', use_container_width=True,
                      on_click=cb_save_edit, args=(rid,))
            c2.button("Cancel",  key=f'cx_{rid}', use_container_width=True,
                      on_click=cb_cancel_edit)
        else:
            # ── view mode ─────────────────────────────────────────────────
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.markdown(f"**{hdate}**  \n<small>{hname}</small>", unsafe_allow_html=True)
            c2.button("✏️", key=f'ed_{rid}', help="Edit",
                      on_click=cb_start_edit, args=(rid,))
            c3.button("🗑️", key=f'dl_{rid}', help="Delete",
                      on_click=cb_delete, args=(rid,))

    st.divider()
    st.markdown("**➕ Add holiday**")
    c1, c2 = st.columns([2, 3])
    c1.text_input("Date", placeholder="2026-05-01", key="add_d", label_visibility="collapsed")
    c2.text_input("Name", placeholder="Labour Day", key="add_n", label_visibility="collapsed")
    st.button("Add", use_container_width=True, on_click=cb_add)
    if st.session_state.h_add_err:
        st.error(st.session_state.h_add_err)
        st.session_state.h_add_err = None

    st.divider()
    st.button("↺ Reset to defaults", use_container_width=True, on_click=reset_holidays)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
st.title("🕐 Attendance Analyzer")

# build active holiday dict from session state
active_holidays = {}
for _, hdate_str, hname in st.session_state.h_rows:
    d = parse_date_safe(hdate_str)
    if d:
        active_holidays[d] = hname

# ── master employee list ─────────────────────────────────────────────────────
ALL_EMPLOYEES = [
    'Abdallah Adel',
    'Abdallah Salama',
    'Abdelrahman Elsherif',
    'Abdelrahman Hassan',
    'Abdelrahman Mohamed Khalaf',
    'Abdelrahman Mohamed Sayed Okaby',
    'Abdelrahman Mohsen Ahmed',
    'Abdelrahman Tarek',
    'Ahmed Abdelkader',
    'Ahmed Abdelsattar',
    'Ahmed Aladdin',
    'Ahmed Almeldien',
    'Ahmed Amr',
    'Ahmed Atef Gamil Mahmoud',
    'Ahmed Eid Ibrahim Mohamed',
    'Ahmed El Naggar',
    'Ahmed Essam Hussien',
'Ahmed Essam Rashdan',
'Ahmed Hesham',
'Ahmed Hossam',
'Ahmed Magdy Momtaz',
'Ahmed Maher',
'Ahmed Nageh',
'Ahmed Sherif Hassan Rateb',
'Ali Mohamed',
'Amin Ibrahim Amin Abdelhafez',
'Amr Naguib',
'Amr Selim',
'Andrew William',
'Ashraf Salah Ahmed Mohamed',
'Asmaa Salah',
'Bassam Ahmed Hassanen',
'Desouky Eid',
'Dina Adel',
'Dina Fayed',
'Dina Mahmoud Sayed Rashwan',
'Eslam Nasser',
'Eyad Abdallah',
'Gasser Hisham',
'Hany Fares',
'Hassan Mohamed',
'Haytham Abou Zeid',
'Hazem Tarek Mohamed',
'Hisham Magdy',
'Hossam Aglan',
'Islam Shaaban',
'Khaled Salman',
'Mahmoud Abdellah',
'Mahmoud Samaha',
'Mahmoud Sherif',
'Mariam Hossam',
'Menna Khaled Hassan',
'Mohab Mohamed Hossam',
'Mohamed Abdelbaky Mostafa',
'Mohamed Ahmed Abdelmaqsoud',
'Mohamed Ahmed Abdelsatar Shatla',
'Mohamed Alaa',
'Mohamed El Sadek',
'Mohamed Essmat',
'Mohamed Hisham',
'Mohamed Medhat',
'Mohamed Nasser',
'Mohamed Omar Ali Wasfy',
'Mohamed Rakha',
'Mohamed Saad Abdelaziz Shaaban',
'Mohamed Sayed Mansour Ahmed',
'Mohamed Sherif Hassan Rateb',
'Mohamed Yousry Aly',
'Mokhtar Shabaan',
'Mostafa Mohamed Anwar',
'Nader Nabil',
'Omar Aboubakr',
'Omar Bahaa',
'Omar Hassan',
'Omar Magdy',
'Omar Selim',
'Ramadan Mahmoud',
'Rania Shiba',
'Refaat Ahmed',
'Sohailah Mohamed Salah',
'Amr Tarek',
'Mohamed Galal',
'Mahmoud AbdelAziz',
'Abdelrhman Tarek',
'Sara essam mohamed ',
'Amr Maged Hanfy',
'Mohab mohamed hossam',
'merna sameh',
'Youssef Tarek',

]

# ── file uploader ─────────────────────────────────────────────────────────────
st.markdown("**📂 Upload attendance file**")
uploaded = st.file_uploader("Attendance Excel", type=["xlsx"],
                            label_visibility="collapsed")

if not uploaded:
    st.markdown("<div style='text-align:center;padding:40px;color:#888;font-size:18px'>"
                "Drop your attendance .xlsx file above to get started</div>",
                unsafe_allow_html=True)
    st.stop()

with st.spinner("Processing…"):
    daily = process(uploaded)

all_work_days   = get_working_days(daily['Date'].min(), daily['Date'].max(),
                                   list(active_holidays.keys()))
period_holidays = {d: n for d, n in active_holidays.items()
                   if daily['Date'].min() <= d <= daily['Date'].max()}

# employees in attendance but not in master list → append with warning
attended_emps   = list(daily['Employee'].unique())
unknown_emps    = [e for e in attended_emps if e not in ALL_EMPLOYEES]
all_emps        = ALL_EMPLOYEES + unknown_emps

if unknown_emps:
    with st.expander(f"⚠️ {len(unknown_emps)} name(s) in the attendance file not found in the master list"):
        for n in unknown_emps:
            st.markdown(f"- `{n}`")

records = []
for emp in all_emps:
    ed            = daily[daily['Employee'] == emp]
    attended      = set(ed['Date'].tolist())
    late_dates    = sorted(ed[ed['Discounted']]['Date'].tolist())
    missing_dates = sorted(d for d in all_work_days if d not in attended)

    records.append({
        'Employee':          emp,
        'Attendance Days':   len(attended),
        'Late / Disc. Days': len(late_dates),
        'Late Day Dates':    '\n'.join(str(d) for d in late_dates)    or '—',
        'Missing Days':      len(missing_dates),
        'Missing Day Dates': '\n'.join(str(d) for d in missing_dates) or '—',
    })

summary = (pd.DataFrame(records)
             .sort_values('Late / Disc. Days', ascending=False)
             .reset_index(drop=True))

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("👥 Employees",        len(records))
c2.metric("📅 Working Days",     len(all_work_days))
c3.metric("❌ Total Discounted", int(summary['Late / Disc. Days'].sum()))
c4.metric("🏖️ Public Holidays",  len(period_holidays))
st.markdown("---")

# ── table ─────────────────────────────────────────────────────────────────────
st.subheader("Employee Summary")

def color_late(val):
    if val == 0:  return 'color:#2ecc71;font-weight:bold'
    if val <= 3:  return 'color:#f39c12;font-weight:bold'
    return 'color:#e74c3c;font-weight:bold'

def color_miss(val):
    if val == 0:  return 'color:#2ecc71;font-weight:bold'
    if val <= 2:  return 'color:#f39c12;font-weight:bold'
    return 'color:#e74c3c;font-weight:bold'

styled = (summary.style
          .map(color_late, subset=['Late / Disc. Days'])
          .map(color_miss, subset=['Missing Days'])
          .set_properties(**{'text-align': 'left', 'white-space': 'pre-wrap'}))

max_dates  = max(summary['Late / Disc. Days'].max(), summary['Missing Days'].max(), 1)
row_height = max(40, min(max_dates * 22 + 20, 200))
tbl_height = min(len(summary) * row_height + 60, 800)

st.dataframe(styled, use_container_width=True, height=tbl_height, hide_index=True,
             column_config={
                 'Late Day Dates':    st.column_config.TextColumn('Late Day Dates',    width='medium'),
                 'Missing Day Dates': st.column_config.TextColumn('Missing Day Dates', width='medium'),
             })

if period_holidays:
    with st.expander("🏖️ Public holidays excluded from missing days"):
        for d, name in sorted(period_holidays.items()):
            tag = " ⚠️ (falls on weekend — verify substitute)" if d.weekday() in (4, 5) else ""
            st.markdown(f"- **{d}** ({d.strftime('%A')}) — {name}{tag}")

export = summary.copy()
csv = export.to_csv(index=False).encode('utf-8')
st.download_button("⬇️ Download CSV", csv, "attendance_summary.csv", "text/csv")
