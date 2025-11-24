import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time
import plotly.graph_objects as go

# --- Sayfa Ayarları ---
st.set_page_config(page_title="AI Mülakat Simülasyonu", layout="wide")
st.title("🤖 AI Mülakat Simülasyonu (Final Versiyon)")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    
    # 1. API Key
    api_key = st.text_input("Google API Key", type="password")
    
    # 2. Model Seçimi (FİLTRELİ - KOTA DOSTU)
    model_options = ["Önce API Key Girin"]
    if api_key:
        try:
            genai.configure(api_key=api_key)
            options = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # Deneysel (exp) ve 2.5 modellerini LİSTEYE ALMA
                    if "exp" not in m.name and "2.5" not in m.name: 
                        options.append(m.name)
            if options:
                model_options = options
        except:
            st.error("API Key geçersiz.")

    # Otomatik olarak 1.5 Flash'ı seç
    index = 0
    for i, name in enumerate(model_options):
        if "1.5" in name and "flash" in name:
            index = i
            break
            
    selected_model = st.selectbox("Model Seçimi", model_options, index=index)

    # 3. Form
    with st.form("main_form"):
        st.info("Mülakat Detayları")
        job_description = st.text_area("İş İlanı (JD)", height=100)
        cv_file = st.file_uploader("CV (Zorunlu)", type="pdf")
        portfolio_files = st.file_uploader("Ek Dosyalar", type="pdf", accept_multiple_files=True)
        
        start_interview = st.form_submit_button("Mülakatı Başlat")
    
    st.markdown("---")
    if st.session_state.get('chat_session'):
        if st.button("🏁 Mülakatı Bitir ve Raporla", type="primary"):
            st.session_state['finish_requested'] = True

# --- Fonksiyonlar ---
def get_pdf_text(pdf_file):
    text = ""
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text()
    except: pass
