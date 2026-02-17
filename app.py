import streamlit as st
import requests
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lego Set Inventory",
    page_icon="🧱",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&family=Space+Mono&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
}
h1, h2, h3 {
    font-family: 'Nunito', sans-serif;
    font-weight: 900;
}
.lego-header {
    background: linear-gradient(135deg, #e3000b 0%, #c0392b 100%);
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 15px rgba(227,0,11,0.3);
}
.lego-header h1 { margin: 0; font-size: 2rem; color: white; }
.lego-header p  { margin: 0; opacity: 0.85; font-size: 0.95rem; }
.set-card {
    background: #fff;
    border: 2px solid #e3000b;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-top: 1rem;
    box-shadow: 4px 4px 0px #e3000b33;
}
.set-card h3 { color: #e3000b; margin-top: 0; }
.badge {
    display: inline-block;
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.8rem;
    font-weight: 700;
    margin-right: 6px;
    color: #856404;
}
.success-banner {
    background: #d4edda;
    border-left: 4px solid #28a745;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    color: #155724;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lego-header">
    <h1>🧱 Lego Set Inventory Logger</h1>
    <p>Look up a set, confirm the details, and log it to your Google Doc.</p>
</div>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

REBRICKABLE_BASE = "https://rebrickable.com/api/v3/lego"

def get_lego_api_key() -> str:
    return st.secrets["lego"]["api_key"]

def fetch_set(set_id: str) -> dict | None:
    """Fetch set details from Rebrickable. Returns dict or None on failure."""
    # Rebrickable requires the set number to end with '-1' (or similar suffix)
    # If the user didn't add it, default to '-1'
    if "-" not in set_id:
        set_id = f"{set_id}-1"

    url = f"{REBRICKABLE_BASE}/sets/{set_id}/"
    headers = {"Authorization": f"key {get_lego_api_key()}"}
    resp = requests.get(url, headers=headers, timeout=10)

    if resp.status_code == 200:
        return resp.json()
    else:
        st.error(f"Rebrickable returned {resp.status_code}: {resp.text}")
        return None

def fetch_theme_name(theme_id: int) -> str:
    """Fetch theme name from Rebrickable."""
    url = f"{REBRICKABLE_BASE}/themes/{theme_id}/"
    headers = {"Authorization": f"key {get_lego_api_key()}"}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        return resp.json().get("name", "Unknown")
    return "Unknown"

def get_docs_service():
    """Build a Google Docs API service from st.secrets."""
    creds_info = dict(st.secrets["gcp_service_account"])
    # st.secrets returns an AttrDict; convert nested values to plain types
    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/documents"],
    )
    return build("docs", "v1", credentials=creds)

def append_row_to_doc(doc_id: str, set_data: dict):
    """
    Append a new row to the LAST table in the Google Doc.
    The table is expected to have columns: Set ID | Name | Year | Theme | Date Added
    """
    service = get_docs_service()
    doc = service.documents().get(documentId=doc_id).execute()

    # Find the last table in the document
    body_content = doc.get("body", {}).get("content", [])
    table_element = None
    for element in body_content:
        if "table" in element:
            table_element = element

    if table_element is None:
        st.error("No table found in the specified Google Doc. Please create a table first.")
        return False

    table = table_element["table"]
    num_rows = table["rows"]
    table_start_index = table_element["startIndex"]

    # We need to insert a new row at the end of the table.
    # Google Docs API: insertTableRow
    requests_body = [
        {
            "insertTableRow": {
                "tableCellLocation": {
                    "tableStartLocation": {"index": table_start_index},
                    "rowIndex": num_rows - 1,
                },
                "insertBelow": True,
            }
        }
    ]
    service.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests_body}
    ).execute()

    # Re-fetch to get the updated indices
    doc = service.documents().get(documentId=doc_id).execute()
    body_content = doc.get("body", {}).get("content", [])
    for element in body_content:
        if "table" in element:
            table_element = element  # keep updating to get the last table

    table = table_element["table"]
    new_row = table["tableRows"][-1]  # the row we just inserted
    cells = new_row["tableCells"]

    cell_texts = [
        set_data["set_num"],
        set_data["name"],
        str(set_data["year"]),
        set_data["theme"],
        datetime.now().strftime("%Y-%m-%d"),
    ]

    insert_requests = []
    for i, cell in enumerate(cells[:len(cell_texts)]):
        cell_index = cell["content"][0]["startIndex"]
        insert_requests.append(
            {
                "insertText": {
                    "location": {"index": cell_index},
                    "text": cell_texts[i],
                }
            }
        )

    if insert_requests:
        service.documents().batchUpdate(
            documentId=doc_id, body={"requests": insert_requests}
        ).execute()

    return True

# ── Session state ─────────────────────────────────────────────────────────────
if "fetched_set" not in st.session_state:
    st.session_state.fetched_set = None
if "recent_additions" not in st.session_state:
    st.session_state.recent_additions = []

# ── Input section ─────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    set_id_input = st.text_input(
        "Lego Set ID",
        placeholder="e.g. 75192 or 75192-1",
        label_visibility="visible",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    lookup_btn = st.button("🔍 Look Up", use_container_width=True)

# ── Fetch set data ─────────────────────────────────────────────────────────────
if lookup_btn and set_id_input.strip():
    with st.spinner("Fetching from Rebrickable…"):
        data = fetch_set(set_id_input.strip())
        if data:
            theme_name = fetch_theme_name(data.get("theme_id", 0))
            data["theme"] = theme_name
            st.session_state.fetched_set = data

# ── Display fetched set ───────────────────────────────────────────────────────
if st.session_state.fetched_set:
    s = st.session_state.fetched_set
    img_url = s.get("set_img_url", "")

    st.markdown("### Confirm Set Details")
    img_col, info_col = st.columns([1, 2])

    with img_col:
        if img_url:
            st.image(img_url, use_container_width=True)
        else:
            st.info("No image available.")

    with info_col:
        st.markdown(f"""
        <div class="set-card">
            <h3>{s['name']}</h3>
            <span class="badge">📦 {s['set_num']}</span>
            <span class="badge">📅 {s['year']}</span>
            <span class="badge">🏷️ {s['theme']}</span>
            <p style="margin-top:0.75rem; font-size:0.9rem; color:#555;">
                <strong>Pieces:</strong> {s.get('num_parts', 'N/A')}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    add_btn = st.button("✅ Add to Inventory", type="primary", use_container_width=True)

    if add_btn:
        doc_id = st.secrets["google"]["doc_id"]
        with st.spinner("Writing to Google Doc…"):
            success = append_row_to_doc(doc_id, s)
        if success:
            st.markdown('<div class="success-banner">✅ Set logged successfully!</div>', unsafe_allow_html=True)
            st.session_state.recent_additions.append({
                "Set ID": s["set_num"],
                "Name": s["name"],
                "Year": s["year"],
                "Theme": s["theme"],
                "Date Added": datetime.now().strftime("%Y-%m-%d"),
            })
            st.session_state.fetched_set = None

# ── Recent additions ──────────────────────────────────────────────────────────
if st.session_state.recent_additions:
    st.markdown("---")
    st.markdown("### 📋 Recent Additions (this session)")
    df = pd.DataFrame(st.session_state.recent_additions)
    st.table(df)
