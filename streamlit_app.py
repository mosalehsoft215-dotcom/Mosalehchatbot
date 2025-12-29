import streamlit as st
import base64
import io
import os
from PIL import Image
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv

# ==========================================================
# 1. CONFIGURATION & SETUP
# ==========================================================
load_dotenv()

st.set_page_config(
    page_title="Pro Chat Workspace",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

def get_groq_api_key() -> str | None:
    """Retrieves API key from Secrets or Environment."""
    try:
        return st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    except Exception:
        return None

# Initialize Client
api_key = get_groq_api_key()
if not api_key:
    st.warning("⚠️ GROQ_API_KEY not detected.")
    st.info("Add it to `.streamlit/secrets.toml` or your `.env` file to proceed.")
    st.stop()

client = Groq(api_key=api_key)

# ==========================================================
# 2. STATE MANAGEMENT
# ==========================================================
if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_chat_id" not in st.session_state:
    new_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.current_chat_id = new_id
    st.session_state.conversations[new_id] = []

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if "model_id" not in st.session_state:
    st.session_state.model_id = "llama-3.2-90b-vision-preview"

# ==========================================================
# 3. PROFESSIONAL STYLING (CSS)
# ==========================================================
def inject_custom_css(theme: str):
    """
    Injects professional CSS based on the selected theme.
    Removes clutter and focuses on typography and spacing.
    """
    if theme == "Dark":
        # Gemini-inspired Dark Theme
        bg_color = "#0e1117"  # Deep dark
        chat_bg = "#161b22"
        text_color = "#e6edf3"
        accent_color = "#2f81f7"
        border_color = "rgba(240, 246, 252, 0.1)"
        user_bubble = "#1f6feb" # Blueish
        ai_bubble = "#161b22"
    else:
        # Clean Professional Light Theme
        bg_color = "#ffffff"
        chat_bg = "#f6f8fa"
        text_color = "#1f2328"
        accent_color = "#0969da"
        border_color = "rgba(31, 35, 40, 0.15)"
        user_bubble = "#ddf4ff" # Light Blue
        ai_bubble = "#f6f8fa"

    css = f"""
    <style>
        /* Main Container Cleanups */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        /* Remove Streamlit Header/Footer clutter */
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        /* Chat Input Styling */
        .stChatInput textarea {{
            background-color: {chat_bg} !important;
            color: {text_color} !important;
            border: 1px solid {border_color} !important;
        }}
        
        /* Message Bubbles */
        div[data-testid="stChatMessage"] {{
            background-color: transparent;
            padding: 1rem;
        }}
        
        div[data-testid="stChatMessage"][data-role="user"] {{
            background-color: transparent;
        }}
        
        /* Sidebar Polish */
        section[data-testid="stSidebar"] {{
            background-color: {chat_bg};
            border-right: 1px solid {border_color};
        }}
        
        /* Headings */
        h1, h2, h3 {{
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            color: {text_color} !important;
        }}
        
        /* Custom Card for Content */
        .pro-card {{
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 20px;
            background-color: {chat_bg};
            margin-bottom: 20px;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_custom_css(st.session_state.theme)

# ==========================================================
# 4. HELPER FUNCTIONS
# ==========================================================
def image_to_base64(uploaded_file) -> str:
    image = Image.open(uploaded_file).convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def create_new_chat():
    new_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.current_chat_id = new_id
    st.session_state.conversations[new_id] = []
    st.rerun()

def delete_chat(chat_id):
    if chat_id in st.session_state.conversations:
        del st.session_state.conversations[chat_id]
    # If we deleted the current one, reset
    if chat_id == st.session_state.current_chat_id:
        create_new_chat()
    else:
        st.rerun()

# ==========================================================
# 5. SIDEBAR (Navigation & Settings)
# ==========================================================
with st.sidebar:
    st.title("🎛️ Controls")
    
    # 5.1 Theme Toggle
    theme_col1, theme_col2 = st.columns(2)
    with theme_col1:
        if st.button("🌑 Dark", use_container_width=True):
            st.session_state.theme = "Dark"
            st.rerun()
    with theme_col2:
        if st.button("☀️ Light", use_container_width=True):
            st.session_state.theme = "Light"
            st.rerun()

    st.markdown("---")
    
    # 5.2 Model Selection (Making it Useful)
    st.subheader("🤖 Model Intelligence")
    model_choice = st.selectbox(
        "Select Model",
        [
            "llama-3.2-90b-vision-preview", # Best for everything + images
            "llama-3.2-11b-vision-preview", # Faster, good for images
            "llama3-70b-8192",              # High intelligence text
            "mixtral-8x7b-32768",           # Good reasoning
        ],
        index=0,
        key="model_selector"
    )
    st.session_state.model_id = model_choice
    
    # 5.3 System Prompt (Enhancing Utility)
    st.subheader("🧠 System Persona")
    system_prompt = st.text_area(
        "Define AI Behavior", 
        value="You are a helpful, professional, and concise AI assistant.",
        height=100
    )

    st.markdown("---")

    # 5.4 Chat History
    st.subheader("💬 History")
    if st.button("➕ New Conversation", use_container_width=True):
        create_new_chat()
    
    # List recent chats
    chat_ids = list(st.session_state.conversations.keys())
    for c_id in reversed(chat_ids[-10:]): # Show last 10
        col_lbl, col_del = st.columns([0.8, 0.2])
        label = f"Chat {c_id[9:14]}" # Simple timestamp label
        
        # Highlight active
        btn_type = "primary" if c_id == st.session_state.current_chat_id else "secondary"
        
        if col_lbl.button(f"📄 {label}", key=f"sel_{c_id}", type=btn_type, use_container_width=True):
            st.session_state.current_chat_id = c_id
            st.rerun()
        
        if col_del.button("✖", key=f"del_{c_id}", help="Delete"):
            delete_chat(c_id)

# ==========================================================
# 6. MAIN CHAT INTERFACE
# ==========================================================

# 6.1 Header
st.title("M‑Saleh Professional AI")
st.caption(f"Powered by **{st.session_state.model_id}** • Secure & Private")

# 6.2 Chat Container
current_messages = st.session_state.conversations[st.session_state.current_chat_id]

for msg in current_messages:
    with st.chat_message(msg["role"]):
        for item in msg["content"]:
            if item["type"] == "text":
                st.markdown(item["text"])
            elif item["type"] == "image_url":
                st.image(item["image_url"]["url"], width=300)

# 6.3 Input Area (Image + Text)
with st.container():
    # Integrated Image Uploader (Collapsible to save space)
    with st.popover("📎 Attach Image", use_container_width=True):
        uploaded_image = st.file_uploader(
            "Upload an image for analysis", 
            type=["png", "jpg", "jpeg"],
            key=f"img_{len(current_messages)}"
        )
    
    # Chat Input
    user_input = st.chat_input("Message M-Saleh AI...")

# ==========================================================
# 7. LOGIC & STREAMING
# ==========================================================
if user_input:
    # 7.1 Construct User Message Payload
    user_content = [{"type": "text", "text": user_input}]
    
    if uploaded_image:
        # Verify model supports vision
        if "vision" not in st.session_state.model_id:
            st.toast("⚠️ Switching to Vision model for image analysis...", icon="🔄")
            st.session_state.model_id = "llama-3.2-90b-vision-preview"
            
        b64_img = image_to_base64(uploaded_image)
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64_img}"}
        })

    # Add to state
    st.session_state.conversations[st.session_state.current_chat_id].append(
        {"role": "user", "content": user_content}
    )
    
    # Rerun to show user message immediately
    st.rerun()

# Trigger Assistant Response (after rerun)
if current_messages and current_messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # Prepare messages for API (System + History)
            api_messages = [{"role": "system", "content": system_prompt}]
            
            # Add history (sanitize for API)
            for m in current_messages:
                api_messages.append(m)

            stream = client.chat.completions.create(
                model=st.session_state.model_id,
                messages=api_messages,
                temperature=0.6,
                max_completion_tokens=2048,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            
            # Save assistant response
            st.session_state.conversations[st.session_state.current_chat_id].append(
                {"role": "assistant", "content": [{"type": "text", "text": full_response}]}
            )
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
