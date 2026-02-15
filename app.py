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

# --- VERBINDUNG ZUM GOOGLE SHEET ---
def get_connection():
    try:
        # Wir laden die Secrets als Dictionary
        # .to_dict() stellt sicher, dass wir die Daten bearbeiten können
        creds = st.secrets["connections"]["gsheets"].to_dict()
        
        # Falls der Key aus den Secrets noch \n als Text enthält,
        # wandeln wir diese in echte Zeilenumbrüche um (PEM-Fix).
        if "private_key" in creds:
            creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        
        # WICHTIG: Wir entfernen 'type' aus den creds, 
        # da wir es als Argument 'type=GSheetsConnection' bereits übergeben.
        if "type" in creds:
            del creds["type"]
        
        # Verbindung herstellen
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
        # Versucht das Blatt "Einkaufsliste" zu lesen
        data = conn.read(worksheet="Einkaufsliste", ttl=0)
        
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])
        return data
    except Exception:
        # Falls das Blatt nicht gefunden wird (z.B. falscher Name), leeres Gerüst
        return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])

# --- LOGIN BEREICH ---
st.title("🏘️ Nachbarschafts-App")

user = st.selectbox("Wer bist du?", ["Bitte wählen"] + list(PASSWORDS.keys()))
pin = st.text_input("Gib deinen PIN ein:", type="password")

if user != "Bitte wählen" and pin == PASSWORDS[user]:
    st.success(f"Willkommen, {user}!")
    
    # Daten frisch aus dem Sheet laden
    df = load_data()

    # --- ANSICHT FÜR NACHBARN (Bestell-Modus) ---
    if user != "Einkäufer":
        st.header(f"Deine Einkaufsliste")
        
        with st.form("add_item", clear_on_submit=True):
            neuer_artikel = st.text_input("Was brauchst du?")
            submit = st.form_submit_button("Hinzufügen")
            
            if submit and neuer_artikel:
                new_row = pd.DataFrame([{
                    "Besteller": user,
                    "Artikel": neuer_artikel,
                    "Status": "Offen"
                }])
                # Neue Zeile anhängen
                updated_df = pd.concat([df, new_row], ignore_index=True)
                # Zu Google Sheets hochladen
                conn.update(worksheet="Einkaufsliste", data=updated_df)
                st.success(f"'{neuer_artikel}' wurde hinzugefügt!")
                st.rerun()

        st.subheader("Deine aktuellen Bestellungen")
        meine_liste = df[df["Besteller"] == user]
        if not meine_liste.empty:
            st.table(meine_liste[["Artikel", "Status"]])
        else:
            st.info("Du hast noch nichts auf der Liste.")

    # --- ANSICHT FÜR EINKÄUFER (Abhak-Modus) ---
    else:
        st.header("🛒 Alle offenen Einkäufe")
        
        if not df.empty:
            # Nur Einträge zeigen, die noch "Offen" sind
            offene_artikel = df[df["Status"] == "Off
