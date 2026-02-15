import streamlit as st

# --- VERBINDUNG ---
# Streamlit sucht automatisch nach [connections.tidb] in deinen Secrets
conn = st.connection("tidb", type="sql")

st.title("🏘️ Live-Sync Nachbar-App")

# Tabelle erstellen, falls sie noch nicht existiert
with conn.session as s:
    s.execute("CREATE TABLE IF NOT EXISTS einkaufsliste (id INT AUTO_INCREMENT PRIMARY KEY, besteller VARCHAR(255), artikel VARCHAR(255), status VARCHAR(50));")
    s.commit()

# --- LOGIN ---
user = st.sidebar.selectbox("Wer bist du?", ["Nachbar A", "Nachbar B", "Einkäufer"])
pin = st.sidebar.text_input("PIN", type="password")

if pin: # Hier könntest du deine PIN-Prüfung wieder einbauen
    # EINGABE
    if user != "Einkäufer":
        neuer = st.text_input("Artikel + Enter")
        if neuer:
            with conn.session as s:
                s.execute("INSERT INTO einkaufsliste (besteller, artikel, status) VALUES (:b, :a, :s);", 
                          {"b": user, "a": neuer, "s": "Offen"})
                s.commit()
            st.rerun()

    # ANZEIGE
    df = conn.query("SELECT * FROM einkaufsliste WHERE status = 'Offen';")
    st.dataframe(df)
