const TELEGRAM = process.env.NEXT_PUBLIC_TELEGRAM_URL;
const WHATSAPP = process.env.NEXT_PUBLIC_WHATSAPP_GROUP_URL;

export default function JoinButtons() {
  if (!TELEGRAM && !WHATSAPP) return null;
  return (
    <div className="join">
      {TELEGRAM && (
        <a className="btn telegram" href={TELEGRAM} target="_blank" rel="noopener noreferrer">
          ✈️ Join on Telegram
        </a>
      )}
      {WHATSAPP && (
        <a className="btn whatsapp" href={WHATSAPP} target="_blank" rel="noopener noreferrer">
          💬 Join WhatsApp group
        </a>
      )}
    </div>
  );
}
