import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time
import plotly.graph_objects as go

# --- Sayfa Ayarları ---
st.set_page_config(page_title="AI Mülakat Simülasyonu", layout="wide")
st.title("🤖 AI Mülakat Simülasyonu (Stabil Versiyon)")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    
    # 1. API Key
    api_key = st.text_input("Google API Key", type="password")
    
    # 2. Model Seçimi (FİLTRELİ)
    model_options = ["Önce API Key Girin"]
    if api_key:
        try:
            genai.configure(api_key=api_key)
            options = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # KRİTİK FİLTRE: Deneysel (exp) ve 2.5 modellerini LİSTEYE ALMA
                    if "exp" not in m.name and "2.5" not in m.name: 
                        options.append(m.name)
            if options:
                model_options = options
        except:
            st.error("API Key geçersiz.")

    # Otomatik olarak 1.5 Flash'ı seçtirmeye çalış
    index = 0
    for i, name in enumerate(model_options):
        if "1.5" in name and "flash" in name:
            index = i
            break
            
    selected_model = st.selectbox("Model Seçimi (Sadece Ücretsizler)", model_options, index=index)

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
    return text

# --- Hafıza ---
if "messages" not in st.session_state: st.session_state.messages = [] 
if "chat_session" not in st.session_state: st.session_state.chat_session = None 
if "finish_requested" not in st.session_state: st.session_state.finish_requested = False

# --- GÜVENLİK AYARLARI ---
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# --- Mülakatı Başlatma ---
if start_interview:
    if not api_key or not cv_file or selected_model == "Önce API Key Girin":
        st.error("Lütfen eksik bilgileri doldurun.")
    else:
        genai.configure(api_key=api_key)
        cv_text = get_pdf_text(cv_file)
        portfolio_text = ""
        if portfolio_files:
            for file in portfolio_files:
                portfolio_text += f"\n--- DOSYA: {file.name} ---\n{get_pdf_text(file)}\n"
                
        try:
            # SİSTEM PROMPTU
            system_prompt = f"""
            GÖREVİN:
            Sen, aşağıda verilen İŞ İLANI için en uygun "İşe Alım Yöneticisi" kimliğine bürüneceksin.
            
            VERİLER:
            - İŞ İLANI (JD): {job_description}
            - ADAY CV: {cv_text}
            - ADAY DOSYALARI: {portfolio_text}
            
            MÜLAKAT STRATEJİN:
            1. ROLÜ BENİMSE: İlana göre uygun role gir.
            2. ZORLA: Adayın deneyimlerini didik didik et.
            3. SENARYO SOR: Anlık kriz durumları sor.
            
            KURALLAR:
            - Tek seferde SADECE BİR soru sor.
            - Profesyonel ve sorgulayıcı ol.
            
            Rolünü belirterek mülakatı başlat.
            """
            
            model = genai.GenerativeModel(
                model_name=selected_model,
                safety_settings=safety_settings 
            )
            chat = model.start_chat(history=[])
            st.session_state.chat_session = chat
            
            chat.send_message(system_prompt)
            response = chat.send_message("Mülakatı başlat.")
            
            st.
