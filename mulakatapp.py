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
    api_key = st.text_input("Google API Key", type="password")
    
    # Model Seçimi (FİLTRELİ)
    model_options = ["Önce API Key Girin"]
    if api_key:
        try:
            genai.configure(api_key=api_key)
            options = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if "exp" not in m.name and "2.5" not in m.name: 
                        options.append(m.name)
            if options: model_options = options
        except: st.error("API Key geçersiz.")

    index = 0
    for i, name in enumerate(model_options):
        if "1.5" in name and "flash" in name: index = i; break
    selected_model = st.selectbox("Model Seçimi", model_options, index=index)

    with st.form("main_form"):
        st.info("Mülakat Detayları")
        job_description = st.text_area("İş İlanı (JD)", height=100)
        cv_file = st.file_uploader("CV (Zorunlu)", type="pdf")
        portfolio_files = st.file_uploader("Ek Dosyalar", type="pdf", accept_multiple_files=True)
        start_interview = st.form_submit_button("Mülakatı Başlat")
    
    st.markdown("---")
    # Butona basınca sadece tetikleyiciyi çalıştırıyoruz
    if st.session_state.get('chat_session'):
        if st.button("🏁 Mülakatı Bitir ve Raporla", type="primary"):
            st.session_state['finish_requested'] = True

# --- Fonksiyonlar ---
def get_pdf_text(pdf_file):
    text = ""
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages: text += page.extract_text()
    except: pass
    return text

# --- Hafıza Yönetimi ---
if "messages" not in st.session_state: st.session_state.messages = [] 
if "chat_session" not in st.session_state: st.session_state.chat_session = None 
if "finish_requested" not in st.session_state: st.session_state.finish_requested = False
# Rapor verilerini hafızada tutmak için yeni değişken:
if "report_data" not in st.session_state: st.session_state.report_data = None 

# --- Güvenlik ---
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# --- Mülakat Başlatma ---
if start_interview:
    if not api_key or not cv_file:
        st.error("Eksik bilgi.")
    else:
        st.session_state.report_data = None # Yeni mülakatta eski raporu sil
        genai.configure(api_key=api_key)
        cv_text = get_pdf_text(cv_file)
        portfolio_text = ""
        if portfolio_files:
            for file in portfolio_files:
                portfolio_text += f"\n--- DOSYA: {file.name} ---\n{get_pdf_text(file)}\n"
        try:
            system_prompt = f"""
            GÖREVİN: Verilen İŞ İLANI ({job_description}) için en uygun İşe Alım Yöneticisi ol.
            ADAY CV: {cv_text}
            EK DOSYALAR: {portfolio_text}
            STRATEJİ:
            1. Role gir.
            2. Zorlayıcı sorular sor.
            3. Senaryo sor.
            Kısa ve net ol. Tek soru sor.
            """
            model = genai.GenerativeModel(model_name=selected_model, safety_settings=safety_settings)
            chat = model.start_chat(history=[])
            st.session_state.chat_session = chat
            chat.send_message(system_prompt)
            response = chat.send_message("Mülakatı başlat.")
            st.session_state.messages = [{"role": "assistant", "content": response.text}]
            st.success("Başladı!")
        except Exception as e: st.error(f"Hata: {e}")

# --- Sohbet Akışı (ÖNCE BURASI ÇALIŞSIN) ---
if st.session_state.chat_session:
    for message in st.session_state.messages:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.write(message["content"])

    if user_input := st.chat_input("Cevabın..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.write(user_input)
        with st.spinner("..."):
            try:
                time.sleep(1)
                response = st.session_state.chat_session.send_message(user_input)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                with st.chat_message("assistant"): st.write(response.text)
            except: pass

# --- Raporlama Mantığı (EN SONA ALDIK) ---
if st.session_state.finish_requested and st.session_state.chat_session:
    with st.spinner("Grafikler hazırlanıyor..."):
        try:
            report_prompt = """
            MÜLAKAT BİTTİ. Detaylı analiz yap.
            FORMAT:
            SKOR: (0-100)
            KARAR: (Olumlu / Olumsuz)
            -- PUAN DETAYLARI --
            TEKNİK: (0-100)
            İLETİŞİM: (0-100)
            PROBLEM_ÇÖZME: (0-100)
            TEORİK_BİLGİ: (0-100)
            POTANSİYEL: (0-100)
            -- SÖZEL RAPOR --
            (Kısa bir özet yaz)
            """
            response = st.session_state.chat_session.send_message(report_prompt)
            full_text = response.text
            
            # Veriyi Ayıkla
            try: score = int(full_text.split("SKOR:")[1].split("\n")[0].strip())
            except: score = 0
            try: decision = full_text.split("KARAR:")[1].split("\n")[0].strip()
            except: decision = "Belirsiz"
            
            categories = ["TEKNİK", "İLETİŞİM", "PROBLEM_ÇÖZME", "TEORİK_BİLGİ", "POTANSİYEL"]
            values = []
            for cat in categories:
                try: val = int(full_text.split(f"{cat}:")[1].split("\n")[0].strip())
                except: val = 50
                values.append(val)
            
            try: verbal_report = full_text.split("-- SÖZEL RAPOR --")[1]
            except: verbal_report = full_text

            # VERİYİ HAFIZAYA KAYDET (Kalıcı Olsun)
            st.session_state.report_data = {
                "score": score,
                "decision": decision,
                "categories": categories,
                "values": values,
                "text": verbal_report
            }
            st.session_state.finish_requested = False # İsteği kapat
            st.rerun() # Sayfayı yenile ki aşağıda gözüksün

        except Exception as e: st.error(f"Hata: {e}")

# --- Raporu Ekrana Bas (EN ALTTA) ---
if st.session_state.report_data:
    data = st.session_state.report_data
    
    st.markdown("---")
    st.header("📊 Mülakat Sonuç Karnesi")
    
    c1, c2 = st.columns(2)
    c1.metric("Genel Puan", f"{data['score']}/100")
    if "Olumlu" in data['decision']: c2.success(f"Karar: {data['decision']}")
    else: c2.error(f"Karar: {data['decision']}")
    
    st.progress(data['score'])
    
    col_chart, col_text = st.columns([1, 1])
    with col_chart:
        # Radar Grafiği         fig = go.Figure(data=go.Scatterpolar(
            r=data['values'], theta=data['categories'], fill='toself', name='Aday'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_text:
        st.info(data['text'])
