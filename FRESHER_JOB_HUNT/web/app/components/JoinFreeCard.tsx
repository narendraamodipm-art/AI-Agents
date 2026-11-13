import { FREE_JOIN_URL } from "@/lib/contact";

/** Shown instead of the Subscribe card while payments are off: the channel is free to join. */
export default function JoinFreeCard() {
  return (
    <div className="card tg-card premium">
      <h3>Join free on Telegram</h3>
      <p>Get every job, every day at 10 AM IST, in our Telegram channel. No signup and no payment.</p>
      <ul>
        <li>Up to 12 jobs per experience level, daily</li>
        <li>Fresher to 6+ years, across AI, data and software roles</li>
        <li>Direct links to company apply pages</li>
      </ul>
      <a className="btn telegram block" href={FREE_JOIN_URL} target="_blank" rel="noopener noreferrer">
        ✈️ Join the channel free
      </a>
    </div>
  );
}
