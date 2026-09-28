import streamlit as st
import os
import shutil
import pandas as pd
from datetime import datetime, date
from dotenv import load_dotenv, set_key

# Interaktiver FullCalendar Import
try:
    from streamlit_calendar import calendar
except ImportError:
    calendar = None

# KI SDKs importieren
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from google import genai
except ImportError:
    genai = None

# --- UMWELTVARIABLEN & CONFIG ---
ENV_PATH = os.path.join(os.getcwd(), ".env")
if not os.path.exists(ENV_PATH):
    open(ENV_PATH, 'w').close()

load_dotenv(ENV_PATH)

# Logo-Pfad aus Dateibaum ermitteln
logo_path = None
possible_logos = [
    "wordmark_studio_dark.png",
    "wordmark_square_dark.png",
    "wordmark_studio.png",
    "wordmark_square.png",
    "logo.png",
    "assets/wordmark_studio_dark.png",
    "assets/logo.png"
]

for candidate in possible_logos:
    if os.path.exists(candidate):
        logo_path = candidate
        break

# Erzwingt permanent geöffnete Sidebar beim Laden
st.set_page_config(
    page_title="CBA Studio",
    page_icon=logo_path if logo_path else None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# --- MIDNIGHT NAVY: Badges weg, Sidebar-Pfeil bleibt klickbar ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, .stApp, p, label, input, textarea {
        font-family: 'Helvetica Neue', Helvetica, Inter, sans-serif !important;
    }

    h1, h2, h3, h4, .stSubheader, .brand-header-title {
        font-family: 'Helvetica Neue', Helvetica, Inter, sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 3px !important;
        color: #0A192F !important;
        text-transform: uppercase;
    }

    footer,
    [data-testid="stStatusWidget"],
    [data-testid="stDecoration"],
    #stDecoration,
    #MainMenu,
    [data-testid="stToolbar"],
    [data-testid="stToolbarActions"],
    [data-testid="stAppDeployButton"],
    [data-testid="stMainMenu"],
    [data-testid="manage-app-button"],
    .viewerBadge_container__1QSob,
    .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK,
    .styles_viewerBadge__1yB5_,
    div[class*="viewerBadge"],
    a[href*="streamlit.io"],
    a[href*="share.streamlit.io"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* Header bleibt im DOM, damit der Expand-Pfeil oben links nicht verschwindet */
    [data-testid="stHeader"] {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* Collapse/Expand-Pfeil immer sichtbar und über dem Inhalt */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stExpandSidebarButton"],
    button[aria-label="Expand sidebar"],
    button[aria-label="Collapse sidebar"],
    button[title="Expand sidebar"],
    button[title="Collapse sidebar"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        color: #0A192F !important;
        z-index: 999999 !important;
    }

    [data-testid="stSidebarCollapsedControl"] {
        position: fixed !important;
        top: 0.65rem !important;
        left: 0.65rem !important;
        z-index: 1000000 !important;
    }

    div[data-baseweb="input"],
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="input"] > div,
    .stTextInput input,
    .stTextInput input:focus,
    .stTextInput input:active {
        border-color: #E2E8F0 !important;
        box-shadow: none !important;
        outline: none !important;
    }

    div[data-baseweb="input"]:focus-within {
        border-color: #0A192F !important;
    }

    div[data-testid="stInputInstruction"],
    div[data-baseweb="error"] {
        display: none !important;
    }

    .brand-header-banner {
        background-color: #0A192F;
        color: #FFFFFF;
        padding: 20px 28px;
        border-radius: 6px;
        margin-bottom: 24px;
    }

    .brand-header-title {
        font-size: 1.25rem;
        margin: 0;
        letter-spacing: 4px !important;
        color: #FFFFFF !important;
    }

    .stButton > button {
        background-color: #0A192F !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        border: none !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
    }

    .stButton > button:hover {
        background-color: #1E293B !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Helvetica Neue', Helvetica, Inter, sans-serif !important;
        letter-spacing: 1.2px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.8rem !important;
        color: #64748B !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #0A192F !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #0A192F !important;
        font-weight: 700 !important;
        border-bottom-color: #0A192F !important;
    }
    </style>
""", unsafe_allow_html=True)

# Ordnerverwaltung
DOCS_DIR = os.path.join(os.getcwd(), "documents")
if not os.path.exists(DOCS_DIR):
    os.makedirs(DOCS_DIR)

for folder in ["Brand_Guidelines", "Kollektionen", "Skills_and_Prompts", "Eingangsrechnungen"]:
    os.makedirs(os.path.join(DOCS_DIR, folder), exist_ok=True)

# Session States
if "events_and_todos" not in st.session_state:
    st.session_state["events_and_todos"] = [
        {"id": "init_1", "title": "Herbst-Kollektion Content-Plan", "start": "2026-09-22", "type": "Content", "completed": False},
        {"id": "init_2", "title": "Gewerbeanmeldung Schritt 4", "start": "2026-09-25", "type": "Business", "completed": False}
    ]

if "chats" not in st.session_state:
    st.session_state["chats"] = {"Haupt-Arbeitsbereich": []}

if "active_chat" not in st.session_state:
    st.session_state["active_chat"] = "Haupt-Arbeitsbereich"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- LOGIN SEITE ---
if not st.session_state["logged_in"]:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.write("")
        st.write("")
        if logo_path:
            st.image(logo_path, use_container_width=True)
            
        st.markdown("""
        <div style="text-align: center; margin-top: 15px; margin-bottom: 25px;">
            <p style="font-size: 1rem; font-weight: 600; letter-spacing: 3px; color: #0A192F; margin: 0;">HEADQUARTER LOGIN</p>
        </div>
        """, unsafe_allow_html=True)
        
        pwd = st.text_input("Zugangsschlüssel:", type="password", key="clean_hq_pwd_key")

        if st.button("Anmelden", use_container_width=True, key="login_submit_btn"):
            if pwd == "CraftedCEO2026!":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Falscher Zugangsschlüssel")
    st.stop()

# --- SIDEBAR (SEITENLEISTE - IMMER AKTIV) ---
with st.sidebar:
    if logo_path:
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("### CBA STUDIO")
    
    st.divider()
    st.markdown("### ARBEITSBEREICHE")
    
    with st.expander("Neuen Arbeitsbereich erstellen", expanded=False):
        new_chat_name = st.text_input("Name:", key="new_chat_name_input")
        if st.button("Erstellen", use_container_width=True, key="create_workspace_btn"):
            if new_chat_name.strip() and new_chat_name.strip() not in st.session_state["chats"]:
                st.session_state["chats"][new_chat_name.strip()] = []
                st.session_state["active_chat"] = new_chat_name.strip()
                st.rerun()

    chat_list = list(st.session_state["chats"].keys())
    if st.session_state["active_chat"] not in chat_list:
        st.session_state["active_chat"] = chat_list[0]

    selected_chat = st.radio(
        label="Aktiver Arbeitsbereich:",
        options=chat_list,
        index=chat_list.index(st.session_state["active_chat"]),
        key="chat_selection_radio"
    )

    if selected_chat != st.session_state["active_chat"]:
        st.session_state["active_chat"] = selected_chat
        st.rerun()

    st.divider()
    if st.button("Abmelden", use_container_width=True, key="logout_btn"):
        st.session_state["logged_in"] = False
        st.rerun()
        
    st.divider()
    with st.expander("API Schlüssel", expanded=False):
        saved_claude = os.getenv("CLAUDE_API_KEY", "")
        saved_gemini = os.getenv("GEMINI_API_KEY", "")
        
        claude_key = st.text_input("Claude Key", value=saved_claude, type="password", key="sec_claude_key")
        gemini_key = st.text_input("Gemini Key", value=saved_gemini, type="password", key="sec_gemini_key")
        
        if st.button("Speichern", use_container_width=True, key="save_api_keys_btn"):
            set_key(ENV_PATH, "CLAUDE_API_KEY", claude_key.strip())
            set_key(ENV_PATH, "GEMINI_API_KEY", gemini_key.strip())
            st.rerun()

# --- HEADER BANNER ---
st.markdown("""
<div class="brand-header-banner">
    <div class="brand-header-title">CBA STUDIO HQ</div>
</div>
""", unsafe_allow_html=True)

# 7 REITER
tab_mitarbeiter, tab_dokumente, tab_plattformen, tab_kalender, tab_todo, tab_finanzen, tab_buchhaltung = st.tabs([
    "Mitarbeiter",
    "Dokumente",
    "Vertriebskanäle & Plattformen",
    "Kalender",
    "To-do",
    "Finanzkennzahlen",
    "Buchhaltung & Rechnungen"
])

# 1. MITARBEITER
with tab_mitarbeiter:
    current_chat_name = st.session_state["active_chat"]
    st.markdown(f"### {current_chat_name.upper()}")
    
    active_history = st.session_state["chats"][current_chat_name]
    
    for msg in active_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    prompt = st.chat_input("Eingabe...")
    if prompt:
        active_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        with st.chat_message("assistant"):
            c_key = os.getenv("CLAUDE_API_KEY", "")
            g_key = os.getenv("GEMINI_API_KEY", "")
            response_text = ""
            
            if c_key and anthropic:
                try:
                    client = anthropic.Anthropic(api_key=c_key)
                    msg = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response_text = msg.content[0].text
                except Exception as e:
                    response_text = f"Fehler: {str(e)}"

            if not response_text and g_key and genai:
                try:
                    client = genai.Client(api_key=g_key)
                    res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    response_text = res.text
                except Exception as e:
                    response_text = f"Fehler: {str(e)}"
                    
            if not response_text:
                response_text = "Bitte API-Schlüssel eintragen."
                st.warning(response_text)
            else:
                st.write(response_text)
                
            active_history.append({"role": "assistant", "content": response_text})

# 2. DOKUMENTE
with tab_dokumente:
    st.markdown("### DOKUMENTE")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### ORDNER")
        with st.expander("Ordner hinzufügen", expanded=False):
            new_folder_name = st.text_input("Name:", key="new_folder_input")
            if st.button("Erstellen", key="create_folder_btn"):
                if new_folder_name.strip():
                    os.makedirs(os.path.join(DOCS_DIR, new_folder_name.strip()), exist_ok=True)
                    st.rerun()

        existing_folders = [f for f in os.listdir(DOCS_DIR) if os.path.isdir(os.path.join(DOCS_DIR, f))]
        for folder in sorted(existing_folders):
            folder_path = os.path.join(DOCS_DIR, folder)
            files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            
            with st.expander(f"{folder} ({len(files_in_folder)})"):
                for file in files_in_folder:
                    st.text(f"- {file}")

    with col_right:
        st.markdown("#### UPLOAD")
        uploaded_file = st.file_uploader(
            "Datei wählen",
            type=["pdf", "docx", "txt", "csv", "png", "jpg", "md"],
            key="docs_file_uploader",
        )
        existing_folders = [f for f in os.listdir(DOCS_DIR) if os.path.isdir(os.path.join(DOCS_DIR, f))]
        if existing_folders and uploaded_file:
            target_folder = st.selectbox("Zielordner:", sorted(existing_folders), key="docs_target_folder")
            if st.button("Speichern", key="save_upload_btn"):
                file_path = os.path.join(DOCS_DIR, target_folder, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Gespeichert.")
                st.rerun()

# 3. VERTRIEBSKANÄLE & PLATTFORMEN
with tab_plattformen:
    st.markdown("### VERTRIEBSKANÄLE & PLATTFORMEN")
    st.button("Tapstitch verbinden", key="connect_tapstitch_btn")
    st.button("Etsy verbinden", key="connect_etsy_btn")
    st.button("Metricool verbinden", key="connect_metricool_btn")

# 4. KALENDER
with tab_kalender:
    st.markdown("### KALENDER")
    
    with st.expander("API Konfiguration", expanded=False):
        st.text_input("Google Token:", type="password", key="sec_google_token")
        st.text_input("Metricool Token:", type="password", key="sec_metricool_token")

    col_bus, col_con = st.columns(2)
    
    with col_bus:
        st.markdown("#### BUSINESS KALENDER")
        b_date = st.date_input("Business Datum wählen", date.today(), key="b_date_picker")
        b_title = st.text_input("Eintrag", key="b_title_in")
        if st.button("Business-Termin speichern", key="save_business_event_btn"):
            if b_title.strip():
                new_id = f"bus_{datetime.now().timestamp()}"
                st.session_state["events_and_todos"].append({
                    "id": new_id, 
                    "title": b_title.strip(), 
                    "start": str(b_date), 
                    "type": "Business",
                    "completed": False
                })
                st.rerun()

    with col_con:
        st.markdown("#### CONTENT KALENDER")
        c_date = st.date_input("Content Datum wählen", date.today(), key="c_date_picker")
        c_title = st.text_input("Content Eintrag", key="c_title_in")
        if st.button("Content-Termin speichern", key="save_content_event_btn"):
            if c_title.strip():
                new_id = f"con_{datetime.now().timestamp()}"
                st.session_state["events_and_todos"].append({
                    "id": new_id, 
                    "title": c_title.strip(), 
                    "start": str(c_date), 
                    "type": "Content",
                    "completed": False
                })
                st.rerun()

    st.divider()

    bus_events = [{"title": e["title"], "start": e["start"], "color": "#0A192F"} 
                  for e in st.session_state["events_and_todos"] if e.get("type") == "Business"]
    
    con_events = [{"title": e["title"], "start": e["start"], "color": "#475569"} 
                  for e in st.session_state["events_and_todos"] if e.get("type") == "Content"]

    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay"
        },
        "initialView": "dayGridMonth",
        "selectable": True,
        "editable": True
    }

    if calendar:
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            calendar(events=bus_events, options=calendar_options, key="bus_cal_widget")
        with c_col2:
            calendar(events=con_events, options=calendar_options, key="con_cal_widget")

# 5. TO-DO
with tab_todo:
    st.markdown("### TO-DO")
    t_title = st.text_input("Aufgabe:", key="new_todo_title")
    t_date = st.date_input("Fällig am:", value=date.today(), key="new_todo_date")
    t_type = st.selectbox("Zuordnung:", ["Business", "Content"], key="new_todo_type")
    
    if st.button("Hinzufügen", key="add_todo_btn"):
        if t_title.strip():
            new_id = f"task_{datetime.now().timestamp()}"
            st.session_state["events_and_todos"].append({
                "id": new_id, 
                "title": t_title.strip(), 
                "start": str(t_date), 
                "type": t_type,
                "completed": False
            })
            st.rerun()

    st.divider()
    st.markdown("#### OFFENE AUFGABEN")
    
    for idx, item in enumerate(st.session_state["events_and_todos"]):
        if not item.get("completed", False):
            unique_key = f"chk_{item.get('id', idx)}"
            is_done = st.checkbox(f"**[{item['start']}]** {item['title']} *({item.get('type', 'Business')})*", key=unique_key)
            if is_done:
                item["completed"] = True
                st.rerun()

# 6. FINANZKENNZAHLEN
with tab_finanzen:
    st.markdown("### FINANZKENNZAHLEN")
    m1, m2, m3 = st.columns(3)
    m1.metric("Umsatz", "14.850 €")
    m2.metric("Kosten", "6.200 €")
    m3.metric("Gewinn", "8.650 €")

# 7. BUCHHALTUNG & RECHNUNGEN
with tab_buchhaltung:
    st.markdown("### BUCHHALTUNG & RECHNUNGEN")
    pin = st.text_input("Vault PIN:", type="password", key="sec_vault_pin")
    if pin == "VaultSecure99!":
        st.success("Entsperrt")
        st.text_input("SevDesk Token:", type="password", key="sec_sevdesk_token")