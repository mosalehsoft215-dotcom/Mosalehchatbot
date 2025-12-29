import streamlit as st
import base64
import io
import os
from PIL import Image
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# ==========================================================
# CONFIG / SECRETS
# ==========================================================
load_dotenv()

def get_groq_api_key() -> str | None:
    """Prefer Streamlit Secrets (cloud), fall back to env/.env (local)."""
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY")

GROQ_API_KEY = get_groq_api_key()
if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found. Add it to Streamlit Secrets or create a local .env file.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="M‑Saleh AI Assistant",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# THEME + UI STATE
# ==========================================================
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"
if "wrap_code" not in st.session_state:
    st.session_state.wrap_code = True
if "show_previews" not in st.session_state:
    st.session_state.show_previews = True

# ==========================================================
# HELPERS
# ==========================================================
def apply_ui(theme_mode: str, wrap_code: bool) -> None:
    """Apply professional theme styling inspired by Gemini and Grok"""
    is_dark = theme_mode == "dark"
    
    if is_dark:
        # Dark theme - inspired by Gemini/Grok
        bg_primary = "#0A0A0A"
        bg_secondary = "#1A1A1A"
        bg_chat = "#171717"
        bg_user = "#2D2D2D"
        bg_assistant = "#1E1E1E"
        text_primary = "#E8E8E8"
        text_secondary = "#A0A0A0"
        border_color = "#2D2D2D"
        accent_color = "#8B5CF6"
        input_bg = "#1E1E1E"
        sidebar_bg = "#0F0F0F"
    else:
        # Light theme - clean and professional
        bg_primary = "#FFFFFF"
        bg_secondary = "#F8F9FA"
        bg_chat = "#FFFFFF"
        bg_user = "#F0F4FF"
        bg_assistant = "#F8F9FA"
        text_primary = "#1A1A1A"
        text_secondary = "#6B7280"
        border_color = "#E5E7EB"
        accent_color = "#6366F1"
        input_bg = "#FFFFFF"
        sidebar_bg = "#F9FAFB"

    code_wrap = "white-space: pre-wrap !important; word-break: break-word !important;" if wrap_code else ""

    css = f"""
    <style>
        /* Global Styles */
        .stApp {{
            background-color: {bg_primary};
            color: {text_primary};
        }}
        
        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Main container */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }}
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg};
            border-right: 1px solid {border_color};
        }}
        
        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 2rem;
        }}
        
        /* Header section */
        .header-container {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.5rem 2rem;
            background-color: {bg_secondary};
            border-radius: 16px;
            margin-bottom: 2rem;
            border: 1px solid {border_color};
        }}
        
        .header-title {{
            font-size: 1.8rem;
            font-weight: 700;
            color: {text_primary};
            margin: 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .header-subtitle {{
            font-size: 0.95rem;
            color: {text_secondary};
            margin-top: 0.25rem;
        }}
        
        /* Chat container */
        .chat-container {{
            background-color: {bg_chat};
            border-radius: 20px;
            padding: 1.5rem;
            min-height: 60vh;
            max-height: 65vh;
            overflow-y: auto;
            border: 1px solid {border_color};
            margin-bottom: 1rem;
        }}
        
        /* Chat messages */
        div[data-testid="stChatMessage"] {{
            background-color: transparent;
            padding: 0.75rem 0;
            border: none;
        }}
        
        div[data-testid="stChatMessage"] > div {{
            border-radius: 18px;
            padding: 1rem 1.25rem;
            border: 1px solid {border_color};
            max-width: 85%;
        }}
        
        /* User message */
        div[data-testid="stChatMessage"][data-testid*="user"] > div {{
            background-color: {bg_user};
            margin-left: auto;
        }}
        
        /* Assistant message */
        div[data-testid="stChatMessage"][data-testid*="assistant"] > div {{
            background-color: {bg_assistant};
            margin-right: auto;
        }}
        
        /* Chat input area */
        .input-container {{
            background-color: {bg_secondary};
            border-radius: 16px;
            padding: 1.25rem;
            border: 1px solid {border_color};
        }}
        
        div[data-testid="stChatInput"] {{
            background-color: transparent;
        }}
        
        div[data-testid="stChatInput"] textarea {{
            background-color: {input_bg} !important;
            border: 2px solid {border_color} !important;
            border-radius: 12px !important;
            padding: 0.875rem !important;
            font-size: 0.95rem !important;
            color: {text_primary} !important;
            resize: none !important;
            min-height: 52px !important;
        }}
        
        div[data-testid="stChatInput"] textarea:focus {{
            border-color: {accent_color} !important;
            box-shadow: 0 0 0 3px {accent_color}20 !important;
        }}
        
        /* File uploader */
        .stFileUploader {{
            background-color: transparent;
            border: 2px dashed {border_color};
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        
        .stFileUploader:hover {{
            border-color: {accent_color};
            background-color: {accent_color}10;
        }}
        
        /* Buttons */
        .stButton > button {{
            width: 100%;
            border-radius: 10px;
            padding: 0.625rem 1rem;
            font-weight: 500;
            border: 1px solid {border_color};
            background-color: {bg_secondary};
            color: {text_primary};
            transition: all 0.2s;
        }}
        
        .stButton > button:hover {{
            background-color: {accent_color};
            border-color: {accent_color};
            color: white;
            transform: translateY(-1px);
        }}
        
        /* Primary button (New Chat) */
        .stButton > button[kind="primary"] {{
            background-color: {accent_color};
            color: white;
            border: none;
        }}
        
        .stButton > button[kind="primary"]:hover {{
            background-color: {accent_color}DD;
        }}
        
        /* Radio buttons */
        .stRadio > div {{
            flex-direction: row;
            gap: 0.5rem;
        }}
        
        .stRadio > div > label {{
            background-color: {bg_secondary};
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border: 1px solid {border_color};
            cursor: pointer;
        }}
        
        /* Toggle */
        .stCheckbox {{
            padding: 0.5rem 0;
        }}
        
        /* Divider */
        hr {{
            border-color: {border_color};
            margin: 1rem 0;
        }}
        
        /* Code blocks */
        pre {{
            background-color: {bg_secondary} !important;
            border: 1px solid {border_color} !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }}
        
        pre code {{
            {code_wrap}
            color: {text_primary} !important;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {bg_secondary};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {border_color};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {text_secondary};
        }}
        
        /* Quick action buttons */
        .quick-actions {{
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }}
        
        .quick-action-btn {{
            background-color: {bg_secondary};
            border: 1px solid {border_color};
            border-radius: 20px;
            padding: 0.5rem 1rem;
            font-size: 0.85rem;
            color: {text_primary};
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .quick-action-btn:hover {{
            background-color: {accent_color}20;
            border-color: {accent_color};
        }}
        
        /* Settings popover */
        [data-testid="stPopover"] {{
            background-color: {bg_secondary};
        }}
        
        /* Captions and help text */
        .stCaption {{
            color: {text_secondary};
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def image_to_base64(uploaded_file) -> str:
    image = Image.open(uploaded_file).convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def new_chat():
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.current_chat_id = chat_id
    st.session_state.conversations[chat_id] = []
    st.session_state.uploader_counter += 1
    st.rerun()

def get_preview(chat_messages, max_len: int = 40) -> str:
    """Return a short label preview based on the last user message."""
    last_user_text = ""
    for m in reversed(chat_messages):
        if m.get("role") == "user":
            for item in m.get("content", []):
                if item.get("type") == "text":
                    last_user_text = item.get("text", "")
                    break
        if last_user_text:
            break
    if not last_user_text:
        return "New conversation"
    last_user_text = " ".join(last_user_text.split())
    return (last_user_text[:max_len] + "...") if len(last_user_text) > max_len else last_user_text

# Apply UI theme
apply_ui(st.session_state.theme_mode, st.session_state.wrap_code)

# ==========================================================
# SESSION STATE
# ==========================================================
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_chat_id" not in st.session_state:
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.current_chat_id = chat_id
    st.session_state.conversations[chat_id] = []
if "uploader_counter" not in st.session_state:
    st.session_state.uploader_counter = 0

# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    st.markdown("### 💬 Conversations")
    
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_chat()
    
    st.divider()
    
    # Show conversation history
    if st.session_state.conversations:
        st.caption("RECENT CHATS")
        for chat_id in reversed(list(st.session_state.conversations.keys())):
            messages_in_chat = st.session_state.conversations[chat_id]
            preview = get_preview(messages_in_chat) if st.session_state.show_previews else f"Chat {chat_id[-6:]}"
            
            is_active = chat_id == st.session_state.current_chat_id
            label = f"{'🟢' if is_active else '💬'} {preview}"
            
            if st.button(label, key=f"chat_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.session_state.uploader_counter += 1
                st.rerun()
    
    st.divider()
    
    # Settings in sidebar
    with st.expander("⚙️ Settings", expanded=False):
        theme = st.radio(
            "Theme",
            ["light", "dark"],
            index=0 if st.session_state.theme_mode == "light" else 1,
            horizontal=True
        )
        
        wrap_code = st.checkbox(
            "Wrap code blocks",
            value=st.session_state.wrap_code
        )
        
        show_previews = st.checkbox(
            "Show message previews",
            value=st.session_state.show_previews
        )
        
        # Apply changes
        if (theme != st.session_state.theme_mode or 
            wrap_code != st.session_state.wrap_code or 
            show_previews != st.session_state.show_previews):
            st.session_state.theme_mode = theme
            st.session_state.wrap_code = wrap_code
            st.session_state.show_previews = show_previews
            st.rerun()
    
    st.divider()
    st.caption("🔑 Powered by Groq API")

# ==========================================================
# MAIN CONTENT
# ==========================================================

# Header
st.markdown(
    """
    <div class="header-container">
        <div>
            <div class="header-title">✨ M‑Saleh AI Assistant</div>
            <div class="header-subtitle">Powered by Groq • Multi-modal conversations • Real-time streaming</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Chat container
