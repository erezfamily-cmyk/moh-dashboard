import streamlit as st
import json
import os
import subprocess
from datetime import datetime

st.set_page_config(
    page_title="דשבורד משרד הבריאות",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# RTL support
st.markdown("""
<style>
    body, .stApp { direction: rtl; }
    .stMarkdown, .stText, h1, h2, h3, p { text-align: right; direction: rtl; }
    .site-card {
        background: #f8f9fa;
        border-right: 4px solid #0066cc;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .item-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .status-ok { color: #28a745; }
    .status-blocked { color: #ffc107; }
    .status-error { color: #dc3545; }
    .tag {
        display: inline-block;
        background: #e8f0fe;
        color: #1a73e8;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        margin-left: 6px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏥 דשבורד משרד הבריאות")
st.caption("מציג תוכן מאתרי משרד הבריאות: פורטל הורים, בריאות הנפש, ופורטל ראשי")

# Load data
data_file = 'scraped_data.json'

col_refresh, col_time = st.columns([1, 4])
with col_refresh:
    if st.button("🔄 רענן נתונים", type="primary"):
        with st.spinner("גורד נתונים..."):
            try:
                result = subprocess.run(
                    ['python', 'src/scraper.py'],
                    capture_output=True, text=True, cwd=os.path.dirname(__file__)
                )
                if result.returncode == 0:
                    st.success("עודכן בהצלחה!")
                else:
                    st.error(f"שגיאה: {result.stderr[:200]}")
            except Exception as e:
                st.error(f"שגיאה: {e}")
        st.rerun()

if os.path.exists(data_file):
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Show last update time
    times = [v.get('last_scraped') for v in data.values() if v.get('last_scraped')]
    if times:
        last = max(times)
        try:
            dt = datetime.fromisoformat(last)
            with col_time:
                st.caption(f"עדכון אחרון: {dt.strftime('%d/%m/%Y %H:%M')}")
        except Exception:
            pass

    # Display each site
    for site_name, info in data.items():
        status = info.get('status', 'unknown')
        status_icon = {'ok': '🟢', 'blocked': '🟡', 'error': '🔴'}.get(status, '⚪')

        with st.expander(f"{status_icon} {site_name}", expanded=(status == 'ok')):
            if status == 'blocked':
                st.warning(f"⚠️ {info.get('error', 'האתר חוסם גישה אוטומטית')}")
                st.info(f"🔗 [פתח באתר]({info.get('url', '')})")

            elif status == 'error':
                st.error(f"שגיאה: {info.get('error', '')}")

            else:
                items = info.get('items', [])
                if not items:
                    st.info("לא נמצא תוכן. נסה לרענן.")
                else:
                    st.markdown(f"**{len(items)} פריטים נמצאו**")
                    for item in items:
                        title = item.get('title', '')
                        link = item.get('link', '')
                        desc = item.get('description', '')
                        date = item.get('date', '')

                        # Format date
                        date_display = ''
                        try:
                            dt = datetime.fromisoformat(date)
                            date_display = dt.strftime('%d/%m/%Y')
                        except Exception:
                            date_display = date[:10] if date else ''

                        if link:
                            st.markdown(f"**[{title}]({link})**")
                        else:
                            st.markdown(f"**{title}**")

                        if desc:
                            st.caption(desc)

                        if date_display:
                            st.caption(f"📅 {date_display}")

                        st.divider()

            # Show URL
            url = info.get('url', '')
            if url:
                st.markdown(f"🔗 [עבור לאתר]({url})")

else:
    st.warning("אין נתונים עדיין. לחץ על 'רענן נתונים' להתחיל.")
    if st.button("התחל גרידה"):
        with st.spinner("גורד נתונים בפעם הראשונה..."):
            try:
                result = subprocess.run(
                    ['python', 'src/scraper.py'],
                    capture_output=True, text=True, cwd=os.path.dirname(__file__)
                )
                st.rerun()
            except Exception as e:
                st.error(f"שגיאה: {e}")
