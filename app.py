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

# --- VERBINDUNG ZUM GOOGLE SHEET (MIT FIX) ---
def get_connection():
    # Wir holen die Daten aus den Secrets
    creds = dict(st.secrets["connections"]["gsheets"])
    # Falls der Schlüssel im Textformat vorliegt, korrigieren wir die Zeilenumbrüche
    if "private_key" in creds:
        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
    
    # Verbindung mit den korrigierten Zugangsdaten herstellen
    return st.connection("gsheets", type=GSheetsConnection, **creds)

try:
    conn = get_connection()
except Exception as e:
    st.error("Verbindung fehlgeschlagen. Bitte prüfe die Secrets.")
    st.stop()

def load_data():
    try:
        # Versucht das Blatt "Einkaufsliste" zu lesen
        return conn.read(worksheet="Einkaufsliste", ttl=0)
    except:
        # Falls das Blatt nicht existiert oder leer ist, erstelle leeres Gerüst
        return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])

# --- LOGIN BEREICH ---
st.title("🏘️ Nachbarschafts-App")

user = st.selectbox("Wer bist du?", ["Bitte wählen"] + list(PASSWORDS.keys()))
pin = st.text_input("Gib deinen PIN ein:", type="password")

if user != "Bitte wählen" and pin == PASSWORDS[user]:
    st.success(f"Willkommen, {user}!")
    
    # Daten laden
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
                # Neue Daten an das bestehende DataFrame hängen
                updated_df = pd.concat([df, new_row], ignore_index=True)
                # Zurück zu Google Sheets schreiben
                conn.update(worksheet="Einkaufsliste", data=updated_df)
                st.success(f"'{neuer_artikel}' wurde hinzugefügt!")
                st.rerun()

        st.subheader("Deine aktuellen Bestellungen")
        # Filtere die Liste nur nach den Einträgen des Nutzers
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
            offene_artikel = df[df["Status"] == "Offen"]
            
            if offene_artikel.empty:
                st.balloons()
                st.success("Alles erledigt! Genieße deinen Feierabend.")
            else:
                for index, row in offene_artikel.iterrows():
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{row['Artikel']}** (für {row['Besteller']})")
                    if col2.button("Erledigt", key=f"check_{index}"):
                        # Status direkt im DataFrame ändern
                        df.at[index, "Status"] = "Erledigt"
                        # Das komplette aktualisierte Blatt hochladen
                        conn.update(worksheet="Einkaufsliste", data=df)
                        st.rerun()
        else:
            st.info("Die Liste ist momentan komplett leer.")
