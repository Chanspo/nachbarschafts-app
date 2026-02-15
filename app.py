import streamlit as st

# --- KONFIGURATION (Das sind eure Zugangsdaten) ---
# In einem echten Szenario würden wir diese in eine Datenbank auslagern
PASSWORDS = {
    "Nachbar A": "1111",
    "Nachbar B": "2222",
    "Nachbar C": "3333",
    "Einkäufer": "0000" # Der Master-PIN
}

st.title("🏘️ Nachbarschafts-Einkaufshilfe")

# --- LOGIN BEREICH ---
user = st.sidebar.selectbox("Wer bist du?", ["Bitte wählen"] + list(PASSWORDS.keys()))
pin = st.sidebar.text_input("Dein 4-stelliger PIN:", type="password")

if user != "Bitte wählen" and pin == PASSWORDS[user]:
    st.sidebar.success(self_id := f"Eingeloggt als {user}")
    
    # --- WEICHE: EINKÄUFER VS NACHBAR ---
    if user == "Einkäufer":
        st.header("🛒 Master-Liste für den Einkauf")
        st.info("Hier sieht nur der Einkäufer alle Artikel, sortiert nach Produkt.")
        # Hier kommt später die Logik für die Gesamtliste hin
        
    else:
        st.header(f"Deine Liste ({user})")
        item = st.text_input("Was brauchst du?")
        if st.button("Hinzufügen"):
            st.success(f"'{item}' wurde gespeichert (Nur für dich und den Einkäufer sichtbar).")
            # Hier kommt später die Speicherung ins Google Sheet hin

elif pin != "":
    st.sidebar.error("Falscher PIN!")
else:
    st.info("Bitte wähle deinen Namen und gib deinen PIN in der Seitenleiste ein.")
