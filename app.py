import streamlit as st
import pandas as pd

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Nachbar-App", layout="centered", page_icon="🏘️")

# --- DATEN-SPEICHER INITIALISIEREN ---
if 'einkaufsliste' not in st.session_state:
    st.session_state.einkaufsliste = pd.DataFrame(columns=["Besteller", "Artikel", "Status"])

# --- LOGIN-DATEN ---
USERS = {
    "Nachbar A": "1111",
    "Nachbar B": "2222",
    "Einkäufer": "0000"
}

# --- UI ---
st.title("🏘️ Nachbarschaftshilfe")

# Sidebar für Login
st.sidebar.header("Anmeldung")
user = st.sidebar.selectbox("Wer bist du?", ["Bitte wählen"] + list(USERS.keys()))
pin = st.sidebar.text_input("PIN", type="password")

# --- HAUPT-LOGIK ---
if user != "Bitte wählen" and pin == USERS[user]:
    st.sidebar.success(f"Eingeloggt als {user}")

    # --- BEREICH FÜR EINKÄUFER ---
    if user == "Einkäufer":
        st.header("🛒 Alle offenen Einkäufe")
        df = st.session_state.einkaufsliste
        offene_posten = df[df["Status"] == "Offen"]
        
        if offene_posten.empty:
            st.success("Alles erledigt! Keine offenen Wünsche.")
        else:
            for index, row in offene_posten.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['Artikel']}** (für {row['Besteller']})")
                if col2.button("Erledigt ✅", key=f"done_{index}"):
                    st.session_state.einkaufsliste.at[index, "Status"] = "Erledigt"
                    st.rerun()
        
        with st.expander("Vergangene Einkäufe einblenden"):
            st.dataframe(df[df["Status"] == "Erledigt"])

    # --- BEREICH FÜR NACHBARN ---
    else:
        tab1, tab2 = st.tabs(["➕ Neuer Wunsch", "📋 Meine Liste & Korrektur"])

        with tab1:
            st.subheader("Was brauchst du heute?")
            with st.form("wunsch_form", clear_on_submit=True):
                artikel = st.text_input("Artikelname (z.B. 1L Milch)")
                absenden = st.form_submit_button("Auf die Liste setzen")
                
                if absenden and artikel:
                    # Neuen Eintrag erstellen
                    new_entry = pd.DataFrame([{"Besteller": user, "Artikel": artikel, "Status": "Offen"}])
                    # In den Session State schreiben
                    st.session_state.einkaufsliste = pd.concat([st.session_state.einkaufsliste, new_entry], ignore_index=True)
                    st.success(f"'{artikel}' wurde gespeichert!")
                    st.rerun()

        with tab2:
            st.subheader("Deine aktuellen Einträge")
            # Wir holen nur die Daten des aktuellen Nutzers
            df = st.session_state.einkaufsliste
            meine_daten = df[df["Besteller"] == user]
            
            if meine_daten.empty:
                st.info("Du hast noch keine Artikel hinzugefügt.")
            else:
                for index, row in meine_daten.iterrows():
                    # Wir zeigen nur Löschen-Buttons für Sachen, die noch "Offen" sind
                    if row["Status"] == "Offen":
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"⏳ {row['Artikel']}")
                        if c2.button("Löschen 🗑️", key=f"del_{index}"):
                            # Zeile aus dem DataFrame entfernen
                            st.session_state.einkaufsliste = st.session_state.einkaufsliste.drop(index)
                            st.rerun()
                    else:
                        st.write(f"✅ {row['Artikel']} (Bereits erledigt)")

else:
    if pin != "":
        st.sidebar.error("Falscher PIN")
    st.info("Bitte wähle links deinen Namen und gib deinen PIN ein.")
