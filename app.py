import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- VERBINDUNG ZUM GOOGLE SHEET ---
# Wir sagen der App explizit, dass sie den öffentlichen Link nutzen soll
conn = st.connection("gsheets", type=GSheetsConnection)

# --- PASSWÖRTER (PINs) ---
PASSWORDS = {"Nachbar A": "1111", "Nachbar B": "2222", "Nachbar C": "3333", "Einkäufer": "0000"}

st.title("🏘️ Nachbarn-Einkauf")

# LOGIN
user = st.sidebar.selectbox("Wer bist du?", ["Bitte wählen"] + list(PASSWORDS.keys()))
pin = st.sidebar.text_input("PIN:", type="password")

if user != "Bitte wählen" and pin == PASSWORDS[user]:
    # Daten laden
    conn.read(worksheet="Einkaufsliste", ttl=0) # ttl=0 erzwingt jedes Mal frische Daten
    
    if user == "Einkäufer":
        st.header("🛒 Einkaufsliste (Alle)")
        if not df.empty:
            # Sortieren für den Einkäufer
            df_display = df.sort_values(by="Artikel")
            for index, row in df_display.iterrows():
                col1, col2 = st.columns([3, 1])
                status = "✅" if row["Status"] == "Erledigt" else "⏳"
                col1.write(f"{status} **{row['Artikel']}** ({row['Besteller']})")
                if row["Status"] == "Offen":
                    if col2.button("Erledigt", key=index):
                        df.at[index, "Status"] = "Erledigt"
                        conn.update(data=df, worksheet="Einkaufsliste")
                        st.rerun()
        else:
            st.info("Liste ist leer.")
            
    else:
        st.header(f"Deine Liste ({user})")
        # Zeige nur eigene Artikel
        meine_sachen = df[df["Besteller"] == user] if not df.empty else pd.DataFrame()
        
        for _, row in meine_sachen.iterrows():
            st.write(f"- {row['Artikel']} [{'Bereit' if row['Status'] == 'Offen' else 'Eingekauft'}]")
            
        new_item = st.text_input("Neuer Artikel:")
        if st.button("Hinzufügen"):
            new_data = pd.DataFrame([{"Besteller": user, "Artikel": new_item, "Status": "Offen"}])
            updated_df = pd.concat([df, new_data], ignore_index=True)
            conn.update(data=updated_df, worksheet="Einkaufsliste")
            st.success("Gespeichert!")
            st.rerun()

elif pin != "":
    st.sidebar.error("Falscher PIN")
