import type { Metadata } from "next";
import Link from "next/link";
import { BOT_USERNAME, POLICY_DATE, SUPPORT_EMAIL } from "@/lib/contact";
import { PAYMENTS_OPEN } from "@/lib/flags";

export const metadata: Metadata = { title: "Terms | JOB HUNTER" };

export default function Terms() {
  return (
    <section className="section narrow prose">
      <h1 className="page-title">Terms of service</h1>
      <p className="muted">Last updated: {POLICY_DATE}</p>
      {!PAYMENTS_OPEN && (
        <p className="card slim">Premium subscriptions aren&apos;t open yet. These terms apply once they open.</p>
      )}

      <h2>What you get</h2>
      <p>
        JOB HUNTER Premium gives you access to a private Telegram channel where we post a daily list of tech job
        openings in India, grouped by experience level. The list is collected automatically from company career pages
        and job boards.
      </p>

      <h2>Price and renewal</h2>
      <p>
        Premium costs <strong>₹99 per month</strong>. Your subscription renews automatically every month through
        Razorpay until you cancel. Payments are processed by Razorpay; we never see or store your card or UPI details.
      </p>

      <h2>Cancelling</h2>
      <p>
        You can cancel any time by sending <strong>/cancel</strong> to our Telegram bot{" "}
        <a href={`https://t.me/${BOT_USERNAME}`} target="_blank" rel="noopener noreferrer">
          @{BOT_USERNAME}
        </a>
        . You won&apos;t be charged again, and you keep access until the end of the month you&apos;ve paid for. See our{" "}
        <Link href="/refunds">Cancellation &amp; Refunds</Link> policy.
      </p>

      <h2>Access</h2>
      <p>
        Your subscription is for one Telegram account. Please don&apos;t share the channel or forward its posts.
        If a subscription ends or a payment fails, access to the channel is removed.
      </p>

      <h2>About the jobs</h2>
      <ul>
        <li>Jobs link to other companies&apos; websites. We don&apos;t control those sites or the hiring process.</li>
        <li>
          We filter listings carefully, but we can&apos;t guarantee every listing is accurate, still open, or right for
          you. Always check details on the company&apos;s own page before applying.
        </li>
        <li>We don&apos;t promise interviews or jobs, and we never charge you to apply for a job.</li>
      </ul>

      <h2>Changes</h2>
      <p>
        We may update these terms or the price. If the price changes, we&apos;ll tell subscribers in advance, and you can
        cancel before it applies.
      </p>

      <h2>Contact</h2>
      <p>
        Questions? Email <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>.
      </p>
    </section>
  );
}
