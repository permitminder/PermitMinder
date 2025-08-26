import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="PermitMinder", page_icon="", layout="centered")

# Professional CSS injection
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@600&display=swap" rel="stylesheet">
<style>
    /* Global styles */
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        max-width: 960px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    
    /* Typography */
    h1 {
        font-family: 'Source Serif 4', serif !important;
        font-weight: 600 !important;
        color: #0F172A !important;
        font-size: 2.25rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: #0F172A !important;
        font-size: 1.5rem !important;
    }
    
    h3 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        color: #0F172A !important;
        font-size: 1.125rem !important;
    }
    
    p, .stMarkdown {
        color: #475569;
        line-height: 1.6;
    }
    
    /* Help text */
    .help-text {
        font-size: 0.875rem;
        color: #475569;
        margin-top: 0.5rem;
    }
    
    /* Disclaimer */
    .disclaimer {
        background: #FEF3C7;
        border: 1px solid #FCD34D;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin: 1rem 0;
        font-size: 0.875rem;
        color: #78350F;
    }
    
    /* Metrics cards */
    div[data-testid="metric-container"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 1rem;
        box-shadow: none;
    }
    
    div[data-testid="metric-container"] label {
        color: #475569 !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }
    
    div[data-testid="metric-container"] [data-testid="metric-value"] {
        color: #0F172A !important;
        font-weight: 600 !important;
    }
    
    /* Tables */
    .dataframe {
        font-size: 0.875rem !important;
    }
    
    .dataframe thead tr {
        background: #F1F5F9 !important;
        position: sticky;
        top: 0;
    }
    
    .dataframe tbody tr:nth-of-type(even) {
        background: #F8FAFC;
    }
    
    .dataframe tbody tr:hover {
        background: #F1F5F9;
    }
    
    /* Buttons */
    .stButton > button {
        background: #2563EB;
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: background 0.2s;
    }
    
    .stButton > button:hover {
        background: #1D4ED8;
    }
    
    /* Radio buttons */
    .stRadio > div {
        flex-direction: row;
        gap: 1rem;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border: 1px solid #E2E8F0;
        background: #FFFFFF;
        color: #0F172A;
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #94A3B8;
    }
    
    /* Links */
    a {
        color: #2563EB !important;
        text-decoration: none !important;
    }
    
    a:hover {
        text-decoration: underline !important;
    }
    
    /* Facility cards */
    .facility-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 6px !important;
        color: #0F172A !important;
        font-weight: 500 !important;
    }
    
    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_connection():
    return sqlite3.connect('permits.db', check_same_thread=False)


conn = get_connection()

