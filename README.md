# M-Saleh Chatbot Model 🤖

Streamlit multi-chat chatbot with optional image input (vision) using Groq LLMs.

## Run locally

1) Install dependencies:
```bash
pip install -r requirements.txt
```

2) Create `.env` (DO NOT push to GitHub):
```env
GROQ_API_KEY=your_groq_api_key_here
```

3) Start the app:
```bash
streamlit run streamlit_app.py
```

## Deploy (Streamlit Community Cloud)

1) Create the app from this repo.
2) In the app settings → **Secrets**, add:
```toml
GROQ_API_KEY="your_groq_api_key_here"
```
