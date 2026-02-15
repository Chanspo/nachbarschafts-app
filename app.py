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

# --- VERBINDUNG ZUM GOOGLE SHEET (DER FINALE FIX) ---
def get_connection():
    try:
        # 1. Wir laden die Daten aus den Secrets in ein Dictionary
        # .to_dict() ist wichtig, damit wir die Daten bearbeiten können
        creds = st.secrets["connections"]["gsheets"].to_dict()
        
        # 2. Wir entfernen 'type' aus den creds, um den "multiple values" Fehler zu vermeiden
        # Der Wert "service_account" wird hier gelöscht, da er sonst mit dem 
        # Argument 'type=GSheetsConnection' kollidiert.
        if "type" in creds:
            del creds["type"]
            
        # 3. Wir korrigieren die Zeilenumbrüche für den PEM-Key
        if "private_key" in creds:
            creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        
        # 4. Verbindung aufbauen: Wir übergeben GSheetsConnection als Typ 
        # und die restlichen Berechtigungen als Zusatz-Argumente (**creds)
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
        # Hier wird das Blatt "Einkaufsliste" geladen
        data = conn.read(worksheet="Einkaufsliste", ttl=0)
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])
        return data
    except Exception as e:
        # Falls das Blatt nicht existiert, geben wir ein leeres Gerüst zurück
        return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])

# --- LOGIN BEREICH ---
st.title("🏘️ Nachbarschafts-App")

user = st.selectbox("Wer bist du?", ["Bitte wählen"] + list(PASSWORDS.keys()))
pin = st.text_input("Gib deinen PIN ein:", type="password")

if user != "Bitte wählen" and pin == PASSWORDS[user]:
    st.success(f"Eingeloggt als {user}")
    
    # Daten frisch laden
    df = load_data()

    # --- ANSICHT FÜR NACHBARN ---
    if user != "Einkäufer":
        st.header(f"Deine Wünsche")
        
        with st.form("add_form", clear_on_submit=True):
            artikel = st.text_input("Was brauchst du?")
            if st.form_submit_button("Hinzufügen"):
                if artikel:
                    new_row = pd.DataFrame([{"Besteller": user, "Artikel": artikel, "Status": "Offen"}])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    # Zurückschreiben ins Google Sheet
                    conn.update(worksheet="Einkaufsliste", data=updated_df)
                    st.success(f"'{artikel}' gespeichert!")
                    st.rerun()

        # Eigene Einträge anzeigen
        meine_artikel = df[df["Besteller"] == user]
        if not meine_artikel.empty:
            st.table(meine_artikel[["Artikel", "Status"]])
        else:
            st.write("Deine Liste ist aktuell leer.")

    # --- ANSICHT FÜR EINKÄUFER ---
    else:
        st.header("🛒 Einkaufsliste für alle")
        if not df.empty:
            offene = df[df["Status"] == "Offen"]
            
            if offene.empty:
                st.success("Keine offenen Bestellungen!")
            else:
                for index, row in offene.iterrows():
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{row['Artikel']}** (für {row['Besteller']})")
                    if col2.button("Erledigt", key=f"btn_{index}"):
                        df.at[index, "Status"] = "Erledigt"
                        conn.update(worksheet="Einkaufsliste", data=df)
                        st.rerun()
        else:
            st.info("Die Liste im Google Sheet ist noch komplett leer.")

elif pin != "" and user != "Bitte wählen":
    st.error("Falscher PIN.")
