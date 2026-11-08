import { TELEGRAM_URL, WHATSAPP_URL } from "@/lib/links";

export default function JoinButtons() {
  if (!TELEGRAM_URL && !WHATSAPP_URL) return null;
  return (
    <div className="join">
      {TELEGRAM_URL && (
        <a className="btn telegram" href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer">
          ✈️ Join on Telegram
        </a>
      )}
      {WHATSAPP_URL && (
        <a className="btn whatsapp" href={WHATSAPP_URL} target="_blank" rel="noopener noreferrer">
          💬 Join WhatsApp group
        </a>
      )}
    </div>
  );
}
