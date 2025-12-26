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
    page_title="M‑Saleh Chatbot",
    page_icon="🝪",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==========================================================
# THEME + UI STATE
# ==========================================================
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "System"  # Light / Dark / System

if "starry_bg" not in st.session_state:
    st.session_state.starry_bg = True

if "wrap_code" not in st.session_state:
    st.session_state.wrap_code = False

if "show_previews" not in st.session_state:
    st.session_state.show_previews = True

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
    Streamlit doesn't have a first-class runtime theme switch for custom UIs,
    so we style the app with CSS.
    """
    is_dark = theme_mode == "Dark"
    use_custom = theme_mode in ("Light", "Dark")

    bg_img_b64 = None
    if is_dark and starry_bg:
        bg_path = Path(__file__).parent / "assets" / "space_bg.png"
        bg_img_b64 = load_file_b64(bg_path)

    # Backgrounds
    if not use_custom:
        # System: leave Streamlit defaults, only apply small polish
        base_bg = ""
        card_bg = "rgba(255,255,255,0.75)"
        text = ""
        muted = ""
        border = "rgba(0,0,0,0.08)"
    else:
        if is_dark:
            base_bg = "#070A12"
            card_bg = "rgba(18, 24, 38, 0.72)"
            text = "#E8EEF8"
            muted = "rgba(232, 238, 248, 0.72)"
            border = "rgba(255,255,255,0.10)"
        else:
            base_bg = "#F6F7FB"
            card_bg = "rgba(255, 255, 255, 0.80)"
            text = "#0E1222"
            muted = "rgba(14, 18, 34, 0.65)"
            border = "rgba(14,18,34,0.10)"

    bg_css = ""
    if use_custom:
        if bg_img_b64:
            bg_css = f"""
            background-color: {base_bg};
            background-image:
              radial-gradient(1200px 700px at 20% 5%, rgba(120,130,255,0.22), transparent 60%),
              radial-gradient(900px 500px at 90% 15%, rgba(255,90,160,0.14), transparent 55%),
              url("data:image/png;base64,{bg_img_b64}");
            background-size: auto, auto, cover;
            background-position: center, center, center;
            background-attachment: fixed;
            """
        else:
            bg_css = f"""
            background-color: {base_bg};
            background-image:
              radial-gradient(1200px 700px at 20% 5%, rgba(120,130,255,0.22), transparent 60%),
              radial-gradient(900px 500px at 90% 15%, rgba(255,90,160,0.14), transparent 55%);
            background-attachment: fixed;
            """

    code_wrap_css = ""
    if wrap_code:
        code_wrap_css = """
        pre code { white-space: pre-wrap !important; word-break: break-word !important; }
        """

    css = f"""
    <style>
      /* Page background */
      .stApp {{
        {bg_css}
      }}

      /* Content width + spacing */
      section.main > div {{
        max-width: 980px;
        padding-top: 1.0rem;
        padding-bottom: 1.2rem;
      }}

      /* Subtle top header */
      .ms-topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 0.5rem;
      }}
      .ms-brand {{
        display: flex;
        align-items: baseline;
        gap: 10px;
      }}
      .ms-title {{
        font-size: 1.35rem;
        font-weight: 750;
        letter-spacing: -0.02em;
        color: {text if use_custom else 'inherit'};
      }}
      .ms-subtitle {{
        font-size: 0.92rem;
        color: {muted if use_custom else 'inherit'};
        margin-top: -2px;
      }}

      /* Chat "card" */
      .ms-card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 20px;
        padding: 14px 14px 10px 14px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.10);
      }}

      /* Chat message bubbles */
      div[data-testid="stChatMessage"] {{
        padding: 0.35rem 0.25rem;
      }}
      div[data-testid="stChatMessage"] > div {{
        border-radius: 16px;
        padding: 0.55rem 0.75rem;
      }}
      /* user bubble */
      div[data-testid="stChatMessage"][data-role="user"] > div {{
        border: 1px solid {border};
        background: rgba(120,130,255,0.12);
      }}
      /* assistant bubble */
      div[data-testid="stChatMessage"][data-role="assistant"] > div {{
        border: 1px solid {border};
        background: rgba(255,255,255,0.04);
      }}

      /* Chat input */
      div[data-testid="stChatInput"] textarea {{
        border-radius: 16px !important;
        border: 1px solid {border} !important;
      }}
      div[data-testid="stChatInput"] {{
        padding-top: 0.5rem;
      }}

      /* File uploader card */
      .ms-uploader {{
        margin-top: 0.65rem;
      }}

      /* Sidebar polish */
      [data-testid="stSidebar"] > div {{
        padding-top: 1.0rem;
      }}

      /* Reduce Streamlit default top padding a bit */
      header[data-testid="stHeader"] {{
        background: transparent;
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
        return "New chat"
    last_user_text = " ".join(last_user_text.split())
    return (last_user_text[:max_len] + "…") if len(last_user_text) > max_len else last_user_text

# Apply UI theme first (so it affects everything below)
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
    st.markdown("### 💬 Chats")

    if st.button("➕ New Chat", use_container_width=True):
        new_chat()

    st.divider()

    for chat_id in reversed(list(st.session_state.conversations.keys())):
        preview = get_preview(st.session_state.conversations[chat_id]) if st.session_state.show_previews else f"Chat {chat_id[-6:]}"
        label = f"🗨️ {preview}"
        if st.button(label, key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.session_state.uploader_counter += 1
            st.rerun()

    st.divider()
    st.caption("Tip: Add your Groq key in **Secrets** (cloud) or a local **.env** file.")

# ==========================================================
# TOP BAR + SETTINGS (popover)
# ==========================================================
col_a, col_b = st.columns([7, 1])
with col_a:
    st.markdown(
        """
        <div class="ms-topbar">
          <div class="ms-brand">
            <div>
              <div class="ms-title">🤖 M‑Saleh Chatbot</div>
              <div class="ms-subtitle">Modern multi‑chat • Optional image input • Streaming responses</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_b:
    with st.popover("⚙️", use_container_width=True):
        st.markdown("#### Settings")

        theme = st.radio(
            "Appearance",
            ["Light", "Dark", "System"],
            index=["Light", "Dark", "System"].index(st.session_state.theme_mode),
            horizontal=True
        )

        wrap_code = st.toggle("Wrap long lines for code blocks", value=st.session_state.wrap_code)
        show_previews = st.toggle("Show conversation previews in history", value=st.session_state.show_previews)

        starry_bg = st.session_state.starry_bg
        if theme == "Dark":
            starry_bg = st.toggle("Enable starry background", value=st.session_state.starry_bg)
        else:
            st.caption("Starry background is available in Dark mode.")

        # Apply changes
        changed = (
            theme != st.session_state.theme_mode
            or wrap_code != st.session_state.wrap_code
            or show_previews != st.session_state.show_previews
            or starry_bg != st.session_state.starry_bg
        )

        if changed:
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
                st.image(item["image_url"]["url"])

# Input area (uploader + chat input)
with st.container():
    st.markdown('<div class="ms-uploader">', unsafe_allow_html=True)
    uploaded_image = st.file_uploader(
        "📎 Attach an image (optional)",
        type=["png", "jpg", "jpeg"],
        key=f"uploader_{st.session_state.uploader_counter}",
        label_visibility="visible"
    )
    st.markdown("</div>", unsafe_allow_html=True)

user_prompt = st.chat_input("Type a message and press Enter…")

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

    # Assistant response (streaming)
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

    messages.append({"role": "assistant", "content": [{"type": "text", "text": full_response}]})

    st.session_state.uploader_counter += 1
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
