# M‑Saleh Chatbot 🝪🤖

A modern **Streamlit** multi‑chat chatbot with optional **image input** (vision) using **Groq** LLMs.

## Features
- Multi‑conversation chat history (sidebar)
- Optional image attachment (PNG/JPG/JPEG)
- Streaming assistant responses
- Built‑in **Settings** (Light / Dark / System + starry background in Dark mode)
- No API keys stored in code (uses Secrets / .env)

## Run locally

1) Install dependencies:
```bash
pip install -r requirements.txt
```

2) Create a `.env` file (do **not** push to GitHub):
```env
GROQ_API_KEY=your_groq_api_key_here
```

3) Start the app:
```bash
streamlit run streamlit_app.py
```

## Deploy (Streamlit Community Cloud)

1) Deploy from this GitHub repo.
2) In your app settings → **Secrets**, add:
```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

## Notes
- The dark “starry” background image is in `assets/space_bg.png` (you can replace it with any image you like).
- Never commit real API keys. `.gitignore` already blocks `.env`.
