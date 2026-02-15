import streamlit as st
import pandas as pd
from sqlalchemy import text

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Nachbar-App Live", layout="centered", page_icon="🏘️")

# --- DATENBANK-VERBINDUNG ---
try:
    creds = st.secrets["connections"]["tidb"]
    
    # Der Verbindungsstring bleibt gleich
    db_url = f"mysql+pymysql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    
    # Wir probieren die sicherste SSL-Einstellung für Streamlit Cloud
    connect_args = {
        "ssl": {
            "reject_authorized": "false" # Erlaubt die Verbindung, auch wenn das Zertifikat-Bundle leicht abweicht
        }
    }
    
    conn = st.connection(
        "tidb", 
        type="sql", 
        url=db_url,
        connect_args=connect_args
    )
    
except Exception as e:
    st.error("❌ Verbindung fehlgeschlagen!")
    st.info(f"Details: {e}")
    st.stop()

# --- TABELLE INITIALISIEREN ---
try:
    with conn.session as s:
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS einkaufsliste (
                id INT AUTO_INCREMENT PRIMARY KEY,
                besteller VARCHAR(255),
                artikel VARCHAR(255),
                status VARCHAR(50)
            );
        """))
        s.commit()
except Exception as e:
    st.error("Fehler beim Erstellen der Tabelle. Prüfe deine TiDB-Rechte.")
    st.stop()

# --- LOGIN-DATEN ---
USERS = {"Nachbar A": "1111", "Nachbar B": "2222", "Einkäufer": "0000"}

# --- UI ---
st.title("🏘️ Nachbarschaftshilfe Live")

user = st.sidebar.selectbox("Wer bist du?", ["Bitte wählen"] + list(USERS.keys()))
pin = st.sidebar.text_input("PIN", type="password")

if user != "Bitte wählen" and pin == USERS[user]:
    st.sidebar.success(f"Eingeloggt als {user}")

    if user == "Einkäufer":
        st.header("🛒 Einkaufsliste")
        df = conn.query("SELECT * FROM einkaufsliste WHERE status = 'Offen' ORDER BY id DESC;", ttl=0)
        
        if df is None or df.empty:
            st.success("Keine offenen Wünsche!")
        else:
            for index, row in df.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['artikel']}** ({row['besteller']})")
                if col2.button("Erledigt ✅", key=f"done_{row['id']}"):
                    with conn.session as s:
                        s.execute(text("UPDATE einkaufsliste SET status = 'Erledigt' WHERE id = :id"), {"id": row['id']})
                        s.commit()
                    st.rerun()
    else:
        tab1, tab2 = st.tabs(["➕ Neu", "📋 Meine Liste"])
        with tab1:
            neuer = st.text_input("Was fehlt? (Enter)", key="new_item")
            if neuer:
                with conn.session as s:
                    s.execute(text("INSERT INTO einkaufsliste (besteller, artikel, status) VALUES (:b, :a, :s)"),
                              {"b": user, "a": neuer, "s": "Offen"})
                    s.commit()
                st.rerun()
        with tab2:
            meine = conn.query("SELECT * FROM einkaufsliste WHERE besteller = :u AND status = 'Offen';", 
                               params={"u": user}, ttl=0)
            if meine is not None and not meine.empty:
                for index, row in meine.iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"⏳ {row['artikel']}")
                    if c2.button("Löschen", key=f"del_{row['id']}"):
                        with conn.session as s:
                            s.execute(text("DELETE FROM einkaufsliste WHERE id = :id"), {"id": row['id']})
                            s.commit()
                        st.rerun()
else:
    st.info("Bitte links anmelden.")
