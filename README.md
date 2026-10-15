# HahaBot

HahaBot is a Streamlit chat app powered by Mistral AI.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create an app
   from the repository and select `CHATBOT/CHATBOT_APP.py` as the main file.
3. Open the app's **Settings > Secrets** and add your Mistral API key in TOML
   format:

   ```toml
   MISTRAL_API_KEY = "your-mistral-api-key"
   ```

4. Save the secret and deploy the app.

Dependencies are listed in the repository-root `requirements.txt`. Do not
commit API keys; `.env` and local Streamlit secrets files are ignored by Git.
