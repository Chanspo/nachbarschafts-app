import streamlit as st
import pandas as pd

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Nachbar-App Live", layout="centered", page_icon="🏘️")

# --- DATENBANK-VERBINDUNG (Robust-Modus) ---
try:
    # Wir ziehen die Daten direkt aus der Sektion [connections.tidb]
    creds = st.secrets["connections"]["tidb"]
    
    # Wir bauen den Connection-String manuell, um Fehler bei Feldnamen zu vermeiden
    # Format: mysql+pymysql://user:password@host:port/database
    db_url = f"mysql+pymysql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    
    # Verbindung herstellen
    conn = st.connection("tidb", type="sql", url=db_url)
    
except Exception as e:
    st.error(f"❌ Verbindung fehlgeschlagen. Bitte Secrets prüfen!")
    st.info(f"Details: {e}")
    st.stop()

# --- TABELLE INITIALISIEREN ---
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
        # Wir laden die Daten ohne Cache (ttl=0), damit sie immer aktuell sind
        df = conn.query("SELECT * FROM einkaufsliste WHERE status = 'Offen' ORDER BY id DESC;", ttl=0)
        
        if df is None or df.empty:
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
            if erledigt_df is not None:
                st.dataframe(erledigt_df)

    # --- NACHBAR-ANSICHT ---
    else:
        tab1, tab2 = st.tabs(["➕ Neuer Wunsch", "📋 Meine Liste"])

        with tab1:
            st.subheader("Was soll mitgebracht werden?")
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
            meine_daten = conn.query(f"SELECT * FROM einkaufsliste WHERE besteller = '{user}' AND status = 'Offen' ORDER BY id DESC;", ttl=0)
            
            if meine_daten is None or meine_daten.empty:
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
    st.info("Bitte wähle deinen Namen und gib deinen PIN ein.")
