import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import json

# Seitenkonfiguration
st.set_page_config(
    page_title="Image Task Uploader",
    page_icon="📋",
    layout="wide"
)

# Custom CSS für besseres Design
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .upload-section {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("📋 Image Task Uploader")
st.markdown("Laden Sie Bilder mit Aufgaben hoch und lassen Sie diese automatisch verarbeiten.")
st.divider()

# Webhook-Konfiguration aus Secrets laden
try:
    webhook_url = st.secrets.get("WEBHOOK_URL", "")
    
    if not webhook_url:
        st.error("⚠️ Webhook-URL ist nicht konfiguriert. Bitte fügen Sie 'WEBHOOK_URL' in den Streamlit Secrets hinzu.")
        st.stop()
        
except Exception as e:
    st.error(f"⚠️ Fehler beim Laden der Konfiguration: {str(e)}")
    st.stop()

# Initialisierung des Session States
if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None
if 'processing_result' not in st.session_state:
    st.session_state.processing_result = None

# Upload-Sektion
st.subheader("📤 Bild hochladen")

uploaded_file = st.file_uploader(
    "Wählen Sie ein Bild aus (PNG, JPG, JPEG)",
    type=['png', 'jpg', 'jpeg'],
    help="Unterstützte Formate: PNG, JPG, JPEG"
)

# Bildvorschau und Verarbeitung
if uploaded_file is not None:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🖼️ Bildvorschau")
        try:
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)
            st.session_state.uploaded_image = uploaded_file
            
            # Bildinformationen anzeigen
            st.caption(f"Dateiname: {uploaded_file.name}")
            st.caption(f"Bildgröße: {image.size[0]} x {image.size[1]} px")
            st.caption(f"Dateigröße: {uploaded_file.size / 1024:.2f} KB")
            
        except Exception as e:
            st.error(f"❌ Fehler beim Laden des Bildes: {str(e)}")
    
    with col2:
        st.subheader("⚙️ Verarbeitung")
        
        # Upload-Button
        if st.button("🚀 Bild verarbeiten", type="primary", use_container_width=True):
            with st.spinner("Bild wird verarbeitet..."):
                try:
                    # Datei zurücksetzen und als multipart/form-data senden
                    uploaded_file.seek(0)
                    
                    # Files dict für multipart upload
                    files = {
                        'file': (uploaded_file.name, uploaded_file, uploaded_file.type)
                    }
                    
                    # POST-Request an Webhook mit file upload
                    response = requests.post(
                        webhook_url,
                        files=files,
                        timeout=30
                    )
                    
                    # Erfolgreiche Antwort verarbeiten
                    if response.status_code == 200:
                        st.success("✅ Bild erfolgreich verarbeitet!")
                        st.session_state.processing_result = response.json()
                    else:
                        st.error(f"❌ Fehler bei der Verarbeitung (Status {response.status_code}): {response.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("❌ Zeitüberschreitung: Der Server antwortet nicht. Bitte versuchen Sie es später erneut.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Verbindungsfehler: Webhook-URL ist nicht erreichbar.")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Netzwerkfehler: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Unerwarteter Fehler: {str(e)}")

# Ergebnis-Sektion
if st.session_state.processing_result:
    st.divider()
    st.subheader("📊 Verarbeitete Aufgaben")
    
    result = st.session_state.processing_result
    
    # Verschiedene Darstellungsoptionen basierend auf der Antwortstruktur
    if isinstance(result, dict):
        # Wenn die Antwort Aufgaben enthält
        if "tasks" in result or "items" in result:
            tasks = result.get("tasks", result.get("items", []))
            
            if isinstance(tasks, list):
                for idx, task in enumerate(tasks, 1):
                    with st.expander(f"Aufgabe {idx}", expanded=True):
                        if isinstance(task, dict):
                            for key, value in task.items():
                                st.markdown(f"**{key.capitalize()}:** {value}")
                        else:
                            st.write(task)
            else:
                st.json(result)
        
        # Wenn die Antwort Text-Extraktion enthält
        elif "text" in result or "content" in result:
            text_content = result.get("text", result.get("content", ""))
            st.markdown("### Extrahierter Inhalt")
            st.text_area("", text_content, height=300, disabled=True)
        
        # Standardmäßige JSON-Darstellung
        else:
            st.json(result)
    
    elif isinstance(result, list):
        # Liste von Aufgaben
        for idx, item in enumerate(result, 1):
            with st.expander(f"Element {idx}", expanded=True):
                if isinstance(item, dict):
                    for key, value in item.items():
                        st.markdown(f"**{key.capitalize()}:** {value}")
                else:
                    st.write(item)
    
    else:
        # Einfacher Text oder andere Formate
        st.write(result)
    
    # Download-Button für Ergebnisse
    st.download_button(
        label="💾 Ergebnis als JSON herunterladen",
        data=json.dumps(result, indent=2, ensure_ascii=False),
        file_name="verarbeitete_aufgaben.json",
        mime="application/json"
    )
    
    # Reset-Button
    if st.button("🔄 Neues Bild hochladen"):
        st.session_state.uploaded_image = None
        st.session_state.processing_result = None
        st.rerun()

# Footer mit Anleitung
st.divider()
with st.expander("ℹ️ Anleitung & Hilfe"):
    st.markdown("""
    ### So verwenden Sie diese App:
    
    1. **Bild auswählen**: Klicken Sie auf "Browse files" oder ziehen Sie ein Bild in den Upload-Bereich
    2. **Vorschau prüfen**: Überprüfen Sie die Bildvorschau auf der linken Seite
    3. **Verarbeitung starten**: Klicken Sie auf "Bild verarbeiten"
    4. **Ergebnisse ansehen**: Die extrahierten Aufgaben werden strukturiert angezeigt
    
    ### Unterstützte Formate:
    - PNG (.png)
    - JPEG (.jpg, .jpeg)
    
    ### Konfiguration:
    Die Webhook-URL wird über Streamlit Secrets verwaltet.
    
    **Benötigte Secrets:**
    ```toml
    WEBHOOK_URL = "https://ihre-n8n-webhook-url.com/webhook/xyz"
    ```
    """)

# Debug-Modus (nur für Entwicklung)
if st.secrets.get("DEBUG_MODE", False):
    with st.expander("🔧 Debug-Informationen"):
        st.write("Webhook URL:", webhook_url[:30] + "..." if len(webhook_url) > 30 else webhook_url)
        st.write("Session State:", st.session_state)