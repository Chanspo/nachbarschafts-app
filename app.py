import streamlit as st
import pandas as pd

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Nachbar-App", layout="centered")

# --- DATEN-SPEICHER INITIALISIEREN ---
# Wir nutzen den st.session_state. 
# Hinweis: In der Free-Tier Cloud bleibt dieser Speicher aktiv, solange die App läuft.
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

    # Reiter für bessere Übersicht
    tab1, tab2 = st.tabs(["🛒 Aktuelle Liste", "➕ Neuen Wunsch hinzufügen"])

    with tab2:
        if user != "Einkäufer":
            st.header("Was wird benötigt?")
            with st.form("wunsch_form", clear_on_submit=True):
                artikel = st.text_input("Artikelname")
                absenden = st.form_submit_button("Auf die Liste setzen")
                
                if absenden and artikel:
                    new_entry = pd.DataFrame([{"Besteller": user, "Artikel": artikel, "Status": "Offen"}])
                    st.session_state.einkaufsliste = pd.concat([st.session_state.einkaufsliste, new_entry], ignore_index=True)
                    st.success(f"{artikel} wurde hinzugefügt!")
        else:
            st.info("Einkäufer können nur die Liste einsehen und Dinge abhaken.")

    with tab1:
        st.header("Einkaufsliste")
        df = st.session_state.einkaufsliste
        
        if df.empty:
            st.write("Die Liste ist aktuell leer.")
        else:
            # Nur offene Posten anzeigen
            offene_posten = df[df["Status"] == "Offen"]
            
            if offene_posten.empty:
                st.success("Alles erledigt!")
            else:
                for index, row in offene_posten.iterrows():
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{row['Artikel']}** (für {row['Besteller']})")
                    
                    # Erledigt-Button
                    if col2.button("Erledigt ✅", key=f"btn_{index}"):
                        st.session_state.einkaufsliste.at[index, "Status"] = "Erledigt"
                        st.rerun()

            # Historie (optional einblendbar)
            with st.expander("Abgeschlossene Einkäufe anzeigen"):
                st.dataframe(df[df["Status"] == "Erledigt"])

else:
    if pin != "":
        st.sidebar.error("Falscher PIN")
    st.info("Bitte wähle links deinen Namen und gib deinen PIN ein, um die Liste zu sehen.")
