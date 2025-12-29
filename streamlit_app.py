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
# CONFIG / SECRETS (KEPT EXACTLY AS REQUESTED)
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
    page_title="M‑Saleh Chatbot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==========================================================
# THEME + UI STATE
# ==========================================================
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"  # Default to Dark

if "starry_bg" not in st.session_state:
    st.session_state.starry_bg = True

if "wrap_code" not in st.session_state:
    st.session_state.wrap_code = False

if "show_previews" not in st.session_state:
    st.session_state.show_previews = True

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "llama-3.3-70b-versatile"

# ==========================================================
# HELPERS
# ==========================================================
def load_file_b64(path: Path) -> str | None:
    try:
        data = path.read_bytes()
        return base64.b64encode(data).decode("utf-8")
    except Exception:
        return None

def apply_ui(theme_mode: str, starry_bg: bool, wrap_code: bool) -> None:
    """
    Applied Fixed UI with High Contrast for Dark Mode
    """
    is_dark = theme_mode == "Dark"
    
    # Try to load local asset, else None
    bg_img_b64 = None
    if is_dark and starry_bg:
        bg_path = Path(__file__).parent / "assets" / "space_bg.png"
        if bg_path.exists():
            bg_img_b64 = load_file_b64(bg_path)

    # DEFINING COLORS
    if is_dark:
        # HIGH CONTRAST DARK MODE
        base_bg = "#05070A"
        card_bg = "rgba(20, 25, 35, 0.95)" # Less transparent for readability
        text_color = "#FFFFFF"              # Pure White Text
        muted_color = "#A0AAB8"
        border_color = "rgba(255,255,255,0.15)"
        user_bubble = "rgba(60, 80, 200, 0.3)"
        bot_bubble = "rgba(255, 255, 255, 0.1)"
    else:
        # CLEAN LIGHT MODE
        base_bg = "#F6F7FB"
        card_bg = "rgba(255, 255, 255, 0.9)"
        text_color = "#0E1222"
        muted_color = "rgba(14, 18, 34, 0.65)"
        border_color = "rgba(14,18,34,0.10)"
        user_bubble = "rgba(120,130,255,0.15)"
        bot_bubble = "rgba(0,0,0,0.05)"

    # Background CSS
    bg_css = ""
    if bg_img_b64:
        # Use image if found
        bg_css = f"""
            background-color: {base_bg};
            background-image: 
              radial-gradient(1200px 700px at 20% 5%, rgba(120,130,255,0.15), transparent 60%),
              url("data:image/png;base64,{bg_img_b64}");
            background-size: cover;
            background-attachment: fixed;
        """
    elif is_dark and starry_bg:
        # CSS Fallback if image missing (Professional Dark Gradient)
        bg_css = f"""
            background-color: {base_bg};
            background-image: 
              radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
              radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
              radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
            background-attachment: fixed;
        """
    else:
        bg_css = f"background-color: {base_bg};"

    code_wrap_css = ""
    if wrap_code:
        code_wrap_css = "pre code { white-space: pre-wrap !important; word-break: break-word !important; }"

    # INJECT CSS
    css = f"""
    <style>
      /* Page background */
      .stApp {{
        {bg_css}
        color: {text_color};
      }}

      /* Content width + spacing */
      section.main > div {{
        max-width: 900px;
        padding-top: 2rem;
      }}

      /* Header Styling */
      .ms-topbar {{
        margin-bottom: 1rem;
      }}
      .ms-title {{
        font-size: 1.8rem;
        font-weight: 800;
        color: {text_color};
      }}
      .ms-subtitle {{
        font-size: 1rem;
        color: {muted_color};
      }}

      /* Main Chat Card */
      .ms-card {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        margin-bottom: 20px;
      }}

      /* Chat Bubbles */
      div[data-testid="stChatMessage"] {{
        background: transparent;
      }}
      
      div[data-testid="stChatMessage"][data-role="user"] div[data-testid="stMarkdownContainer"] {{
        background: {user_bubble};
        color: {text_color};
        padding: 12px 18px;
        border-radius: 18px;
        border-bottom-right-radius: 4px;
      }}
      
      div[data-testid="stChatMessage"][data-role="assistant"] div[data-testid="stMarkdownContainer"] {{
        background: {bot_bubble};
        color: {text_color};
        padding: 12px 18px;
        border-radius: 18px;
        border-bottom-left-radius: 4px;
      }}

      /* Input Area */
      div[data-testid="stChatInput"] textarea {{
        background: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
      }}

      /* Markdown text adjustment */
      p, li, h1, h2, h3, h4, h5, h6 {{
        color: {text_color} !important;
      }}
      
      {code_wrap_css}
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

def get_preview(chat_messages, max_len: int = 34) -> str:
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
        return "New chat"
    last_user_text = " ".join(last_user_text.split())
    return (last_user_text[:max_len] + "…") if len(last_user_text) > max_len else last_user_text

# Apply UI theme first
apply_ui(st.session_state.theme_mode, st.session_state.starry_bg, st.session_state.wrap_code)

# ==========================================================
# SESSION STATE: conversations
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
    st.title("🤖 M-Saleh")
    
    # Model Selector (CRITICAL UPDATE)
    st.markdown("### 🧠 AI Model")
    st.session_state.selected_model = st.selectbox(
        "Choose Model:",
        options=[
            "llama-3.3-70b-versatile",          # Best for pure text
            "meta-llama/llama-4-maverick-17b-128e-instruct"  # Vision support
        ],
        index=0,
        help="Use 'Maverick' if you need to analyze images. Use 'Versatile' for faster text."
    )

    st.divider()
    
    if st.button("➕ New Chat", use_container_width=True):
        new_chat()

    st.markdown("### 💬 History")
    for chat_id in reversed(list(st.session_state.conversations.keys())):
        preview = get_preview(st.session_state.conversations[chat_id]) if st.session_state.show_previews else f"Chat {chat_id[-6:]}"
        if st.button(f"🗨️ {preview}", key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.session_state.uploader_counter += 1
            st.rerun()

# ==========================================================
# TOP BAR + SETTINGS
# ==========================================================
col_a, col_b = st.columns([7, 1])
with col_a:
    st.markdown(
        """
        <div class="ms-topbar">
          <div class="ms-title">🤖 M‑Saleh Chatbot</div>
          <div class="ms-subtitle">Professional AI Assistant • Multi-Model Support</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_b:
    with st.popover("⚙️", use_container_width=True):
        st.markdown("#### Settings")
        
        # Theme Selector (Removed System option)
        theme = st.radio(
            "Theme Mode",
            ["Dark", "Light"],
            index=["Dark", "Light"].index(st.session_state.theme_mode),
            horizontal=True
        )

        st.divider()
        wrap_code = st.toggle("Wrap Code Lines", value=st.session_state.wrap_code)
        show_previews = st.toggle("Show History Previews", value=st.session_state.show_previews)
        
        starry_bg = st.session_state.starry_bg
        if theme == "Dark":
            starry_bg = st.toggle("Starry Background", value=st.session_state.starry_bg)

        # Apply changes
        if (theme != st.session_state.theme_mode or 
            wrap_code != st.session_state.wrap_code or 
            show_previews != st.session_state.show_previews or 
            starry_bg != st.session_state.starry_bg):
            
            st.session_state.theme_mode = theme
            st.session_state.wrap_code = wrap_code
            st.session_state.show_previews = show_previews
            st.session_state.starry_bg = starry_bg
            st.rerun()

