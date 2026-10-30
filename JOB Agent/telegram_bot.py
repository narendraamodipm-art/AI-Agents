"""Send Telegram messages and read your replies through a Telegram bot (free, no limits).

JOB Agent/.env needs:
    TELEGRAM_BOT_TOKEN=123456:ABC...     (from @BotFather → /newbot)
    TELEGRAM_CHAT_ID=987654321           (your chat with the bot; `python agent.py chat-id` finds it)

Only messages from TELEGRAM_CHAT_ID are acted on — anyone can message a bot, so others are ignored.
"""

import json
import os
import urllib.request

MAX_CHARS = 4000          # Telegram's limit is 4,096 characters per message


def configured() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


def api(method: str, http_timeout=30, **params):
    url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/{method}"
    req = urllib.request.Request(url, data=json.dumps(params).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=http_timeout) as r:
        return json.loads(r.read())["result"]


def split(text: str) -> list[str]:
    """Split between blank-line blocks into chunks under MAX_CHARS (keeps HTML tags whole)."""
    chunks, current = [], ""
    for block in text.split("\n\n"):
        if len(current) + len(block) + 2 > MAX_CHARS and current:
            chunks.append(current)
            current = ""
        current += block + "\n\n"
    return chunks + [current] if current.strip() else chunks


def send(text: str, log=print) -> bool:
    """Send an HTML-formatted message (<b>, <i>, <code>, <a href>, <blockquote>)."""
    if not configured():
        log("Telegram not configured — message not sent:\n" + text)
        return False
    for chunk in split(text):
        api("sendMessage", chat_id=os.environ["TELEGRAM_CHAT_ID"], text=chunk.strip(), parse_mode="HTML",
            link_preview_options={"is_disabled": True})
    return True


def updates(wait=0) -> list[dict]:
    """Messages sent to the bot that Telegram still holds (up to 24 h). wait > 0 long-polls."""
    return [u for u in api("getUpdates", http_timeout=wait + 10, timeout=wait) if "message" in u]


def recent_replies(wait=0) -> list[tuple[str, str]]:
    """(update id, text) of your messages to the bot, oldest first; confirms them to Telegram."""
    if not configured():
        return []
    mine = os.environ["TELEGRAM_CHAT_ID"]
    ups = updates(wait)
    if ups:
        api("getUpdates", offset=ups[-1]["update_id"] + 1, timeout=0)   # don't deliver these again
    return [(str(u["update_id"]), u["message"].get("text", "")) for u in ups
            if str(u["message"]["chat"]["id"]) == mine]


def find_chat_ids() -> list[tuple[str, str]]:
    """(chat id, name) of everyone who has messaged the bot recently — to fill in TELEGRAM_CHAT_ID."""
    seen = {}
    for u in updates():
        chat = u["message"]["chat"]
        seen[str(chat["id"])] = chat.get("username") or chat.get("first_name", "")
    return list(seen.items())
