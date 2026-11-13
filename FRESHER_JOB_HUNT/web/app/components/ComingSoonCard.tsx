import { SUPPORT_EMAIL } from "@/lib/contact";

/** Shown instead of the Subscribe card while payments are paused. */
export default function ComingSoonCard() {
  return (
    <div className="card tg-card premium">
      <h3>Premium is coming soon</h3>
      <p>
        We&apos;re setting up payments for our private Telegram channel with every job, every day. Subscriptions
        aren&apos;t open yet.
      </p>
      <ul>
        <li>Up to 12 jobs per experience level, daily</li>
        <li>Fresher to 6+ years, across AI, data and software roles</li>
      </ul>
      <p className="fine">
        Questions? <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>
      </p>
    </div>
  );
}
