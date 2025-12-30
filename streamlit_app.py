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

# Updated CSS (includes improved visual fixes)
def build_updated_css(allow_starry: bool, bg_img_b64: str | None) -> str:
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

    /* Force readable text everywhere */
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

    /* Chat message bubbles */
    div[data-testid="stChatMessage"] {{
      padding: 0.35rem 0.25rem;
    }}

    .stChatMessageContent {{
      border-radius: 16px !important;
      padding: 0.65rem 0.85rem !important;
      border: 1px solid var(--ms-border) !important;
      background: var(--ms-assistant-bg);
    }}

    /* User vs Assistant Bubbles */
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

    /* Hide the unnecessary border */
    .stApp {{
      border: none;
    }}

    /* Reduce Streamlit default top padding a bit */
    header[data-testid="stHeader"] {{
      background: transparent;
    }}
    """

def apply_updated_ui(theme_mode: str, starry_bg: bool, wrap_code: bool) -> None:
    # Apply updated UI with cleaner visuals
    updated_LIGHT = {
        "bg": "#F6F7FB",
        "bg2": "radial-gradient(900px 520px at 20% 0%, rgba(99,102,241,0.14), transparent 55%),"
               "radial-gradient(800px 460px at 95% 10%, rgba(236,72,153,0.12), transparent 55%)",
        "card": "rgba(255,255,255,0.92)",
        "border": "rgba(15,23,42,0.06)",
        "text": "#0B1220",
        "muted": "rgba(11,18,32,0.65)",
        "user_bg": "rgba(99,102,241,0.16)",
        "assistant_bg": "rgba(2,6,23,0.04)",
        "input_bg": "rgba(255,255,255,0.95)",
        "code_bg": "rgba(2,6,23,0.06)",
    }

    updated_DARK = {
        "bg": "#070A12",
        "bg2": "radial-gradient(1200px 700px at 20% 5%, rgba(120,130,255,0.20), transparent 60%),"
               "radial-gradient(900px 520px at 90% 15%, rgba(255,90,160,0.14), transparent 55%)",
        "card": "rgba(17,24,39,0.74)",
        "border": "rgba(255,255,255,0.12)",
        "text": "#EAF0FF",
        "muted": "rgba(234,240,255,0.75)",
        "user_bg": "rgba(99,102,241,0.24)",
        "assistant_bg": "rgba(255,255,255,0.06)",
        "input_bg": "rgba(17,24,39,0.88)",
        "code_bg": "rgba(255,255,255,0.08)",
    }
    # Apply for Light/Dark mode
    P = updated_DARK if theme_mode == "Dark" else updated_LIGHT

    # Update background image handling for dark mode starry effect
    bg_img_b64 = None
    allow_starry = False
    if theme_mode == "Dark" and starry_bg:
        p1 = Path(__file__).parent / "assets" / "space_bg.png"
        p2 = Path(__file__).parent / "space_bg.png"
        bg_img_b64 = load_file_b64(p1) or load_file_b64(p2)
        allow_starry = bg_img_b64 is not None

    # Generate and apply updated CSS
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

      {build_updated_css(allow_starry=allow_starry, bg_img_b64=bg_img_b64)}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
