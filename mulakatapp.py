import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time

# --- Sayfa Ayarları ---
st.set_page_config(page_title="AI Mülakat Simülasyonu", layout="wide")
st.title("🤖 AI Mülakat Simülasyonu (Advanced Mode)")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    api_key = st.text_input("Google API Key", type="password")
    
    # Model Seçimi
    model_options = ["Önce API Key Girin"]
    if api_key:
        try:
            genai.configure(api_key=api_key)
            options = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    options.append(m.name)
            if options: model_options = options
        except: pass

    index = 0
    for i, name in enumerate(model_options):
        if "flash" in name: index = i; break
    selected_model = st.selectbox("Model Seçimi", model_options, index=index)

    with st.form("main_form"):
        st.info("Mülakat Detayları")
        job_description = st.text_area("İş İlanı (JD)", height=100)
        cv_file = st.file_uploader("CV (Zorunlu)", type="pdf")
        portfolio_files = st.file_uploader("Ek Dosyalar", type="pdf", accept_multiple_files=True)
        start_interview = st.form_submit_button("Mülakatı Başlat")
    
    st.markdown("---")
    if st.session_state.get('chat_session'):
        if st.button("🏁 Mülakatı Bitir ve Puanla", type="primary"):
            st.session_state['finish_requested'] = True

# --- Fonksiyonlar ---
def get_pdf_text(pdf_file):
    text = ""
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages: text += page.extract_text()
    except: pass
    return text

if "messages" not in st.session_state: st.session_state.messages = [] 
if "chat_session" not in st.session_state: st.session_state.chat_session = None 
if "finish_requested" not in st.session_state: st.session_state.finish_requested = False

# --- Mülakatı Başlat ---
if start_interview:
    if not api_key or not cv_file:
        st.error("Eksik bilgi.")
    else:
        genai.configure(api_key=api_key)
        cv_text = get_pdf_text(cv_file)
        portfolio_text = ""
        if portfolio_files:
            for file in portfolio_files:
                portfolio_text += f"\n--- DOSYA: {file.name} ---\n{get_pdf_text(file)}\n"
        
        try:
            # --- İŞTE SİHİR BURADA: GELİŞMİŞ SİSTEM PROMPTU ---
            system_prompt = f"""
            ROLÜN: Sen, detaylara takıntılı, "Senior" seviyesinde bir Teknik İşe Alım Yöneticisisin.
            
            VERİLER:
            - İŞ İLANI: {job_description}
            - CV: {cv_text}
            - PORTFOLYO: {portfolio_text}
            
            MÜLAKAT STRATEJİN (Bunu harfiyen uygula):
            1. AŞAMALI ZORLUK: İlk soru ısınma olsun. Aday doğru bildikçe, soruları "Nasıl?" ve "Neden?" diye derinleştirerek zorlaştır.
            2. DEDEKTİF MODU: Aday "Yaptım, ettim" gibi genel konuşursa KABUL ETME. Hemen "Hangi teknolojiyle?", "Hangi parametreleri kullandın?", "Alternatifleri neden eledin?" diye sor.
            3. STAR TEKNİĞİ: Adaydan her zaman Somut Olay (Situation) ve Sonuç (Result) iste. Teorik tanımları kabul etme.
            4. TUZAK KUR: Arada sırada "Bu işlemi X ile yaptığını söyledin ama Y kullansan daha iyi olmaz mıydı?" gibi (bazen hatalı önermelerle) adayın bilgisini ve özgüvenini sına.
            
            KURALLAR:
            - Asla uzun nutuklar atma. Soru sor ve sus.
            - Tek seferde SADECE BİR soru sor.
            - Adayın kopyala-yapıştır cevap verdiğini hissedersen "Bunu kendi cümlelerinle, yaşadığın bir örnekle anlat" de.
            
            Şimdi, profesyonel ama sorgulayıcı bir tonla kendini tanıt ve CV/Portfolyodaki en dikkat çekici (veya şüpheli) noktadan ilk sorunu sor.
            """
            
            model = genai.GenerativeModel(selected_model)
            chat = model.start_chat(history=[])
            st.session_state.chat_session = chat
            
            chat.send_message(system_prompt)
            response = chat.send_message("Mülakatı başlat.")
            
            st.session_state.messages = [{"role": "assistant", "content": response.text}]
            st.session_state.finish_requested = False
            st.success(f"✅ Zorlu Mod Aktif! Model: {selected_model}")
            
        except Exception as e:
            st.error(f"Hata: {e}")




