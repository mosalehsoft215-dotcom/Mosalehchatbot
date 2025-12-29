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
@st.cache_data(show_spinner=False)
def _read_file_b64(path_str: str) -> str | None:
    try:
        data = Path(path_str).read_bytes()
        return base64.b64encode(data).decode("utf-8")
    except Exception:
        return None

def load_file_b64(path: Path) -> str | None:
    """Read a local file and return base64 (cached)."""
    return _read_file_b64(str(path))

def build_global_css(allow_starry: bool, bg_img_b64: str | None) -> str:
    # Background CSS (kept as plain strings to avoid escaping issues)
    if allow_starry and bg_img_b64:
        bg_css = f"""
        background-color: var(--ms-bg);
        background-image: var(--ms-bg2), url("data:image/png;base64,{bg_img_b64}");
        background-size: auto, cover;
        background-position: center, center;
        background-attachment: fixed;
        """
    else:
        bg_css = """
        background-color: var(--ms-bg);
        background-image: var(--ms-bg2);
        background-attachment: fixed;
        """

    return f"""
    /* Page background + base typography */
    .stApp {{
      {bg_css}
      color: var(--ms-text) !important;
      font-family: var(--ms-font);
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}

    /* Force readable text everywhere (Streamlit sometimes keeps light-theme colors) */
    .stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stApp div {{
      color: var(--ms-text);
    }}
    .stCaption, .stMarkdown small {{
      color: var(--ms-muted) !important;
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
      color: var(--ms-text);
    }}
    .ms-subtitle {{
      font-size: 0.92rem;
      color: var(--ms-muted);
      margin-top: -2px;
    }}

    /* Chat "card" */
    .ms-card {{
      background: var(--ms-card);
      border: 1px solid var(--ms-border);
      border-radius: 20px;
      padding: 14px 14px 10px 14px;
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      box-shadow: 0 10px 28px rgba(0,0,0,0.18);
    }}

    /* Chat message bubbles (Streamlit structure: .stChatMessageContent) */
    div[data-testid="stChatMessage"] {{
      padding: 0.35rem 0.25rem;
    }}

    .stChatMessageContent {{
      border-radius: 16px !important;
      padding: 0.65rem 0.85rem !important;
      border: 1px solid var(--ms-border) !important;
      background: var(--ms-assistant-bg);
    }}

    /* Role-based bubbles (works on recent Streamlit versions) */
    div[data-testid="stChatMessage"][aria-label*="user"] .stChatMessageContent {{
      background: var(--ms-user-bg) !important;
    }}
    div[data-testid="stChatMessage"][aria-label*="assistant"] .stChatMessageContent {{
      background: var(--ms-assistant-bg) !important;
    }}

    /* Code blocks */
    pre {{
      background: var(--ms-code-bg) !important;
      border: 1px solid var(--ms-border) !important;
      border-radius: 14px !important;
      padding: 0.85rem !important;
    }}

    /* Chat input */
    div[data-testid="stChatInput"] textarea {{
      background: var(--ms-input-bg) !important;
      color: var(--ms-text) !important;
      border-radius: 16px !important;
      border: 1px solid var(--ms-border) !important;
    }}
    div[data-testid="stChatInput"] textarea::placeholder {{
      color: var(--ms-muted) !important;
    }}
    div[data-testid="stChatInput"] {{
      padding-top: 0.5rem;
    }}

    /* File uploader */
    div[data-testid="stFileUploaderDropzone"] {{
      background: var(--ms-input-bg) !important;
      border: 1px dashed var(--ms-border) !important;
      border-radius: 16px !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
      background: var(--ms-card) !important;
      border-right: 1px solid var(--ms-border) !important;
    }}
    [data-testid="stSidebar"] > div {{
      padding-top: 1.0rem;
    }}

    /* Buttons */
    .stButton > button {{
      background: var(--ms-input-bg) !important;
      color: var(--ms-text) !important;
      border: 1px solid var(--ms-border) !important;
      border-radius: 14px !important;
      padding: 0.55rem 0.8rem !important;
    }}
    .stButton > button:hover {{
      filter: brightness(1.03);
    }}

    /* Reduce Streamlit default top padding a bit */
    header[data-testid="stHeader"] {{
      background: transparent;
    }}
    """

