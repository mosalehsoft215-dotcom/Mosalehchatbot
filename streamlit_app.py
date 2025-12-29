import streamlit as st
import base64
import io
import os
from PIL import Image
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv

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

# ==========================================================
# HELPERS
# ==========================================================
def apply_ui(theme_mode: str) -> None:
    """Apply professional theme styling"""
    is_dark = theme_mode == "dark"
    
    if is_dark:
        # Dark theme - professional with good contrast
        bg_main = "#0D0D0D"
        bg_sidebar = "#1A1A1A"
        bg_header = "#1F1F1F"
        bg_chat = "#141414"
        bg_input = "#1F1F1F"
        bg_user = "#2A4B7C"
        bg_assistant = "#1F1F1F"
        text_primary = "#FFFFFF"
        text_secondary = "#B4B4B4"
        text_muted = "#808080"
        border_color = "#2D2D2D"
        accent_color = "#7C3AED"
        button_hover = "#2D2D2D"
    else:
        # Light theme - clean and professional
        bg_main = "#FAFAFA"
        bg_sidebar = "#FFFFFF"
        bg_header = "#FFFFFF"
        bg_chat = "#FFFFFF"
        bg_input = "#F5F5F5"
        bg_user = "#E3F2FD"
        bg_assistant = "#F5F5F5"
        text_primary = "#1A1A1A"
        text_secondary = "#4A4A4A"
        text_muted = "#808080"
        border_color = "#E0E0E0"
        accent_color = "#6366F1"
        button_hover = "#F0F0F0"

    css = f"""
    <style>
        /* Reset and base */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        .stApp {{
            background-color: {bg_main};
        }}
        
        /* Hide Streamlit elements */
        #MainMenu, footer, header {{visibility: hidden;}}
        .stDeployButton {{display: none;}}
        
        /* Main container - reduced padding */
        .main .block-container {{
            padding: 1rem 1.5rem;
            max-width: 100%;
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {bg_sidebar};
            border-right: 1px solid {border_color};
            padding: 0 !important;
        }}
        
        [data-testid="stSidebar"] > div:first-child {{
            padding: 1rem;
        }}
        
        [data-testid="stSidebar"] .stMarkdown {{
            margin-bottom: 0.5rem;
        }}
        
        /* Sidebar title */
        [data-testid="stSidebar"] h3 {{
            color: {text_primary};
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            padding: 0 0.5rem;
        }}
        
        /* Header - compact */
        .app-header {{
            background: {bg_header};
            padding: 1rem 1.5rem;
            border-bottom: 1px solid {border_color};
            margin: -1rem -1.5rem 1rem -1.5rem;
        }}
        
        .header-content {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .header-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {text_primary};
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .header-subtitle {{
            font-size: 0.85rem;
            color: {text_secondary};
            margin-top: 0.25rem;
        }}
        
        /* Chat area - no extra spacing */
        .chat-wrapper {{
            background: {bg_chat};
            border: 1px solid {border_color};
            border-radius: 12px;
            height: calc(100vh - 280px);
            overflow-y: auto;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        
        /* Empty state */
        .empty-state {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
        }}
        
        .empty-state h2 {{
            font-size: 1.75rem;
            color: {text_primary};
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}
        
        .empty-state p {{
            color: {text_secondary};
            font-size: 1rem;
        }}
        
        /* Chat messages - compact */
        div[data-testid="stChatMessage"] {{
            padding: 0.5rem 0;
            background: transparent;
        }}
        
        div[data-testid="stChatMessage"] > div {{
            padding: 0.875rem 1rem;
            border-radius: 12px;
            max-width: 80%;
            border: 1px solid {border_color};
        }}
        
        /* User message */
        div[data-testid="stChatMessage"][data-testid*="user"] > div,
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) > div {{
            background: {bg_user};
            margin-left: auto;
            border-color: transparent;
        }}
        
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
            flex-direction: row-reverse;
        }}
        
        /* Assistant message */
        div[data-testid="stChatMessage"][data-testid*="assistant"] > div,
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) > div {{
            background: {bg_assistant};
            margin-right: auto;
        }}
        
        /* Message text */
        div[data-testid="stChatMessage"] p {{
            color: {text_primary};
            line-height: 1.6;
            margin: 0;
        }}
        
        /* Input container - compact */
        .input-wrapper {{
            background: {bg_input};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 0.875rem;
        }}
        
        /* File uploader - compact */
        [data-testid="stFileUploader"] {{
            margin-bottom: 0.75rem;
        }}
        
        [data-testid="stFileUploader"] > div {{
            padding: 0.75rem;
            border: 1.5px dashed {border_color};
            border-radius: 8px;
            background: transparent;
        }}
        
        [data-testid="stFileUploader"] label {{
            color: {text_secondary};
            font-size: 0.85rem;
        }}
        
        [data-testid="stFileUploader"] section {{
            border: none;
            padding: 0;
        }}
        
        /* Chat input */
        [data-testid="stChatInput"] {{
            border: none !important;
            padding: 0 !important;
        }}
        
        [data-testid="stChatInput"] textarea {{
            background: {bg_chat} !important;
            border: 1px solid {border_color} !important;
            border-radius: 10px !important;
            padding: 0.75rem 1rem !important;
            color: {text_primary} !important;
            font-size: 0.95rem !important;
            min-height: 44px !important;
            max-height: 120px !important;
        }}
        
        [data-testid="stChatInput"] textarea:focus {{
            border-color: {accent_color} !important;
            box-shadow: 0 0 0 2px {accent_color}30 !important;
        }}
        
        /* Buttons */
        .stButton button {{
            width: 100%;
            background: {bg_input};
            color: {text_primary};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 0.625rem 1rem;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.2s;
            cursor: pointer;
        }}
        
        .stButton button:hover {{
            background: {button_hover};
            border-color: {accent_color};
        }}
        
        /* Primary button */
        .stButton button[kind="primary"] {{
            background: {accent_color};
            color: white;
            border: none;
            font-weight: 600;
        }}
        
        .stButton button[kind="primary"]:hover {{
            background: {accent_color}DD;
            transform: translateY(-1px);
        }}
        
        /* Radio buttons - compact */
        .stRadio {{
            margin: 0.5rem 0;
        }}
        
        .stRadio > label {{
            color: {text_primary};
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }}
        
        .stRadio [role="radiogroup"] {{
            gap: 0.5rem;
        }}
        
        .stRadio [role="radio"] {{
            background: {bg_input};
            border: 1px solid {border_color};
            padding: 0.5rem 1rem;
            border-radius: 6px;
        }}
        
        /* Divider */
        hr {{
            border: none;
            border-top: 1px solid {border_color};
            margin: 0.75rem 0;
        }}
        
        /* Caption text */
        .stCaption {{
            color: {text_muted};
            font-size: 0.8rem;
        }}
        
        /* Expander */
        [data-testid="stExpander"] {{
            background: transparent;
            border: 1px solid {border_color};
            border-radius: 8px;
            margin: 0.5rem 0;
        }}
        
        [data-testid="stExpander"] summary {{
            color: {text_primary};
            font-weight: 500;
            padding: 0.75rem;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {border_color};
            border-radius: 3px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {text_muted};
        }}
        
        /* Code blocks */
        pre {{
            background: {bg_input} !important;
            border: 1px solid {border_color} !important;
            border-radius: 6px !important;
            padding: 0.75rem !important;
        }}
        
        code {{
            color: {text_primary} !important;
            font-size: 0.9rem !important;
        }}
        
        /* Images in chat */
        [data-testid="stChatMessage"] img {{
            border-radius: 8px;
            max-width: 100%;
            margin-top: 0.5rem;
        }}
        
        /* Settings section */
        .settings-section {{
            margin: 0.75rem 0;
        }}
        
        .settings-label {{
            color: {text_primary};
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: block;
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

def get_preview(chat_messages, max_len: int = 35) -> str:
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
apply_ui(st.session_state.theme_mode)

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
    
    # Conversation history
    if st.session_state.conversations:
        for chat_id in reversed(list(st.session_state.conversations.keys())):
            messages_in_chat = st.session_state.conversations[chat_id]
            preview = get_preview(messages_in_chat)
            
            is_active = chat_id == st.session_state.current_chat_id
            icon = "🟢" if is_active else "💬"
            
            if st.button(f"{icon} {preview}", key=f"chat_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.session_state.uploader_counter += 1
                st.rerun()
    
    st.divider()
    
    # Settings
    with st.expander("⚙️ Settings"):
        st.markdown('<span class="settings-label">Theme</span>', unsafe_allow_html=True)
        theme = st.radio(
            "theme_selector",
            ["light", "dark"],
            index=0 if st.session_state.theme_mode == "light" else 1,
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if theme != st.session_state.theme_mode:
            st.session_state.theme_mode = theme
            st.rerun()

# ==========================================================
# MAIN CONTENT
# ==========================================================

# Header
st.markdown(
    """
    <div class="app-header">
        <div class="header-content">
            <div>
                <div class="header-title">✨ M‑Saleh AI Assistant</div>
                <div class="header-subtitle">Powered by Groq • Multi-modal conversations • Real-time streaming</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Chat area
messages = st.session_state.conversations[st.session_state.current_chat_id]

st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

if not messages:
    st.markdown(
        """
        <div class="empty-state">
            <h2>👋 Hello! How can I assist you today?</h2>
            <p>Start a conversation by typing a message below</p>
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
                    st.image(item["image_url"]["url"], width=350)

st.markdown('</div>', unsafe_allow_html=True)

# Input area
st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)

uploaded_image = st.file_uploader(
    "📎 Attach image",
    type=["png", "jpg", "jpeg"],
    key=f"uploader_{st.session_state.uploader_counter}",
    label_visibility="collapsed"
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
    
    messages.append({"role": "user", "content": user_content})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_prompt.strip())
        if uploaded_image:
            st.image(uploaded_image, width=350)
    
    # Assistant response
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
    
    messages.append({"role": "assistant", "content": [{"type": "text", "text": full_response}]})
    st.session_state.uploader_counter += 1
    st.rerun()