messages = st.session_state.conversations[st.session_state.current_chat_id]

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display chat history
if not messages:
    st.markdown(
        """
        <div style="text-align: center; padding: 4rem 2rem;">
            <h2 style="margin-bottom: 1rem;">👋 Hello! How can I assist you today?</h2>
            <p style="color: #6B7280; font-size: 1rem;">Start a conversation by typing a message below</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    for msg in messages:
        with st.chat_message(msg["role"]):
            for item in msg["content"]:
                if item["type"] == "text":
                    st.markdown(item["text"])
                elif item["type"] == "image_url":
                    st.image(item["image_url"]["url"], width=400)

st.markdown('</div>', unsafe_allow_html=True)

# Input area
st.markdown('<div class="input-container">', unsafe_allow_html=True)

uploaded_image = st.file_uploader(
    "📎 Attach an image (optional)",
    type=["png", "jpg", "jpeg"],
    key=f"uploader_{st.session_state.uploader_counter}",
    help="Upload an image to include in your message"
)

user_prompt = st.chat_input("Ask me anything...")

st.markdown('</div>', unsafe_allow_html=True)

# Send logic
if user_prompt and user_prompt.strip():
    user_content = [{"type": "text", "text": user_prompt.strip()}]
    
    if uploaded_image:
        image_b64 = image_to_base64(uploaded_image)
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
        })
    
    # Save user message
    messages.append({"role": "user", "content": user_content})
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_prompt.strip())
        if uploaded_image:
            st.image(uploaded_image, width=400)
    
    # Assistant response (streaming)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            completion = client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[
                    {"role": "system", "content": "You are a professional, helpful AI assistant. Provide clear, accurate, and thoughtful responses."},
                    *messages
                ],
                temperature=0.9,
                max_completion_tokens=2048,
                stream=True
            )
            
            for chunk in completion:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_response += delta
                    placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            
        except Exception as e:
            placeholder.error(f"Error: {str(e)}")
            full_response = f"Sorry, I encountered an error: {str(e)}"
    
    # Save assistant message
    messages.append({"role": "assistant", "content": [{"type": "text", "text": full_response}]})
    st.session_state.uploader_counter += 1
    st.rerun()
