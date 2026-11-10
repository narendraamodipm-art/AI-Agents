import type { Metadata } from "next";
import { BOT_USERNAME, POLICY_DATE, SUPPORT_EMAIL } from "@/lib/contact";

export const metadata: Metadata = { title: "Cancellation & Refunds | JOB HUNTER" };

export default function Refunds() {
  return (
    <section className="section narrow prose">
      <h1 className="page-title">Cancellation &amp; Refunds</h1>
      <p className="muted">Last updated: {POLICY_DATE}</p>

      <h2>Cancelling</h2>
      <ul>
        <li>
          Cancel any time by sending <strong>/cancel</strong> to{" "}
          <a href={`https://t.me/${BOT_USERNAME}`} target="_blank" rel="noopener noreferrer">
            @{BOT_USERNAME}
          </a>{" "}
          on Telegram, then confirming.
        </li>
        <li>You won&apos;t be charged again after cancelling.</li>
        <li>You keep access to the channel until the end of the month you&apos;ve already paid for.</li>
      </ul>

      <h2>Refunds</h2>
      <ul>
        <li>
          <strong>Payments are non-refundable</strong>, including for months that are partly used.
        </li>
        <li>
          If you were charged twice or charged by mistake, email us with your payment details and we&apos;ll refund the
          extra charge.
        </li>
      </ul>

      <h2>Contact</h2>
      <p>
        Email <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>.
      </p>
    </section>
  );
}
