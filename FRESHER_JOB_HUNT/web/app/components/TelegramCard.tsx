import { TELEGRAM_URL } from "@/lib/links";
import TelegramLink from "./TelegramLink";

export default function TelegramCard() {
  return (
    <div className="card tg-card">
      <span className="tg-icon" aria-hidden="true">
        ✈️
      </span>
      <h3>Get job links on Telegram</h3>
      <p>Join the channel and new jobs reach you every day at 10 AM IST. No signup, no forms, completely free.</p>
      <ul>
        <li>10–12 jobs per experience level</li>
        <li>Direct links to company apply pages</li>
        <li>Leave any time with one tap</li>
      </ul>
      <TelegramLink className="btn telegram block">Join the Telegram channel</TelegramLink>
      <p className="tg-link">{TELEGRAM_URL.replace("https://", "")}</p>
    </div>
  );
}
