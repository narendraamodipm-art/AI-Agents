import { TELEGRAM_URL } from "@/lib/links";

export default function JoinButtons() {
  return (
    <div className="join">
      <a className="btn telegram" href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer">
        ✈️ Join on Telegram
      </a>
    </div>
  );
}
