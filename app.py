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
        # Wir laden die Secrets
        creds = dict(st.secrets["connections"]["gsheets"])
        # Fix für den Private Key (wandelt Text-\n in echte Umbrüche um)
        if "private_key" in creds:
            creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        
        # Verbindung herstellen
        return st.connection("gsheets", type=GSheetsConnection, **creds)
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return None

conn = get_connection()

# --- DATEN LADEN FUNKTION ---
def load_data():
    if conn is None:
        return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])
    
    try:
        # Wir versuchen das Blatt "Einkaufsliste" zu lesen
        data = conn.read(worksheet="Einkaufsliste", ttl=0)
        
        # Falls das Blatt existiert, aber völlig leer ist
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])
        return data
    except Exception as e:
        # Falls das Blatt "Einkaufsliste" nicht gefunden wird
        st.info("Hinweis: Das Tabellenblatt 'Einkaufsliste' wurde nicht gefunden. Bitte prüfe den Namen im Google Sheet.")
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
                    # Neue Zeile an bestehende Daten hängen
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    # Hochladen zu Google
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

elif pin != "" and user != "Bitte wählen":
    st.error("Falscher PIN.")
