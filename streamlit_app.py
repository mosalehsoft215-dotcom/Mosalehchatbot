import streamlit as st
import base64
from groq import Groq
from datetime import datetime
import os
from dotenv import load_dotenv

# 1. SETUP & CONFIG
# =========================================================
load_dotenv()
st.set_page_config(page_title="M-Saleh Chat", page_icon="🤖", layout="centered")

# Get API Key safely
api_key = os.getenv("GROQ_API_KEY")
if not api_key and "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]

if not api_key:
    st.error("⚠️ Missing API Key. Please add GROQ_API_KEY to your .env or secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. SESSION STATE (Memory)
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "model" not in st.session_state:
    st.session_state.model = "llama-3.3-70b-versatile" # Default Text Model

# 3. HELPER FUNCTIONS
# =========================================================
def process_image(uploaded_file):
    """Encodes image to base64 for the API"""
    try:
        return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

# 4. SIDEBAR (Settings)
# =========================================================
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Model Selector
    model_option = st.selectbox(
        "Choose AI Model:",
        (
            "llama-3.3-70b-versatile",          # Best for Text (Fast & Smart)
            "meta-llama/llama-4-maverick-17b-128e-instruct", # Best for Images
            "mixtral-8x7b-32768"                # Good Alternative
        ),
        index=0
    )
    st.session_state.model = model_option
    
    st.divider()
    
    # Clear Chat Button
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.caption("Tip: Use 'Llama 4 Maverick' if you upload images.")

# 5. MAIN CHAT INTERFACE
# =========================================================
st.title("🤖 M-Saleh Chatbot")
st.caption("Simple, Fast, and Powerful.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Check if content is a list (multimodal/image) or string (text)
        if isinstance(message["content"], list):
            for item in message["content"]:
                if item["type"] == "text":
                    st.markdown(item["text"])
                elif item["type"] == "image_url":
                    st.image(item["image_url"]["url"], width=250)
        else:
            st.markdown(message["content"])

# 6. INPUT AREA
# =========================================================
# Image Uploader (Optional)
with st.expander("📷 Upload Image (Optional)"):
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Chat Input
if prompt := st.chat_input("Type your message..."):
    
    # Prepare User Message
    user_message_content = []
    
    # 1. Add Text
    user_message_content.append({"type": "text", "text": prompt})
    
    # 2. Add Image (if uploaded)
    if uploaded_file:
        base64_image = process_image(uploaded_file)
        if base64_image:
            # Force switch to Vision Model if not selected
            if "llama-4" not in st.session_state.model:
                st.session_state.model = "meta-llama/llama-4-maverick-17b-128e-instruct"
                st.toast("Switched to Llama 4 (Vision) for image support.", icon="👁️")
            
            user_message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })

    # Add to History (UI)
    st.session_state.messages.append({"role": "user", "content": user_message_content})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file:
            st.image(uploaded_file, width=250)

    # Generate Response
    with st.chat_message("assistant"):
        stream_container = st.empty()
        full_response = ""
        
        try:
            # Call Groq API
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                model=st.session_state.model,
                stream=True,
            )

            # Stream the response
            for chunk in chat_completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    stream_container.markdown(full_response + "▌")
            
            stream_container.markdown(full_response)
            
            # Save to History
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            error_msg = str(e)
            if "model_decommissioned" in error_msg:
                st.error("❌ The selected model is outdated. Please switch to 'Llama 3.3' in the sidebar.")
            else:
                st.error(f"Error: {error_msg}")