# --- GÜNCELLENMİŞ GÖRSEL RAPORLAMA KISMI ---
if st.session_state.finish_requested and st.session_state.chat_session:
    with st.spinner("Yapay zeka verileri analiz edip grafikleri çiziyor..."):
        try:
            # 1. AI'dan YAPISAL VERİ İSTİYORUZ (JSON Formatına Yakın)
            report_prompt = """
            MÜLAKAT BİTTİ. Adayı analiz et ve aşağıdaki formatta rapor ver.
            
            ÖNEMLİ: Her satırın başına belirleyici etiket koy ki onları ayrıştırabileyim.
            
            FORMAT:
            SKOR: (0-100 arası sadece sayı)
            KARAR: (Olumlu / Olumsuz)
            
            -- PUAN DETAYLARI (0-100 arası puan ver) --
            TEKNİK: (Puan)
            İLETİŞİM: (Puan)
            PROBLEM_ÇÖZME: (Puan)
            TEORİK_BİLGİ: (Puan)
            POTANSİYEL: (Puan)
            
            -- SÖZEL RAPOR --
            GÜÇLÜ: (Maddeler halinde)
            ZAYIF: (Maddeler halinde)
            TAVSİYE: (Kısa tavsiye)
            """
            response = st.session_state.chat_session.send_message(report_prompt)
            full_text = response.text
            
            # 2. METNİ AYRIŞTIRMA (PARSING)
            # AI'ın verdiği metinden sayıları çekiyoruz
            try:
                score = int(full_text.split("SKOR:")[1].split("\n")[0].strip())
            except: score = 0
            
            try:
                decision = full_text.split("KARAR:")[1].split("\n")[0].strip()
            except: decision = "Belirsiz"

            # Detay Puanlarını Çekmeye Çalışalım
            categories = ["TEKNİK", "İLETİŞİM", "PROBLEM_ÇÖZME", "TEORİK_BİLGİ", "POTANSİYEL"]
            values = []
            for cat in categories:
                try:
                    val = int(full_text.split(f"{cat}:")[1].split("\n")[0].strip())
                except: val = 50 # Okuyamazsa ortalama ver
                values.append(val)
            
            # Sözlü Raporu Ayıklama
            try:
                verbal_report = full_text.split("-- SÖZEL RAPOR --")[1]
            except: verbal_report = full_text

            st.session_state.finish_requested = False # Döngüyü kır
            
            # --- 3. GÖRSELLEŞTİRME EKRANI (DASHBOARD) ---
            st.markdown("---")
            st.header("📊 Mülakat Sonuç Karnesi")
            
            # Üst Kısım: Büyük Puan ve Karar
            col1, col2, col3 = st.columns(3)
            col1.metric("Genel Başarı Puanı", f"{score}/100")
            
            if "Olumlu" in decision:
                col2.success(f"Karar: {decision}")
            else:
                col2.error(f"Karar: {decision}")
                
            # Progress Bar (Puan Çubuğu)
            st.progress(score)
            
            # Orta Kısım: Radar Grafiği ve Yorumlar
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.subheader("Yetkinlik Dağılımı")
                # Radar Grafiği Oluşturma
                fig = go.Figure(data=go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='Aday Profili'
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.subheader("📝 Yapay Zeka Yorumu")
                st.info(verbal_report)
                
            # Mesaja da ekle ki kaybolmasın
            st.session_state.messages.append({"role": "assistant", "content": f"**Rapor Oluşturuldu:**\nPuan: {score}\nKarar: {decision}"})

        except Exception as e:
            st.error(f"Grafik oluşturulurken hata: {e}")
            st.write(response.text) # Hata olursa düz metni bas
