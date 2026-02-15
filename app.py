import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Nachbarschafts-Einkaufshilfe", layout="centered")

# --- PASSWÖRTER (PINs) ---
PASSWORDS = {
    "Nachbar A": "1111",
    "Nachbar B": "2222",
    "Einkäufer": "0000"
}

# --- VERBINDUNG ZUM GOOGLE SHEET (DER PEM-FIX) ---
def get_connection():
    try:
        # 1. Wir holen die Zugangsdaten direkt aus den Secrets
        # Wir müssen .to_dict() nutzen, damit wir die Daten bearbeiten können
        creds = st.secrets["connections"]["gsheets"].to_dict()
        
        # 2. DER ENTSCHEIDENDE FIX:
        # Wir ersetzen die Text-Zeichenfolge '\n' durch echte Zeilenumbrüche.
        # Das löst den "Unable to load PEM file" Fehler.
        if "private_key" in creds:
            creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        
        # 3. Verbindung mit den reparierten 'service_account' Daten herstellen
        return st.connection("gsheets", type=GSheetsConnection, **creds)
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return None

conn = get_connection()

# --- DATEN LADEN ---
def load_data():
    if conn is None:
        return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])
    try:
        # Falls das Sheet "Einkaufsliste" heißt:
        data = conn.read(worksheet="Einkaufsliste", ttl=0)
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])
        return data
    except:
        return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])

# --- UI LOGIK ---
st.title("🏘️ Nachbarschafts-App")

user = st.selectbox("Wer bist du?", ["Bitte wählen"] + list(PASSWORDS.keys()))
pin = st.text_input("PIN eingeben:", type="password")

if user != "Bitte wählen" and pin == PASSWORDS[user]:
    st.success(f"Hallo {user}!")
    df = load_data()

    if user != "Einkäufer":
        st.subheader("Was brauchst du?")
        with st.form("neu", clear_on_submit=True):
            artikel = st.text_input("Artikel")
            if st.form_submit_button("Hinzufügen") and artikel:
                new_row = pd.DataFrame([{"Besteller": user, "Artikel": artikel, "Status": "Offen"}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Einkaufsliste", data=updated_df)
                st.success("Gespeichert!")
                st.rerun()
        
        st.table(df[df["Besteller"] == user])

    else:
        st.subheader("Offene Einkäufe")
        offene = df[df["Status"] == "Offen"] if not df.empty else []
        for index, row in offene.iterrows():
            if st.button(f"Erledigt: {row['Artikel']} ({row['Besteller']})", key=index):
                df.at[index, "Status"] = "Erledigt"
                conn.update(worksheet="Einkaufsliste", data=df)
                st.rerun()

elif pin:
    st.error("Falscher PIN")