def apply_ui(theme_mode: str, starry_bg: bool, wrap_code: bool) -> None:
    """
    Light/Dark/System runtime theme via CSS variables.
    Fixes dark-mode readability (global text color + correct chat selectors).
    """
    LIGHT = {
        "bg": "#F6F7FB",
        "bg2": "radial-gradient(900px 520px at 20% 0%, rgba(99,102,241,0.14), transparent 55%),"
               "radial-gradient(800px 460px at 95% 10%, rgba(236,72,153,0.12), transparent 55%)",
        "card": "rgba(255,255,255,0.86)",
        "border": "rgba(15,23,42,0.10)",
        "text": "#0B1220",
        "muted": "rgba(11,18,32,0.62)",
        "user_bg": "rgba(99,102,241,0.16)",
        "assistant_bg": "rgba(2,6,23,0.04)",
        "input_bg": "rgba(255,255,255,0.92)",
        "code_bg": "rgba(2,6,23,0.06)",
    }
    DARK = {
        "bg": "#070A12",
        "bg2": "radial-gradient(1200px 700px at 20% 5%, rgba(120,130,255,0.20), transparent 60%),"
               "radial-gradient(900px 520px at 90% 15%, rgba(255,90,160,0.14), transparent 55%)",
        "card": "rgba(17,24,39,0.74)",
        "border": "rgba(255,255,255,0.12)",
        "text": "#EAF0FF",
        "muted": "rgba(234,240,255,0.70)",
        "user_bg": "rgba(99,102,241,0.24)",
        "assistant_bg": "rgba(255,255,255,0.06)",
        "input_bg": "rgba(17,24,39,0.88)",
        "code_bg": "rgba(255,255,255,0.08)",
    }

    code_wrap_css = ""
    if wrap_code:
        code_wrap_css = "pre code { white-space: pre-wrap !important; word-break: break-word !important; }"

    # In System mode we follow the OS theme using prefers-color-scheme
    if theme_mode == "System":
        css = f"""
        <style>
          :root {{
            --ms-font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
          }}

          /* Light defaults */
          .stApp {{
            --ms-bg: {LIGHT["bg"]};
            --ms-bg2: {LIGHT["bg2"]};
            --ms-card: {LIGHT["card"]};
            --ms-border: {LIGHT["border"]};
            --ms-text: {LIGHT["text"]};
            --ms-muted: {LIGHT["muted"]};
            --ms-user-bg: {LIGHT["user_bg"]};
            --ms-assistant-bg: {LIGHT["assistant_bg"]};
            --ms-input-bg: {LIGHT["input_bg"]};
            --ms-code-bg: {LIGHT["code_bg"]};
          }}

          @media (prefers-color-scheme: dark) {{
            .stApp {{
              --ms-bg: {DARK["bg"]};
              --ms-bg2: {DARK["bg2"]};
              --ms-card: {DARK["card"]};
              --ms-border: {DARK["border"]};
              --ms-text: {DARK["text"]};
              --ms-muted: {DARK["muted"]};
              --ms-user-bg: {DARK["user_bg"]};
              --ms-assistant-bg: {DARK["assistant_bg"]};
              --ms-input-bg: {DARK["input_bg"]};
              --ms-code-bg: {DARK["code_bg"]};
            }}
          }}

          {code_wrap_css}
          {build_global_css(allow_starry=False, bg_img_b64=None)}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
        return

    # Light/Dark explicit
    P = DARK if theme_mode == "Dark" else LIGHT

    # Starry background only in Dark mode (and only if file exists)
    bg_img_b64 = None
    allow_starry = False
    if theme_mode == "Dark" and starry_bg:
        # prefer assets/space_bg.png, fallback to ./space_bg.png (older repo layout)
        p1 = Path(__file__).parent / "assets" / "space_bg.png"
        p2 = Path(__file__).parent / "space_bg.png"
        bg_img_b64 = load_file_b64(p1) or load_file_b64(p2)
        allow_starry = bg_img_b64 is not None

    css = f"""
    <style>
      :root {{
        --ms-font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
      }}

      .stApp {{
        --ms-bg: {P["bg"]};
        --ms-bg2: {P["bg2"]};
        --ms-card: {P["card"]};
        --ms-border: {P["border"]};
        --ms-text: {P["text"]};
        --ms-muted: {P["muted"]};
        --ms-user-bg: {P["user_bg"]};
        --ms-assistant-bg: {P["assistant_bg"]};
        --ms-input-bg: {P["input_bg"]};
        --ms-code-bg: {P["code_bg"]};
      }}

      {code_wrap_css}
      {build_global_css(allow_starry=allow_starry, bg_img_b64=bg_img_b64)}
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
