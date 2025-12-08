import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time
import plotly.graph_objects as go
from fpdf import FPDF
import os
import requests
import tempfile
import re

# --- Sayfa Ayarları ---
st.set_page_config(page_title="AI Mülakat Simülasyonu", layout="wide")
st.title("🤖 AI Mülakat Simülasyonu")

# --- 1. FONKSİYONLAR ---
def check_and_download_fonts():
    fonts = {
        "Roboto-Regular.ttf": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
        "Roboto-Bold.ttf": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    }
    for font_name, url in fonts.items():
        if not os.path.exists(font_name):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    with open(font_name, 'wb') as f:
                        f.write(response.content)
            except: pass

def tr_to_en(text):
    if not text: return ""
    tr_map = {'ğ':'g','Ğ':'G','ş':'s','Ş':'S','ı':'i','İ':'I','ç':'c','Ç':'C','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for tr, en in tr_map.items(): text = text.replace(tr, en)
    return text

# --- GÜVENLİ SES FONKSİYONLARI ---
def get_audio_recorder():
    try:
        from audio_recorder_streamlit import audio_recorder
        return audio_recorder
    except ImportError: return None

def speech_to_text(audio_bytes):
    try:
        import speech_recognition as sr 
        r = sr.Recognizer()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
            tmp_audio.write(audio_bytes)
            tmp_path = tmp_audio.name
        
        with sr.AudioFile(tmp_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="tr-TR")
        os.remove(tmp_path)
        return text
    except Exception as e: return None

def text_to_speech(text):
    try:
        from gTTS import gTTS 
        tts = gTTS(text=text, lang='tr')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
            tts.save(tmp_mp3.name)
            return tmp_mp3.name
    except: return None

def create_pdf_report(data):
    check_and_
