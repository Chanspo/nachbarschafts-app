import streamlit as st

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Nachbar-App Live", layout="centered", page_icon="🏘️")

# --- DATENBANK-VERBINDUNG ---
# Streamlit nutzt die [connections.tidb] Sektion aus deinen Secrets
try:
    conn = st.connection("tidb", type="sql")
except Exception as e:
    st.error(f"Verbindung zur Datenbank fehlgeschlagen. Bitte Secrets prüfen. Fehler: {e}")
    st.stop()

# --- TABELLE INITIALISIEREN ---
# Dies erstellt die Tabelle in der TiDB Cloud, falls sie noch nicht existiert
with conn.session as s:
    s.execute("""
        CREATE TABLE IF NOT EXISTS einkaufsliste (
            id INT AUTO_INCREMENT PRIMARY KEY,
            besteller VARCHAR(255),
            artikel VARCHAR(255),
            status VARCHAR(50)
        );
    """)
    s.commit()

# --- BENUTZER-DATEN ---
USERS = {
    "Nachbar A": "1111",
    "Nachbar B": "2222",
    "Einkäufer": "0000"
}

# --- UI & LOGIN ---
st.title("🏘️ Live-Sync Einkaufsliste")

st.sidebar.header("Anmeldung")
user = st.sidebar.selectbox("Wer bist du?", ["Bitte wählen"] + list(USERS.keys()))
pin = st.sidebar.text_input("PIN", type="password")

if user != "Bitte wählen" and pin == USERS[user]:
    st.sidebar.success(f"Eingeloggt als {user}")

    # --- EINKÄUFER-ANSICHT ---
    if user == "Einkäufer":
        st.header("🛒 Alle offenen Wünsche")
        # Daten live aus TiDB laden
        df = conn.query("SELECT * FROM einkaufsliste WHERE status = 'Offen' ORDER BY id DESC;", ttl=0)
        
        if df.empty:
            st.success("Alles erledigt! Keine offenen Posten.")
        else:
            for index, row in df.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['artikel']}** (für {row['besteller']})")
                if col2.button("Erledigt ✅", key=f"done_{row['id']}"):
                    with conn.session as s:
                        s.execute("UPDATE einkaufsliste SET status = 'Erledigt' WHERE id = :id", {"id": row['id']})
                        s.commit()
                    st.rerun()
        
        with st.expander("Historie ansehen"):
            erledigt_df = conn.query("SELECT * FROM einkaufsliste WHERE status = 'Erledigt' LIMIT 20;", ttl=0)
            st.dataframe(erledigt_df)

    # --- NACHBAR-ANSICHT ---
    else:
        tab1, tab2 = st.tabs(["➕ Neuer Wunsch", "📋 Meine Liste"])

        with tab1:
            st.subheader("Was soll mitgebracht werden?")
            # Automatisches Speichern bei Enter
            neuer_artikel = st.text_input("Artikel eingeben & Enter drücken", key="new_item")
            if neuer_artikel:
                with conn.session as s:
                    s.execute(
                        "INSERT INTO einkaufsliste (besteller, artikel, status) VALUES (:b, :a, :s);",
                        {"b": user, "a": neuer_artikel, "s": "Offen"}
                    )
                    s.commit()
                st.success(f"'{neuer_artikel}' wurde gespeichert!")
                st.rerun()

        with tab2:
            st.subheader("Deine aktuellen Einträge")
            # Nur eigene Einträge laden
            meine_daten = conn.query(f"SELECT * FROM einkaufsliste WHERE besteller = '{user}' AND status = 'Offen' ORDER BY id DESC;", ttl=0)
            
            if meine_daten.empty:
                st.info("Du hast momentan keine offenen Wünsche.")
            else:
                for index, row in meine_daten.iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"⏳ {row['artikel']}")
                    if c2.button("Löschen 🗑️", key=f"del_{row['id']}"):
                        with conn.session as s:
                            s.execute("DELETE FROM einkaufsliste WHERE id = :id", {"id": row['id']})
                            s.commit()
                        st.rerun()
else:
    if pin != "":
        st.sidebar.error("Falscher PIN")
    st.info("Bitte wähle deinen Namen und gib deinen PIN ein, um die Live-Liste zu sehen.")