# Helper function to render permit details
def render_permit_details(permit_no: str):
    q = """
        SELECT PF_NAME, PARAMETER, SAMPLE_VALUE, PERMIT_VALUE,
               NON_COMPLIANCE_DATE, NON_COMPL_TYPE_DESC, COUNTY_NAME, PERMIT_NUMBER
        FROM exceedances
        WHERE PERMIT_NUMBER = ?
        ORDER BY NON_COMPLIANCE_DATE DESC
    """
    df = pd.read_sql_query(q, conn, params=[permit_no])
    
    if df.empty:
        st.error(f"No reported exceedances found for permit {permit_no}")
        return
    
    facility = df.iloc[0]["PF_NAME"]
    county = df.iloc[0]["COUNTY_NAME"]
    
    st.markdown(f"## {facility}")
    
    # Summary cards - wider columns to prevent truncation
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("County", county)
        st.metric("Permit", permit_no)
    with col2:
        st.metric("Exceedances", f"{len(df):,}")
        dmin = pd.to_datetime(df["NON_COMPLIANCE_DATE"]).min()
        dmax = pd.to_datetime(df["NON_COMPLIANCE_DATE"]).max()
        st.metric("Date Range", f"{dmin:%m/%d/%Y} – {dmax:%m/%d/%Y}")
    
    st.markdown("### Reported Exceedance History")
    
    display_df = df[["NON_COMPLIANCE_DATE","PARAMETER","SAMPLE_VALUE","PERMIT_VALUE","NON_COMPL_TYPE_DESC"]].copy()
    display_df.columns = ["Date","Parameter","Reported Value","Permit Limit","Event Type"]
    display_df["Event Type"] = display_df["Event Type"].str.replace("Violation", "Exceedance")
    display_df["Date"] = pd.to_datetime(display_df["Date"]).dt.strftime("%Y-%m-%d")
    
    # Safe exceedance calculation
    rv = pd.to_numeric(display_df["Reported Value"], errors="coerce")
    lim = pd.to_numeric(display_df["Permit Limit"], errors="coerce")
    with pd.option_context("mode.use_inf_as_na", True):
        ex = (rv / lim - 1) * 100
    ex[(lim <= 0) | rv.isna() | lim.isna()] = pd.NA
    display_df["Exceedance %"] = ex.round(1)
    
    # Format numeric columns with thousands separators
    for col in ["Reported Value", "Permit Limit"]:
        display_df[col] = pd.to_numeric(display_df[col], errors="coerce").apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "—")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Exceedance %": st.column_config.NumberColumn("Exceedance %", format="%.1f%%"),
            "Reported Value": st.column_config.TextColumn("Reported Value"),
            "Permit Limit": st.column_config.TextColumn("Permit Limit")
        }
    )

    # Add CSV export button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f'permit_{permit_no}_exceedances.csv',
        mime='text/csv'
    )
# Subscription form
    with st.form(f"subscribe_{permit_no}"):
        st.write("**Get alerts for this permit**")
        email = st.text_input("Email")
        frequency = st.selectbox("Alert frequency", ["Weekly", "Monthly"])
        submit = st.form_submit_button("Subscribe")
        
        if submit and email:
            cur = conn.cursor()
            cur.execute("INSERT INTO subscriptions VALUES (?, ?, ?, date('now'))", 
                       (email, permit_no, frequency))
            conn.commit()
            st.success("Subscribed! Beta alerts starting soon.")
            
# Header
st.markdown("# PermitMinder")
st.markdown("**Track NPDES Permit Exceedances in Pennsylvania**")
st.markdown("""
<div class="disclaimer">
<strong>Disclaimer:</strong> Data reflect self-reported eDMR results compared to permit limits. They are not a legal determination of a exceedances or enforcement finding.
</div>
""", unsafe_allow_html=True)

# Search interface - no white box wrapper
search_type = st.radio("Search by:", ["Permit Number", "Facility Name"], horizontal=True, label_visibility="visible")

if search_type == "Permit Number":
    search_input = st.text_input("", placeholder="PA1234567", label_visibility="collapsed")
    search_value = (search_input or "").strip().upper()
    search_query = """
        SELECT PF_NAME, PARAMETER, SAMPLE_VALUE, PERMIT_VALUE,
               NON_COMPLIANCE_DATE, NON_COMPL_TYPE_DESC, COUNTY_NAME, PERMIT_NUMBER
        FROM exceedances
        WHERE UPPER(PERMIT_NUMBER) LIKE UPPER(?)
        ORDER BY NON_COMPLIANCE_DATE DESC
    """
    search_params = [f"%{search_value}%"] if search_value else None
else:
    search_input = st.text_input("", placeholder="Enter facility name", label_visibility="collapsed")
    search_value = (search_input or "").strip()
    search_query = """
        SELECT DISTINCT PERMIT_NUMBER, PF_NAME, COUNTY_NAME, 
               COUNT(*) as exceedance_count
        FROM exceedances 
        WHERE UPPER(PF_NAME) LIKE UPPER(?)
        GROUP BY PERMIT_NUMBER, PF_NAME, COUNTY_NAME
        ORDER BY exceedance_count DESC
        LIMIT 20
    """
    search_params = [f'%{search_value}%'] if search_value else None

