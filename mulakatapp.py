import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time
import plotly.graph_objects as go
from fpdf import FPDF
import os
import requests

# --- Sayfa Ayarları ---
st.set_page_config(page_title="AI Mülakat Simülasyonu", layout="wide")
st.title("🤖 AI Mülakat Simülasyonu (Final + PDF Rapor)")

# --- 1. FONKSİYONLAR: Font İndirme ve PDF Oluşturma ---
def check_and_download_fonts():
    # Türkçe karakter sorunu yaşamamak için Roboto fontunu indiriyoruz
    fonts = {
        "Roboto-Regular.ttf": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
        "Roboto-Bold.ttf": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    }
    for font_name, url in fonts.items():
        if not os.path.exists(font_name):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(font_name, 'wb') as f:
                        f.write(response.content)
            except: pass

def create_pdf_report(data):
    # Fontları kontrol et
    check_and_download_fonts()
    
    class PDF(FPDF):
        def header(self):
            # Font Tanımlama
            if os.path.exists('Roboto-Bold.ttf'):
                self.add_font('Roboto', 'B', 'Roboto-Bold.ttf', uni=True)
                self.add_font('Roboto', '', 'Roboto-Regular.ttf', uni=True)
                self.set_font('Roboto', 'B', 20)
            else:
                self.set_font('Arial', 'B', 20) # Yedek
            
            self.cell(0, 10, 'AI MULAKAT SONUC RAPORU', 0, 1, 'C')
            self.ln(10)

        def chapter_title(self, title):
            self.set_font('Roboto', 'B', 14)
            self.set_fill_color(230, 230, 230)
            self.cell(0, 10, title, 0, 1, 'L', fill=True)
            self.ln(4)

        def chapter_body(self, body):
            self.set_font('Roboto', '', 11)
            self.multi_cell(0, 6, body)
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    
    # 1. Genel Puan ve Karar
    pdf.set_font('Roboto', 'B', 16)
    pdf.cell(0, 10, f"GENEL PUAN: {data['score']}/100", 0, 1, 'C')
    pdf.set_text_color(0, 100, 0) if "Olumlu" in data['decision'] else pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 10, f"KARAR: {data['decision']}", 0, 1, 'C')
    pdf.set_text_color(0, 0, 0) # Rengi sıfırla
    pdf.ln(10)
    
    # 2. Yetkinlik Tablosu
    pdf.chapter_title("YETKINLIK PUANLARI")
    pdf.set_font('Roboto', '', 12)
    for cat, val in zip(data['categories'], data['values']):
        pdf.cell(100, 8, f"- {cat}", 0, 0)
        pdf.set_font('Roboto', 'B', 12)
        pdf.cell(0, 8, f"{val}/100", 0, 1)
        pdf.set_font('Roboto', '', 12)
    pdf.ln(10)
    
    # 3. Yorumlar
    pdf.chapter_title("YAPAY ZEKA DEGERLENDIRMESI")
    # Emoji temizliği (PDF emojileri sevmez)
    clean_text = data['text'].encode('latin-1', 'ignore').decode('latin-1') 
    # Veya basitçe emojileri görmezden gelmek için safe string kullanalım
    pdf.chapter_body(data['text'])
    
    pdf.chapter_title("ONERILER")
    pdf.chapter_body("Bu rapor Yapay Zeka tarafindan otomatik olusturulmustur. Lutfen eksik oldugunuz alanlarda pratik yapmaya devam edin.")
    
    return pdf.output(dest='S').encode('latin-1') # Streamlit için binary

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    api_key = st.text_input("Google API Key", type="password")
    
    # Model Seçimi (Filtreli)
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

# --- Hafıza ---
if "messages" not in st.session_state: st.session_state.messages = [] 
if "chat_session" not in st.session_state: st.session_state.chat_session = None 
if "finish_requested" not in st.session_state: st.session_state.finish_requested = False
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
        st.session_state.report_data = None
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

# --- Sohbet Akışı ---
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

# --- Raporlama ---
if st.session_state.finish_requested and st.session_state.chat_session:
    with st.spinner("Analiz ve PDF hazırlanıyor..."):
        try:
            report_prompt = """
