import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- KONFIGURATION ---
st.set_page_config(page_title="Nachbarschafts-Einkaufshilfe", layout="centered")

# Passwörter (PINs)
PASSWORDS = {
    "Nachbar A": "1111",
    "Nachbar B": "2222",
    "Einkäufer": "0000"
}

# --- VERBINDUNG ZUM GOOGLE SHEET ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Wir laden explizit das Blatt "Einkaufsliste"
        return conn.read(worksheet="Einkaufsliste", ttl=0)
    except Exception:
        # Falls das Blatt leer ist oder nicht gefunden wird, leeres Gerüst erstellen
        return pd.DataFrame(columns=["Besteller", "Artikel", "Status"])

# --- LOGIN BEREICH ---
st.title("🏘️ Nachbarschafts-App")

user = st.selectbox("Wer bist du?", ["Bitte wählen"] + list(PASSWORDS.keys()))
pin = st.text_input("Gib deinen PIN ein:", type="password")

if user != "Bitte wählen" and pin == PASSWORDS[user]:
    st.success(f"Willkommen, {user}!")
    
    # Daten laden
    df = load_data()

    # --- ANSICHT FÜR NACHBARN ---
    if user != "Einkäufer":
        st.header(f"Deine Einkaufsliste")
        
        # Neuen Artikel hinzufügen
        with st.form("add_item"):
            neuer_artikel = st.text_input("Was brauchst du?")
            submit = st.form_submit_button("Hinzufügen")
            
            if submit and neuer_artikel:
                new_row = pd.DataFrame([{
                    "Besteller": user,
                    "Artikel": neuer_artikel,
                    "Status": "Offen"
                }])
                # Neuen Artikel an die bestehenden Daten hängen
                updated_df = pd.concat([df, new_row], ignore_index=True)
                # Zu Google Sheets hochladen
                conn.update(worksheet="Einkaufsliste", data=updated_df)
                st.success(f"'{neuer_artikel}' wurde hinzugefügt!")
                st.rerun()

        # Eigene Einträge anzeigen
        st.subheader("Deine aktuellen Bestellungen")
        meine_liste = df[df["Besteller"] == user]
        if not meine_liste.empty:
            st.table(meine_liste[["Artikel", "Status"]])
        else:
            st.info("Du hast noch nichts auf der Liste.")

    # --- ANSICHT FÜR EINKÄUFER ---
    else:
        st.header("🛒 Alle Einkäufe")
        
        if not df.empty:
            # Nur offene Artikel anzeigen
            offene_artikel = df[df["Status"] == "Offen"]
            
            if offene_artikel.empty:
                st.balloons()
                st.success("Alles erledigt! Keine offenen Einkäufe.")
            else:
                for index, row in offene_artikel.iterrows():
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{row['Artikel']}** (für {row['Besteller']})")
                    if col2.button("Erledigt", key=f"check_{index}"):
                        # Status im DataFrame ändern
                        df.at[index, "Status"] = "Erledigt"
                        # Ganzes DataFrame bei Google aktualisieren
                        conn.update(worksheet="Einkaufsliste", data=df)
                        st.rerun()
        else:
            st.info("Die Liste ist momentan komplett leer.")

elif pin != "" and user != "Bitte wählen":
    st.error("Falscher PIN. Bitte versuche es erneut.")
