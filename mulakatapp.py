import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time
import plotly.graph_objects as go # Grafik kütüphanesi

# --- Sayfa Ayarları ---
st.set_page_config(page_title="AI Mülakat Simülasyonu", layout="wide")
st.title("🤖 AI Mülakat Simülasyonu (Final + Grafikli)")

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
            
            st.session_state.messages = [{"role": "assistant", "content": response.text}]
            st.session_state.finish_requested = False 
            st.success(f"✅ Başladı! Model: {selected_model}")
            
        except Exception as e:
            st.error(f"Hata: {e}")

# --- Raporlama ve Görselleştirme ---
if st.session_state.finish_requested and st.session_state.chat_session:
    with st.spinner("Grafikler oluşturuluyor..."):
        try:
            report_prompt = """
            MÜLAKAT BİTTİ. Adayı analiz et.
            
            FORMAT (Lütfen sayıları net ver):
            SKOR: (0-100 arası sayı)
            KARAR: (Olumlu / Olumsuz)
            
            -- PUAN DETAYLARI --
            TEKNİK: (0-100)
            İLETİŞİM: (0-100)
            PROBLEM_ÇÖZME: (0-100)
            TEORİK_BİLGİ: (0-100)
            POTANSİYEL: (0-100)
            
            -- SÖZEL RAPOR --
            GÜÇLÜ: (Maddeler)
            ZAYIF: (Maddeler)
            TAVSİYE: (Kısa tavsiye)
            """
            response = st.session_state.chat_session.send_message(report_prompt)
            full_text = response.text
            
            # Parsing (Veriyi Ayıklama)
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

            st.session_state.finish_requested = False
            
            # --- GÖRSELLEŞTİRME EKRANI ---
            st.markdown("---")
            st.header("📊 Mülakat Sonuç Karnesi")
            
            # 1. Metrikler
            col1, col2 = st.columns(2)
            col1.metric("Genel Puan", f"{score}/100")
            if "Olumlu" in decision: col2.success(f"Karar: {decision}")
            else: col2.error(f"Karar: {decision}")
                
            st.progress(score)
            
            # 2. Radar Grafiği ve Yorum
            c1, c2 = st.columns([1, 1])
            with c1:
                st.subheader("Yetkinlik Radarı")
                # Radar Grafiği 

[Image of radar chart competency visualization]

                fig = go.Figure(data=go.Scatterpolar(
                    r=values, 
                    theta=categories, 
                    fill='toself', 
                    name='Aday'
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
                    showlegend=False,
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.subheader("Yapay Zeka Yorumu")
                st.info(verbal_report)
                
            st.session_state.messages.append({"role": "assistant", "content": f"**Rapor:** Puan {score} - {decision}"})

        except Exception as e:
            st.error(f"Grafik Hatası: {e}")

# --- Ekran ---
if st.session_state.chat_session:
    for message in st.session_state.messages:
        role = "user" if message["role"] == "user" else "assistant"
        if role == "assistant" and "SKOR:" in message["content"]: continue
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
