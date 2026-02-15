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
        # Wir erstellen die Verbindung ganz ohne manuelle Parameter-Übergabe.
        # Streamlit zieht sich die Daten AUTOMATISCH aus [connections.gsheets] in den Secrets.
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return None

conn = get_connection()

# --- DATEN LADEN FUNKTION ---
def load_data():
    if conn is None:
        return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])
    
    try:
        # Wir erzwingen das Lesen des Arbeitsblatts "Einkaufsliste"
        data = conn.read(worksheet="Einkaufsliste", ttl=0)
        
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])
        return data
    except Exception as e:
        # Falls das Blatt nicht gefunden wird, geben wir ein leeres Gerüst zurück
        return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])

# --- LOGIN BEREICH ---
st.title("🏘️ Nachbarschafts-App")

user = st.selectbox("Wer bist du?", ["Bitte wählen"] + list(PASSWORDS.keys()))
pin = st.text_input("Gib deinen PIN ein:", type="password")

if user != "Bitte wählen" and pin == PASSWORDS[user]:
    st.success(f"Eingeloggt als {user}")
    
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
