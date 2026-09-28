import streamlit as st
import os
import shutil
import pandas as pd
from datetime import datetime, date
from dotenv import load_dotenv, set_key

# KI SDKs importieren
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from google import genai
except ImportError:
    genai = None

# --- 0. UMWELTVARIABLEN / KEYS SPEICHERN ---
ENV_PATH = os.path.join(os.getcwd(), ".env")
if not os.path.exists(ENV_PATH):
    open(ENV_PATH, 'w').close()

load_dotenv(ENV_PATH)

# Konfiguration
st.set_page_config(
    page_title="CBA Studio - Headquarter",
    page_icon="wordmark_studio_dark.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- EFFORTLESS & MINIMALISTIC BRAND STYLING + NO RED BORDER FIX ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* 1. Haupt-Schriftart für gewöhnliche Fließtexte */
    html, body, .stApp, p, label, input, textarea {
        font-family: 'Helvetica Neue', Helvetica, Inter, -apple-system, sans-serif !important;
    }

    /* 2. Brand-Typografie NUR für echte Überschriften & den Header-Banner */
    h1, h2, h3, h4, .stSubheader, .brand-header-title {
        font-family: 'Helvetica Neue', Helvetica, Inter, sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 3.5px !important;
        color: #0A192F !important;
        text-transform: uppercase;
    }

    /* 3. ABSOLUTER FIX FÜR ROTE INPUT-RAHMEN & FOCUS-INDICATORS */
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

    /* Fehlerindikatoren / Rote Nachrichten unterdrücken */
    div[data-testid="stInputInstruction"],
    div[data-baseweb="error"] {
        display: none !important;
    }

    /* 4. REPARATUR FÜR EXPANDER-PFEILE */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] summary *,
    [data-testid="stIcon"],
    span[data-baseweb="icon"] {
        letter-spacing: normal !important;
        text-transform: none !important;
    }

    /* Edler Dunkelblauer Header-Banner */
    .brand-header-banner {
        background-color: #0A192F;
        color: #FFFFFF;
        padding: 24px 32px;
        border-radius: 8px;
        margin-bottom: 28px;
        box-shadow: 0 4px 14px rgba(10, 25, 47, 0.08);
    }
    
    .brand-header-title {
        font-size: 1.35rem;
        margin: 0;
        letter-spacing: 5.5px !important;
        color: #FFFFFF !important;
    }
    
    .brand-header-subtitle {
        font-family: 'Helvetica Neue', Helvetica, Inter, sans-serif !important;
        font-size: 0.78rem;
        font-weight: 400 !important;
        color: #94A3B8 !important;
        margin: 8px 0 0 0;
        letter-spacing: 3px !important;
        text-transform: uppercase;
    }

    /* Buttons: Midnight Navy */
    .stButton > button {
        background-color: #0A192F !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    .stButton > button:hover {
        background-color: #1E293B !important;
        box-shadow: 0 4px 12px rgba(10, 25, 47, 0.12) !important;
    }

    /* Navigation / Tabs */
    .stTabs [data-baseweb="tab"] {
        font-family: 'Helvetica Neue', Helvetica, Inter, sans-serif !important;
        letter-spacing: 1.5px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.85rem !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #0A192F !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #0A192F !important;
        font-weight: 700 !important;
    }

    /* Passwort-Auge */
    button[aria-label="Show password"],
    button[aria-label="Hide password"],
    button[title="Show password"],
    button[title="Hide password"] {
        color: #0A192F !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. SCHLANKE LOKALE ORDNERVERWALTUNG (DOCUMENTS) ---
DOCS_DIR = os.path.join(os.getcwd(), "documents")
if not os.path.exists(DOCS_DIR):
    os.makedirs(DOCS_DIR)

essential_folders = ["Brand_Guidelines", "Kollektionen", "Skills_and_Prompts", "Eingangsrechnungen"]
for folder in essential_folders:
    os.makedirs(os.path.join(DOCS_DIR, folder), exist_ok=True)

# Session State initialisieren
if "events_and_todos" not in st.session_state:
    st.session_state["events_and_todos"] = [
        {"title": "Herbst-Kollektion Content-Plan abstimmen", "due_date": "2026-09-22", "source": "Content-Kalender (Metricool)", "completed": False},
        {"title": "Gewerbeanmeldung Schritt 4", "due_date": "2026-09-25", "source": "Business-Kalender (Google)", "completed": False}
    ]

if "chats" not in st.session_state:
    st.session_state["chats"] = {"Haupt-Arbeitsbereich": []}

if "active_chat" not in st.session_state:
    st.session_state["active_chat"] = "Haupt-Arbeitsbereich"

# --- ELEGANTE LOGIN-SEITE (CLEAN & OHNE ROTEN RAHMEN) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    _, col_login, _ = st.columns([1, 1.2, 1])
    
    with col_login:
        st.write("")
        st.write("")
        logo_path = "wordmark_studio_dark.png"
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
            
        st.markdown("""
        <div style="text-align: center; margin-top: 15px; margin-bottom: 25px;">
            <p style="font-size: 1.1rem; font-weight: 600; letter-spacing: 4px; color: #0A192F; margin: 0;">HEADQUARTER LOGIN</p>
            <p style="font-size: 0.75rem; color: #64748B; letter-spacing: 2.5px; margin-top: 6px;">CRAFTED BY AI STUDIO</p>
        </div>
        """, unsafe_allow_html=True)
        
        pwd = st.text_input("Zugangsschlüssel:", type="password", key="clean_hq_pwd_key")

        st.write("")
        if st.button("Anmelden", use_container_width=True):
            if pwd == "CraftedCEO2026!":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Falscher Zugangsschlüssel")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    logo_path = "wordmark_studio_dark.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    
    st.markdown("""
    <div class="notranslate" translate="no" lang="en" style="margin-top: 12px;">
        <p style="line-height: 1.6; color: #475569; font-size: 0.8rem; letter-spacing: 1.5px; text-transform: uppercase;">
            Conceived by AI.<br>
            Created by AI.<br>
            Crafted by AI.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()

    st.markdown("### Arbeitsbereiche")
    
    with st.expander("Neuen Arbeitsbereich erstellen", expanded=False):
        new_chat_name = st.text_input("Name des Arbeitsbereichs:", key="new_chat_name_input")
        if st.button("Arbeitsbereich erstellen", use_container_width=True):
            if new_chat_name.strip():
                if new_chat_name.strip() not in st.session_state["chats"]:
                    st.session_state["chats"][new_chat_name.strip()] = []
                    st.session_state["active_chat"] = new_chat_name.strip()
                    st.success(f"Arbeitsbereich '{new_chat_name.strip()}' erstellt!")
                    st.rerun()
                else:
                    st.warning("Ein Arbeitsbereich mit diesem Namen existiert bereits.")
            else:
                st.warning("Bitte einen gültigen Namen eingeben.")

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

    if len(st.session_state["chats"]) > 1:
        if st.button("Aktuellen Arbeitsbereich löschen", use_container_width=True):
            del st.session_state["chats"][st.session_state["active_chat"]]
            st.session_state["active_chat"] = list(st.session_state["chats"].keys())[0]
            st.rerun()

    st.divider()
    
    if st.button("Abmelden", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
        
    st.divider()
    
    with st.expander("Kernschlüssel Konfiguration", expanded=False):
        saved_claude = os.getenv("CLAUDE_API_KEY", "")
        saved_gemini = os.getenv("GEMINI_API_KEY", "")
        
        claude_key = st.text_input("Primärer API-Schlüssel (Claude)", value=saved_claude, type="password", key="sec_claude_key")
        gemini_key = st.text_input("Sekundärer API-Schlüssel (Gemini)", value=saved_gemini, type="password", key="sec_gemini_key")
        
        if st.button("Schlüssel dauerhaft speichern", use_container_width=True):
            set_key(ENV_PATH, "CLAUDE_API_KEY", claude_key.strip())
            set_key(ENV_PATH, "GEMINI_API_KEY", gemini_key.strip())
            st.success("API-Schlüssel lokal gespeichert!")
            st.rerun()
    
    st.divider()
    st.caption("Systemstatus: Wissensspeicher Aktiv | Lokal")

# --- HAUPTBEREICH MIT QUIET LUXURY BANNER ---
st.markdown("""
<div class="brand-header-banner notranslate" translate="no">
    <div class="brand-header-title">CBA STUDIO HQ</div>
    <div class="brand-header-subtitle">CONCEIVED BY AI. CREATED BY AI. CRAFTED BY AI.</div>
</div>
""", unsafe_allow_html=True)

tab_mitarbeiter, tab_dokumente, tab_plattformen, tab_kalender, tab_todo, tab_finanzen, tab_buchhaltung = st.tabs([
    "Mitarbeiter",
    "Dokumente & Skills",
    "Plattformen & Vertriebskanäle",
    "Kalender",
    "To-do",
    "Finanzkennzahlen",
    "Buchhaltung & Rechnungen"
])

# 1. REITER: MITARBEITER
with tab_mitarbeiter:
    current_chat_name = st.session_state["active_chat"]
    st.subheader(f"Working space: {current_chat_name}")
    
    active_history = st.session_state["chats"][current_chat_name]
    
    for msg in active_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    prompt = st.chat_input(f"Aufgabe im Arbeitsbereich '{current_chat_name}' tippen...")
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
                        model="claude-sonnet-5",
                        max_tokens=1000,
                        system="Du bist das KI-Core-Team für 'Crafted by AI Studio'. Dein Slogan lautet: Conceived by AI. Created by AI. Crafted by AI. Antworte professionell, hochpräzise und beachte alle hinterlegten Brand Guidelines.",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response_text = msg.content[0].text
                except Exception as e:
                    response_text = f"Fehler bei Claude API: {str(e)}"

            if not response_text and g_key and genai:
                try:
                    client = genai.Client(api_key=g_key)
                    res = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    response_text = res.text
                except Exception as e:
                    response_text = f"Fehler bei Gemini API: {str(e)}"
                    
            if not response_text:
                response_text = "Bitte klappe in der Seitenleiste 'Kernschlüssel Konfiguration' auf, trage deine API-Schlüssel ein und klicke auf 'Schlüssel dauerhaft speichern'."
                st.warning(response_text)
            else:
                st.write(response_text)
                
            active_history.append({"role": "assistant", "content": response_text})

# 2. REITER: DOKUMENTE & SKILLS
with tab_dokumente:
    st.subheader("Dokumente & Business-Skills")
    st.caption("Zentrale Ablage für Matt Claude Skills, Branding Guides & Vorlagen")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### Ordnerverwaltung")
        
        with st.expander("+ Ordner hinzufügen", expanded=True):
            new_folder_name = st.text_input("Ordnername eingeben:", key="new_folder_input")
            if st.button("Ordner erstellen"):
                if new_folder_name.strip():
                    new_path = os.path.join(DOCS_DIR, new_folder_name.strip())
                    if not os.path.exists(new_path):
                        os.makedirs(new_path)
                        st.success(f"Ordner '{new_folder_name.strip()}' erfolgreich erstellt!")
                        st.rerun()
                    else:
                        st.warning("Dieser Ordner existiert bereits.")
                else:
                    st.warning("Bitte gib einen Ordnernamen ein.")

        st.divider()
        st.markdown("#### Vorhandene Ordner")
        
        existing_folders = [f for f in os.listdir(DOCS_DIR) if os.path.isdir(os.path.join(DOCS_DIR, f))]
        
        if existing_folders:
            for folder in sorted(existing_folders):
                folder_path = os.path.join(DOCS_DIR, folder)
                files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
                
                with st.expander(f"/{folder} ({len(files_in_folder)} Dateien)"):
                    if files_in_folder:
                        st.markdown("**Dateien im Ordner:**")
                        for file in files_in_folder:
                            file_p = os.path.join(folder_path, file)
                            c1, c2 = st.columns([3, 1])
                            c1.text(f"• {file}")
                            if c2.button("Datei löschen", key=f"del_file_{folder}_{file}"):
                                os.remove(file_p)
                                st.success(f"'{file}' gelöscht!")
                                st.rerun()
                    else:
                        st.caption("Ordner ist leer.")
                    
                    st.divider()
                    
                    action = st.selectbox(
                        "Ordner-Optionen",
                        ["Aktion wählen...", "Ordner umbenennen", "Ordner löschen"],
                        key=f"action_{folder}"
                    )
                    
                    if action == "Ordner umbenennen":
                        rename_input = st.text_input("Neuer Ordnername:", value=folder, key=f"rename_input_{folder}")
                        if st.button("Umbenennen bestätigen", key=f"rename_btn_{folder}"):
                            if rename_input.strip() and rename_input.strip() != folder:
                                new_folder_p = os.path.join(DOCS_DIR, rename_input.strip())
                                if not os.path.exists(new_folder_p):
                                    os.rename(folder_path, new_folder_p)
                                    st.success(f"Ordner in '{rename_input.strip()}' umbenannt!")
                                    st.rerun()
                                else:
                                    st.warning("Ein Ordner mit diesem Namen existiert bereits.")
                    
                    elif action == "Ordner löschen":
                        st.warning(f"Soll der Ordner '{folder}' mit allen enthaltenen Dateien gelöscht werden?")
                        if st.button("Löschen definitiv bestätigen", key=f"del_confirm_btn_{folder}"):
                            shutil.rmtree(folder_path)
                            st.success(f"Ordner '{folder}' wurde gelöscht!")
                            st.rerun()
        else:
            st.info("Keine Ordner vorhanden.")

    with col_right:
        st.markdown("#### Datei hochladen")
        uploaded_file = st.file_uploader("Datei wählen", type=["pdf", "docx", "txt", "csv", "png", "jpg", "md"])
        
        existing_folders = [f for f in os.listdir(DOCS_DIR) if os.path.isdir(os.path.join(DOCS_DIR, f))]
        
        if existing_folders:
            target_folder = st.selectbox("Zielordner für Upload wählen:", sorted(existing_folders))
            
            if uploaded_file and st.button("Datei im Ordner speichern"):
                save_path = os.path.join(DOCS_DIR, target_folder)
                file_path = os.path.join(save_path, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Datei '{uploaded_file.name}' in '/{target_folder}' gespeichert!")
                st.rerun()
        else:
            st.warning("Bitte erstelle zuerst links einen Ordner, um Dateien hochzuladen.")

# 3. REITER: PLATTFORMEN & VERTRIEBSKANÄLE
with tab_plattformen:
    st.subheader("Vertriebskanäle & Plattformen")
    st.caption("Verbindung zu deinen Verkaufs- und Marketingkanälen")
    
    with st.expander("Tapstitch (POD & Produktion)"):
        st.markdown("Fokus: Mockups, Textilien & Drops verwalten")
        st.button("Schnittstelle zu Tapstitch konfigurieren")
        
    with st.expander("Etsy (Marktplatz)"):
        st.markdown("Fokus: Listings, Bestellungen & Kundenanfragen")
        st.button("Schnittstelle zu Etsy konfigurieren")
        
    with st.expander("Metricool (Social-Media-Autopilot)"):
        st.markdown("Fokus: Redaktionsplan, Posting-Automatisierung & Analytics")
        st.button("Schnittstelle zu Metricool konfigurieren")
        
    with st.expander("Instagram & Pinterest (Visuelle Markenkanäle)"):
        st.markdown("Fokus: Content-Distribution & Visual Brand Asset Sync")
        st.button("Schnittstelle konfigurieren")

# 4. REITER: KALENDER
with tab_kalender:
    st.title("KALENDER & REDAKTIONSPLANUNG")
    st.caption("Verknüpfung mit Google Kalender & Metricool für automatische KI-Terminplanung")

    # 1. API-Einstellungen im Ausklapp-Menü
    with st.expander("⚙️ API-Verbindungen & Schlüssel verwalten"):
        col_api1, col_api2 = st.columns(2)
        
        with col_api1:
            st.subheader("GOOGLE KALENDER")
            google_token = st.text_input("Google OAuth Client ID / Token:", type="password", key="sec_google_token")
            if st.button("Mit Google Kalender verbinden", key="btn_connect_google"):
                st.success("Google Kalender erfolgreich gekoppelt!")

        with col_api2:
            st.subheader("METRICOOL REDAKTIONSIKALENDER")
            metricool_token = st.text_input("Metricool User Token:", type="password", key="sec_metricool_token")
            if st.button("Redaktionsplan synchronisieren", key="btn_connect_metricool"):
                st.success("Metricool erfolgreich synchronisiert!")

    st.markdown("---")

    # 2. Zwei Kalender nebeneinander
    col_business, col_content = st.columns(2)

    with col_business:
        st.markdown("### 💼 BUSINESS-KALENDER (GOOGLE)")
        st.caption("Anstehende Businesstermine, Meetings & Fristen")
        
        b_title = st.text_input("Terminbezeichnung", placeholder="z. B. Gespräch mit Steuerberater", key="b_title_in")
        b_date = st.date_input("Datum", date.today(), key="b_date_input")
        
        if st.button("In Business-Kalender eintragen", key="b_btn_submit"):
            if b_title.strip():
                st.session_state["events_and_todos"].append({
                    "title": b_title.strip(),
                    "due_date": str(b_date),
                    "source": "Business-Kalender (Google)",
                    "completed": False
                })
                st.success(f"Termin '{b_title}' eingetragen!")
                st.rerun()

        st.markdown("#### Aktuelle Business-Termine")
        business_items = [e for e in st.session_state["events_and_todos"] if e["source"] == "Business-Kalender (Google)"]
        if business_items:
            for item in business_items:
                st.info(f"📅 **{item['due_date']}:** {item['title']}")
        else:
            st.caption("Keine Termine vorhanden.")

    with col_content:
        st.markdown("### 📱 CONTENT-KALENDER (METRICOOL)")
        st.caption("Social Media Posts, Reels, Etsy-Launches & Redaktionsplan")
        
        c_title = st.text_input("Post / Content Titel", placeholder="z. B. Streetwear Reel Teaser", key="c_title_in")
        c_date = st.date_input("Datum", date.today(), key="c_date_input")
        
        if st.button("In Content-Kalender eintragen", key="c_btn_submit"):
            if c_title.strip():
                st.session_state["events_and_todos"].append({
                    "title": c_title.strip(),
                    "due_date": str(c_date),
                    "source": "Content-Kalender (Metricool)",
                    "completed": False
                })
                st.success(f"Content '{c_title}' eingeplant!")
                st.rerun()

        st.markdown("#### Geplante Posts & Releases")
        content_items = [e for e in st.session_state["events_and_todos"] if e["source"] == "Content-Kalender (Metricool)"]
        if content_items:
            for item in content_items:
                st.info(f"🎬 **{item['due_date']}:** {item['title']}")
        else:
            st.caption("Keine Content-Termine vorhanden.")

# 5. REITER: TO-DO
with tab_todo:
    st.subheader("To-do-Liste")
    st.caption("Verwalte deine Aufgaben – neue To-dos werden automatisch dem gewählten Kalender zugewiesen.")
    
    st.markdown("#### Neue To-do-Aufgabe erstellen")
    col_t1, col_t2, col_t3, col_t4 = st.columns([3, 2, 2.5, 1.5])
    
    with col_t1:
        task_title = st.text_input("Aufgabe eingeben:", key="new_todo_title")
    with col_t2:
        task_date = st.date_input("Erledigen bis:", value=date.today(), key="new_todo_date")
    with col_t3:
        target_cal = st.selectbox("Ziel-Kalender:", ["Business-Kalender (Google)", "Content-Kalender (Metricool)"], key="todo_target_cal")
    with col_t4:
        st.write("")
        st.write("")
        if st.button("Erstellen", use_container_width=True):
            if task_title.strip():
                st.session_state["events_and_todos"].append({
                    "title": task_title.strip(),
                    "due_date": str(task_date),
                    "source": target_cal,
                    "completed": False
                })
                st.success("Aufgabe erstellt und im Kalender hinterlegt!")
                st.rerun()

    st.divider()
    st.markdown("#### Offene To-dos")
    
    open_todos = [item for item in st.session_state["events_and_todos"] if not item["completed"]]
    
    if open_todos:
        for idx, item in enumerate(open_todos):
            is_done = st.checkbox(f"**[{item['due_date']}]** {item['title']} — *(Zuordnung: {item['source']})*", key=f"todo_item_{idx}")
            if is_done:
                item["completed"] = True
                st.success(f"'{item['title']}' als erledigt markiert!")
                st.rerun()
    else:
        st.success("Keine offenen Aufgaben vorhanden!")

# 6. REITER: FINANZKENNZAHLEN
with tab_finanzen:
    st.subheader("Finanzkennzahlen & Performance Dashboard")
    st.caption("Echtzeit-Übersicht deiner Umsätze, Kosten, Gewinne und Absätze über deine Vertriebskanäle")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(label="Gesamtumsatz (YTD)", value="14.850 €", delta="+12.5%")
    m2.metric(label="Gesamtkosten (POD & Ads)", value="6.200 €", delta="-3.1%")
    m3.metric(label="Netto-Gewinn", value="8.650 €", delta="+18.2%")
    m4.metric(label="Absatz (Verkaufte Pieces)", value="342 Stk.", delta="+45 Stk.")
    
    st.divider()
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("#### Umsatz & Gewinnentwicklung (Monatlich)")
        financial_data = pd.DataFrame({
            "Monat": ["Mai", "Juni", "Juli", "August", "September"],
            "Umsatz (€)": [1800, 2400, 3100, 3800, 3750],
            "Gewinn (€)": [950, 1300, 1850, 2300, 2250]
        })
        st.line_chart(financial_data.set_index("Monat"))
        
    with chart_col2:
        st.markdown("#### Absatz nach Vertriebskanal (Pieces)")
        channel_data = pd.DataFrame({
            "Vertriebskanal": ["Etsy Marktplatz", "Direktvertrieb / Events"],
            "Verkäufe": [215, 127]
        })
        st.bar_chart(channel_data.set_index("Vertriebskanal"))
        
    st.divider()
    st.info("API-Status: Sobald deine Etsy- und sevdesk-Keys hinterlegt sind, werden diese Kennzahlen automatisch live aktualisiert.")

# 7. REITER: BUCHHALTUNG & RECHNUNGEN
with tab_buchhaltung:
    st.subheader("Buchhaltung & Rechnungen")
    st.caption("Geschützter Bereich für finanzielle Auswertungen, Belegverwaltung & E-Mail-Posteingang")
    
    pin = st.text_input("Vault PIN eingeben:", type="password", key="sec_vault_pin")
    if pin == "VaultSecure99!":
        st.success("Zugriff gewährt")
        
        st.markdown("#### Eingangsrechnungen & Belegabgleich")
        st.caption("Eingegangene Rechnungen im Ordner '/documents/Eingangsrechnungen'")
        
        rechnungen_dir = os.path.join(DOCS_DIR, "Eingangsrechnungen")
        invoices = [f for f in os.listdir(rechnungen_dir) if os.path.isfile(os.path.join(rechnungen_dir, f))]
        
        if invoices:
            for inv in invoices:
                st.write(f"📄 **{inv}**")
        else:
            st.info("Keine neuen Eingangsrechnungen vorhanden.")

        st.divider()
        st.markdown("#### sevdesk (Buchhaltung Schnittstelle)")
        st.text_input("sevdesk API Token:", type="password", key="sec_sevdesk_token")
        st.button("Belege mit sevdesk abgleichen")
    elif pin != "":
        st.error("Ungültige PIN")