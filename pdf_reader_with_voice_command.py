import streamlit as st
import speech_recognition as sr
from dotenv import load_dotenv

from gtts import gTTS
import tempfile
from pypdf import PdfReader
import google.generativeai as genai
import os
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ GOOGLE_API_KEY environment variable not set.")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")



def process_pdf(uploaded_file):
    if not uploaded_file:
        return "❌ No file uploaded."

    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    if not text.strip():
        return "❌ No readable text found in PDF."

    return text

def query_qa(uploaded_file, question):
    pdf_text = process_pdf(uploaded_file)
    if isinstance(pdf_text, str) and pdf_text.startswith("❌"):
        return pdf_text
    try:
        prompt = f"Answer the following question based on this PDF content:\n\n{pdf_text}\n\nQuestion: {question}"
        response = model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else str(response)
    except Exception as e:
        return f"❌ Error during question answering: {str(e)}"

def get_voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Listening... Speak now")
        audio = recognizer.listen(source)
        try:
            query = recognizer.recognize_google(audio)
            st.success(f"🗣️ You said: {query}")
            return query
        except sr.UnknownValueError:
            st.error("❌ Could not understand audio.")
        except sr.RequestError:
            st.error("❌ Could not connect to recognition service.")
    return ""

def speak_text(text):
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3")
    except Exception as e:
        st.error(f"❌ Voice output error: {str(e)}")

# Streamlit UI
st.title("🧠 GenAI Voice PDF Assistant")

uploaded_pdf = st.file_uploader("📎 Upload a PDF file", type="pdf")

if "query" not in st.session_state:
    st.session_state["query"] = ""

if st.button("🎤 Use Voice Input"):
    voice_query = get_voice_input()
    if voice_query:
        st.session_state["query"] = voice_query

query = st.text_input("💬 Ask a question", value=st.session_state["query"])
st.session_state["query"] = query

if st.button("🔍 Get Answer"):
    if uploaded_pdf and st.session_state["query"]:
        answer = query_qa(uploaded_pdf, st.session_state["query"])
        st.text_area("📝 Answer", value=answer, height=150)
        speak_text(answer)
    else:
        st.warning("⚠️ Please upload a PDF and provide a question.")