"""Sending: Telegram (channel + admin) and optional email via Resend."""

import os

import requests

TG_LIMIT = 4096


def split_message(text, limit=TG_LIMIT):
    """Split on blank lines / line breaks so each part fits Telegram's 4,096-character limit."""
    parts, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > limit:
            parts.append(current.rstrip())
            current = ""
        current += line + "\n"
    if current.strip():
        parts.append(current.rstrip())
    return parts


def telegram(chat_id, text, html=True):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    for part in split_message(text):
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=30, json={
            "chat_id": chat_id, "text": part, "disable_web_page_preview": True,
            **({"parse_mode": "HTML"} if html else {})})
        if not r.ok:
            raise RuntimeError(f"Telegram {chat_id}: {r.status_code} {r.text[:200]}")


def email(to, subject, html_body, unsubscribe_url):
    r = requests.post("https://api.resend.com/emails", timeout=30,
                      headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                      json={"from": os.environ["EMAIL_FROM"], "to": [to], "subject": subject, "html": html_body,
                            "headers": {"List-Unsubscribe": f"<{unsubscribe_url}>"}})
    if not r.ok:
        raise RuntimeError(f"Resend {to}: {r.status_code} {r.text[:200]}")
