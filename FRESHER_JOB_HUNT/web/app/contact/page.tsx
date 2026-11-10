import type { Metadata } from "next";
import { BOT_USERNAME, SUPPORT_EMAIL } from "@/lib/contact";

export const metadata: Metadata = { title: "Contact | JOB HUNTER" };

export default function Contact() {
  return (
    <section className="section narrow prose">
      <h1 className="page-title">Contact us</h1>

      <h2>Email</h2>
      <p>
        For payments, access or anything else: <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>
      </p>
      <p className="muted">For payment questions, include the email or phone number you paid with.</p>

      <h2>Telegram</h2>
      <p>
        Our bot{" "}
        <a href={`https://t.me/${BOT_USERNAME}`} target="_blank" rel="noopener noreferrer">
          @{BOT_USERNAME}
        </a>{" "}
        handles joining the channel. Send <strong>/cancel</strong> to it to stop your subscription.
      </p>
    </section>
  );
}
