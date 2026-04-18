AI-Powered Talent Assessment & Interview Simulator
Bu kodlar, projenin sadece bir "ödev" değil, uçtan uca bir ürün (SaaS MVP) olduğunu kanıtlıyor. Upwork'te bu projeyi sunarken; Streamlit, Google Gemini API, Speech-to-Text ve Otomatik Raporlama entegrasyonlarını vurgulaman seni diğer adayların çok önüne geçirecektir.

İşte Upwork portföyün için bu koda özel hazırlanmış açıklama:

Project Title: AI-Powered Talent Assessment & Interview Simulator
Project Overview
I developed a comprehensive, end-to-end AI Interview Simulation tool that automates the recruitment process. This application enables candidates to undergo realistic, competency-based interviews using LLMs while providing recruiters with detailed, data-driven assessment reports.

Key Technical Features
LLM Integration & Prompt Engineering: Orchestrated Google Gemini 1.5 Pro/Flash using advanced system prompting to simulate a "Senior Talent Assessment Agent." Implemented a "Deep-Dive" questioning strategy and STAR methodology enforcement.

Multimodal Interaction: Integrated Speech-to-Text (STT) and Text-to-Speech (TTS) features, allowing candidates to interact via voice or text, providing a natural interview experience.

Dynamic Data Processing: Developed a custom PDF engine to parse CVs and Portfolios, enabling the AI to ask context-aware, personalized technical questions.

Automated Evaluation System: Built a reporting module that analyzes interview transcripts to generate:

Competency Radar Charts (using Plotly) for technical, communication, and problem-solving skills.

Automated PDF Reports (using FPDF) with logic-based hiring decisions.

Session & Time Management: Implemented real-time tracking for interview flow, ensuring candidate responses are handled within specific time limits (5-minute window) to simulate high-pressure environments.

Technical Stack
Frontend/UI: Streamlit (Python-based Web Framework)

AI/ML: Google Generative AI (Gemini API), gTTS (Google Text-to-Speech)

Data Visualization: Plotly (Radar Charts)

File Handling: PyPDF, FPDF (PDF Generation/Parsing)

Speech Processing: Streamlit Mic Recorder (STT)

The Impact
This tool demonstrates my ability to build production-ready AI agents. It solves real-world recruitment bottlenecks by providing consistent, objective, and scalable initial screenings, significantly reducing the manual workload for HR departments.
