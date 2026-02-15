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
        creds = st.secrets["connections"]["gsheets"].to_dict()
        if "private_key" in creds:
            creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        if "type" in creds:
            del creds["type"]
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
        data = conn.read(worksheet="Einkaufsliste", ttl=0)
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])
        return data
    except Exception:
        return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])

# --- LOGIN BEREICH ---
st.title("🏘️ Nachbarschafts-App")

user = st.selectbox("Wer bist du?", ["Bitte wählen"] + list(PASSWORDS.keys()))
pin = st.text_input("Gib deinen PIN ein:", type="password")

if user != "Bitte wählen" and pin == PASSWORDS[user]:
    st.success(f"Willkommen, {user}!")
    df = load_data()

    # --- ANSICHT FÜR NACHBARN ---
    if user != "Einkäufer":
        st.header(f"Deine Einkaufsliste")
        with st.form("add_item", clear_on_submit=True):
            neuer_artikel = st.text_input("Was brauchst du?")
            submit = st.form_submit_button("Hinzufügen")
            if submit and neuer_artikel:
                new_row = pd.DataFrame([{"Besteller": user, "Artikel": neuer_artikel, "Status": "Offen"}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Einkaufsliste", data=updated_df)
                st.success(f"'{neuer_artikel}' wurde hinzugefügt!")
                st.rerun()

        st.subheader("Deine aktuellen Bestellungen")
        meine_liste = df[df["Besteller"] == user]
        if not meine_liste.empty:
            st.table(meine_liste[["Artikel", "Status"]])
        else:
            st.info("Du hast noch nichts auf der Liste.")

    # --- ANSICHT FÜR EINKÄUFER ---
    else:
        st.header("🛒 Alle offenen Einkäufe")
        if not df.empty:
            # Hier war der Fehler: Das Wort "Offen" muss in Anführungszeichen stehen
            offene_artikel = df[df["Status"] == "Offen"]
            
            if offene_artikel.empty:
                st.balloons()
                st.success("Alles erledigt!")
            else:
                for index, row in offene_artikel.iterrows():
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{row['Artikel']}** (für {row['Besteller']})")
                    if col2.button("Erledigt", key=f"check_{index}"):
                        df.at[index, "Status"] = "Erledigt"
                        conn.update(worksheet="Einkaufsliste", data=df)
                        st.rerun()
        else:
            st.info("Die Liste ist momentan komplett leer.")

elif pin != "" and user != "Bitte wählen":
    st.error("Falscher PIN.")