# ==========================================================
# MAIN CHAT "CARD"
# ==========================================================
st.markdown('<div class="ms-card">', unsafe_allow_html=True)

messages = st.session_state.conversations[st.session_state.current_chat_id]

# Display chat history
for msg in messages:
    with st.chat_message(msg["role"]):
        for item in msg["content"]:
            if item["type"] == "text":
                st.markdown(item["text"])
            elif item["type"] == "image_url":
                # Handle images in history
                st.image(item["image_url"]["url"], width=300)

# Input area (uploader + chat input)
with st.container():
    uploaded_image = st.file_uploader(
        "📎 Attach an image (Required for Vision Model)",
        type=["png", "jpg", "jpeg"],
        key=f"uploader_{st.session_state.uploader_counter}",
    )
    
    if uploaded_image and "llama-4" not in st.session_state.selected_model:
        st.warning("⚠️ You attached an image but selected a Text-only model. Please switch to 'Llama 4 Maverick' in the sidebar.")

user_prompt = st.chat_input("Type a message...")

# Send logic
if user_prompt and user_prompt.strip():
    user_content = [{"type": "text", "text": user_prompt.strip()}]
    
    # Image Handling
    if uploaded_image:
        image_b64 = image_to_base64(uploaded_image)
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
        })

    # Save user message
    messages.append({"role": "user", "content": user_content})
    
    # Force UI update to show user message immediately
    with st.chat_message("user"):
        st.markdown(user_prompt)
        if uploaded_image:
            st.image(uploaded_image, width=300)

    # Assistant response (streaming)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            # Use the SELECTED model variable
            completion = client.chat.completions.create(
                model=st.session_state.selected_model,
                messages=[
                    {"role": "system", "content": "You are a professional, helpful AI assistant."},
                    *messages
                ],
                temperature=0.7,
                max_completion_tokens=1024,
                stream=True
            )

            for chunk in completion:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_response += delta
                    placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            messages.append({"role": "assistant", "content": [{"type": "text", "text": full_response}]})
            
        except Exception as e:
            st.error(f"Error: {e}")
            if "model_decommissioned" in str(e):
                st.info("💡 Tip: Try switching the model in the Sidebar.")

    st.session_state.uploader_counter += 1
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
