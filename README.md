# AI-Agents Streamlit Apps

This repository contains two Streamlit apps: HahaBot, a Mistral-powered
chatbot, and DocChat AI, a RAG app that answers questions about uploaded PDFs
or webpages using Mistral AI and Pinecone.

## Deploy on Streamlit Community Cloud...

Push this repository to GitHub, then create a separate app for each interface
in [Streamlit Community Cloud](https://share.streamlit.io/). For each app,
select this repository and the `main` branch, then choose its main file:

- HahaBot: `CHATBOT/CHATBOT_APP.py`
- DocChat AI (RAG): `RAG/RAG.py`

After creating each app, open **Settings > Secrets**, add the required secrets
in TOML format, and save. Keep API keys out of the source code and GitHub.

HahaBot requires:

```toml
MISTRAL_API_KEY = "your-mistral-api-key"
```

DocChat AI requires both:

```toml
MISTRAL_API_KEY = "your-mistral-api-key"
PINECONE_API_KEY = "your-pinecone-api-key"
```

The RAG app connects to the Pinecone index configured in `RAG/RAG.py`. Its
document processing replaces the contents of the app's configured `RAG`
namespace, so processing a new document removes previously indexed content in
that namespace.

Dependencies for both apps are listed in the repository-root
`requirements.txt`. For local development, use a `.env` file; `.env` and local
Streamlit secrets files are ignored by Git.
