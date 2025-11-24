import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder # Ses Kayıt
import speech_recognition as sr # Sesi Yazıya Çevirme
from gTTS import gTTS # Yazıyı Sese Çevirme
import tempfile # Geçici dosya işlemleri
import os

st.title("🎙️ Sesli Asistan Test Odası")
st.info("Bu sayfa ana projeden bağımsızdır. Sadece ses özelliklerini test eder.")

# API Key (Test için tekrar girmemiz gerek)
api_key = st.text_input("Google API Key", type="password")

# --- FONKSİYONLAR ---

# 1. Sesi Yazıya Çevir (Speech-to-Text)
def ses_to_text(audio_bytes):
    r = sr.Recognizer()
    # Ses verisini geçici dosyaya kaydet
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
        tmp_audio.write(audio_bytes)
        tmp_audio_path = tmp_audio.name
    
    try:
        with sr.AudioFile(tmp_audio_path) as source:
            audio_data = r.record(source)
            # Google'ın ücretsiz servisini kullan (Türkçe destekli)
            text = r.recognize_google(audio_data, language="tr-TR")
            return text
    except sr.UnknownValueError:
        return "Ses anlaşılamadı."
    except sr.RequestError:
        return "Google servisine ulaşılamadı."
    except Exception as e:
        return f"Hata: {e}"
    finally:
        os.remove(tmp_audio_path) # Temizlik

# 2. Yazıyı Sese Çevir (Text-to-Speech)
def text_to_ses(text):
    try:
        tts = gTTS(text=text, lang='tr')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
            tts.save(tmp_mp3.name)
            return tmp_mp3.name
    except Exception as e:
        st.error(f"Ses oluşturma hatası: {e}")
        return None

# --- ANA AKIŞ ---

if api_key:
    genai.configure(api_key=api_key)
    
    st.subheader("1. Adım: Mikrofonla Konuş")
    # Mikrofon Butonu
    audio_bytes = audio_recorder(
        text="Konuşmak için butona tıkla",
        recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_name="microphone",
        icon_size="2x",
    )

    if audio_bytes:
        # 1. Sesi Oynat (Kontrol)
        st.audio(audio_bytes, format="audio/wav")
        
        # 2. Yazıya Çevir
        with st.spinner("Sesin yazıya çevriliyor..."):
            user_text = ses_to_text(audio_bytes)
        
        st.success(f"🗣️ Senin Söylediğin: **{user_text}**")
        
        # 3. Gemini'ye Gönder (Eğer anlamlı bir cümle ise)
        if "Hata" not in user_text and "anlaşılamadı" not in user_text:
            with st.spinner("Yapay zeka düşünüyor..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(user_text)
                ai_response = response.text
            
            st.info(f"🤖 AI Cevabı: **{ai_response}**")
            
            # 4. Cevabı Seslendir
            with st.spinner("Cevap seslendiriliyor..."):
                audio_file_path = text_to_ses(ai_response)
                if audio_file_path:
                    st.audio(audio_file_path, format="audio/mp3")
                    os.remove(audio_file_path) # Temizlik
