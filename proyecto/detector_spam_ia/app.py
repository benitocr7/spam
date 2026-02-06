import streamlit as st
import joblib

modelo = joblib.load("modelo_spam.pkl")

st.set_page_config(page_title="Detector de Spam", page_icon="📩")

st.title("📩 Detector de Spam con IA")
st.write("Escribe un mensaje y la IA detectará si es SPAM o NO SPAM")

mensaje = st.text_area("✉️ Mensaje")

if st.button("Analizar"):
    if mensaje.strip() == "":
        st.warning("Escribe un mensaje")
    else:
        resultado = modelo.predict([mensaje])[0]

        if resultado == 1:
            st.error("🚫 SPAM detectado")
        else:
            st.success("✅ Mensaje normal (NO SPAM)")
