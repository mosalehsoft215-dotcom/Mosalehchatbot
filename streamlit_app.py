import streamlit as st
import base64
import io
import os
from datetime import datetime
from typing import Optional

from PIL import Image
from groq import Groq
from dotenv import load_dotenv

# ============================
# LOAD ENV / SECRETS
# ============================
load_dotenv()

def get_groq_api_key() -> Optional[str]:
    # Streamlit Cloud / Streamlit Secrets
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    # Local dev (.env or environment variables)
    return os.getenv("GROQ_API_KEY")

GROQ_API_KEY = get_groq_api_key()
if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found. Add it to Streamlit Secrets or a local .env file.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ============================
# PAGE CONFIG
# ============================
st.set_page_config(
    page_title="M-Saleh Chatbot Model",
    page_icon="🝪",
    layout="centered"
)

st.title("🤖 M-Saleh Chatbot Model")
st.caption("Professional Multi-Chat Vision + Text AI")

# ============================
# SESSION STATE
# ============================
if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_chat_id" not in st.session_state:
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.current_chat_id = chat_id
    st.session_state.conversations[chat_id] = []

if "uploader_counter" not in st.session_state:
    st.session_state.uploader_counter = 0

# ============================
# HELPERS
# ============================
def image_to_base64(uploaded_file) -> str:
    image = Image.open(uploaded_file).convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def new_chat() -> None:
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.current_chat_id = chat_id
    st.session_state.conversations[chat_id] = []
    st.session_state.uploader_counter += 1
    st.rerun()

# ============================
# SIDEBAR
# ============================
with st.sidebar:
    st.header("💬 Chats")

    if st.button("➕ New Chat"):
        new_chat()

    st.markdown("---")

    for chat_id in reversed(list(st.session_state.conversations.keys())):
        label = f"Chat {chat_id[-6:]}"
        if st.button(label, key=f"chat_{chat_id}"):
            st.session_state.current_chat_id = chat_id
            st.session_state.uploader_counter += 1
            st.rerun()

# ============================
# CURRENT CHAT
# ============================
messages = st.session_state.conversations[st.session_state.current_chat_id]

# ============================
# DISPLAY CHAT
# ============================
for msg in messages:
    with st.chat_message(msg["role"]):
        for item in msg["content"]:
            if item["type"] == "text":
                st.markdown(item["text"])
            elif item["type"] == "image_url":
                st.image(item["image_url"]["url"])

# ============================
# INPUT AREA
# ============================
uploaded_image = st.file_uploader(
    "📎 Attach image (optional)",
    type=["png", "jpg", "jpeg"],
    key=f"uploader_{st.session_state.uploader_counter}"
)

user_prompt = st.chat_input("Type a message and press Enter...")

# ============================
# SEND LOGIC
# ============================
if user_prompt and user_prompt.strip():
    user_content = [{"type": "text", "text": user_prompt}]

    if uploaded_image:
        image_b64 = image_to_base64(uploaded_image)
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
        })

    # Save user message
    messages.append({"role": "user", "content": user_content})

    # Assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        completion = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[
                {"role": "system", "content": "You are a professional, helpful AI assistant."},
                *messages
            ],
            temperature=0.9,
            max_completion_tokens=1024,
            stream=True
        )

        for chunk in completion:
            delta = chunk.choices[0].delta.content
            if delta:
                full_response += delta
                placeholder.markdown(full_response)

    messages.append({
        "role": "assistant",
        "content": [{"type": "text", "text": full_response}]
    })

    # Reset uploader safely
    st.session_state.uploader_counter += 1
    st.rerun()
