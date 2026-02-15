import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("Diagnose-Modus")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Test 1: Erkennt er die URL aus den Secrets?
    st.write("✅ Verbindung zum Modul hergestellt.")
    
    # Test 2: Kann er das Dokument grundsätzlich sehen?
    # Wir lassen 'worksheet' weg, um zu sehen, ob er das erste Blatt findet
    df = conn.read(ttl=0)
    st.write("✅ Zugriff auf das Sheet erfolgreich!")
    st.write("Gefundene Spalten:", list(df.columns))
    st.write("Gefundene Daten:", df)

except Exception as e:
    st.error("❌ Fehler beim Zugriff auf Google Sheets:")
    st.code(str(e))
    st.info("Checkliste: 1. Service-Email im Sheet freigegeben? 2. Secrets korrekt im TOML-Format? 3. Sheet-URL korrekt?")
