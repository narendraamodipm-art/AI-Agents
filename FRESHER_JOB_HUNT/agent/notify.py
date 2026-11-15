"""Sending: Telegram (channel + admin)."""

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


def remove_member(chat_id, user_id):
    """Remove someone from a channel. Unbanning straight away lets them rejoin if they subscribe again."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    for method, extra in (("banChatMember", {}), ("unbanChatMember", {"only_if_banned": True})):
        r = requests.post(f"https://api.telegram.org/bot{token}/{method}", timeout=30,
                          json={"chat_id": chat_id, "user_id": user_id, **extra})
        if not r.ok:
            raise RuntimeError(f"Telegram {method} {user_id}: {r.status_code} {r.text[:200]}")


def telegram(chat_id, text, html=True, buttons=None):
    """Send a message (split if too long). `buttons` = inline keyboard rows, put on the last part.
    Returns the sent message IDs."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    parts, ids = split_message(text), []
    for i, part in enumerate(parts):
        extra = {"reply_markup": {"inline_keyboard": buttons}} if buttons and i == len(parts) - 1 else {}
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=30, json={
            "chat_id": chat_id, "text": part, "disable_web_page_preview": True,
            **({"parse_mode": "HTML"} if html else {}), **extra})
        if not r.ok:
            raise RuntimeError(f"Telegram {chat_id}: {r.status_code} {r.text[:200]}")
        ids.append(r.json()["result"]["message_id"])
    return ids


def delete(chat_id, message_id):
    """Delete one channel message. Returns True if it's gone (including if it was already deleted)."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    r = requests.post(f"https://api.telegram.org/bot{token}/deleteMessage", timeout=30,
                      json={"chat_id": chat_id, "message_id": message_id})
    if r.ok or "not found" in r.text.lower():
        return True
    raise RuntimeError(f"Telegram delete {message_id}: {r.status_code} {r.text[:200]}")