# Search results
if search_value and search_params:
    st.markdown("---")
    
    if search_type == "Permit Number":
        df = pd.read_sql_query(search_query, conn, params=search_params)
        
        if not df.empty:
            unique_permits = df['PERMIT_NUMBER'].unique()
            
            if len(unique_permits) == 1:
                render_permit_details(unique_permits[0])
            else:
                st.markdown(f"### Found {len(unique_permits)} permits matching '{search_value}'")
                
                for permit in unique_permits[:10]:
                    facility_df = df[df['PERMIT_NUMBER'] == permit]
                    facility_name = facility_df.iloc[0]['PF_NAME']
                    county = facility_df.iloc[0]['COUNTY_NAME']
                    
                    st.markdown('<div class="facility-card">', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns([4, 2, 1])
                    col1.markdown(f"**{facility_name}**")
                    col2.markdown(f"{county} County")
                    col3.markdown(f"{len(facility_df):,} reported exceedances")
                    
                    if st.button("View", key=f"perm_{permit}", type="primary"):
                        st.session_state['selected_permit'] = permit
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error(f"No reported exceedances found for permits matching '{search_value}'")
    
    else:  # Facility name search
        df = pd.read_sql_query(search_query, conn, params=search_params)
        
        if not df.empty:
            st.markdown(f"### Found {len(df)} facilities matching '{search_value}'")
            
            for idx, row in df.iterrows():
                st.markdown('<div class="facility-card">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns([4, 2, 1])
                col1.markdown(f"**{row['PF_NAME']}**")
                col2.markdown(f"{row['COUNTY_NAME']} County")
                col3.markdown(f"{row['exceedance_count']:,} reported exceedances")
                
                if st.button("View", key=f"fac_{idx}", type="primary"):
                    st.session_state['selected_permit'] = row['PERMIT_NUMBER']
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning(f"No facilities found matching '{search_value}'")

# Handle selected permit
if st.session_state.get("selected_permit"):
    st.markdown("---")
    render_permit_details(st.session_state["selected_permit"])
    del st.session_state["selected_permit"]

# Database statistics
dminmax = pd.read_sql_query("SELECT MIN(NON_COMPLIANCE_DATE) AS dmin, MAX(NON_COMPLIANCE_DATE) AS dmax FROM exceedances", conn).iloc[0]

with st.expander("Database Statistics"):
    c1, c2, c3, c4 = st.columns(4)
    
    total = pd.read_sql_query("SELECT COUNT(*) AS c FROM exceedances", conn).iloc[0]["c"]
    unique_permits = pd.read_sql_query("SELECT COUNT(DISTINCT PERMIT_NUMBER) AS c FROM exceedances", conn).iloc[0]["c"]
    unique_facilities = pd.read_sql_query("SELECT COUNT(DISTINCT PF_NAME) AS c FROM exceedances", conn).iloc[0]["c"]
    
    c1.metric("Total Reported Exceedances", f"{total:,}")
    c2.metric("Unique Facilities", f"{unique_facilities:,}")
    c3.metric("Unique Permits", f"{unique_permits:,}")
    
    try:
        c4.metric("Data Period", f"{pd.to_datetime(dminmax['dmin']):%Y-%m-%d} – {pd.to_datetime(dminmax['dmax']):%Y-%m-%d}")
    except:
        c4.metric("Data Period", "—")

# Footer
st.markdown("---")
try:
    last_date = pd.to_datetime(dminmax["dmax"])
    updated_txt = f"Updated: {last_date:%B %Y}"
except:
    updated_txt = "Updated: —"

st.caption(f"Data: PA DEP eDMR System | {updated_txt} | Contact: **permitminder@gmail.com**")
st.caption(f"Data: PA DEP eDMR System | {updated_txt} | [Feedback](https://forms.gle/uciAb25JHxn7JVHc7) | Contact: **permitminder@gmail.com**")