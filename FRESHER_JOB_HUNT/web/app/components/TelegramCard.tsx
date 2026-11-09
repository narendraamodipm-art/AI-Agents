import { TELEGRAM_URL } from "@/lib/links";
import TelegramLink from "./TelegramLink";

export default function TelegramCard() {
  return (
    <div className="card tg-card">
      <span className="tg-icon" aria-hidden="true">
        ✈️
      </span>
      <h3>Free channel</h3>
      <p>Join free on Telegram for a sample of each day&apos;s jobs. No signup needed.</p>
      <TelegramLink className="btn telegram block">Join the free channel</TelegramLink>
      <p className="tg-link">{TELEGRAM_URL.replace("https://", "")}</p>
    </div>
  );
}
