import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy | Fresher Job Hunt" };

export default function Privacy() {
  return (
    <section className="section narrow prose">
      <h1 className="page-title">Privacy policy</h1>
      <p className="muted">Last updated: 8 November 2026</p>

      <h2>What we collect</h2>
      <p>
        When you sign up we store your <strong>name</strong>, <strong>email address</strong>, the{" "}
        <strong>job fields</strong> and <strong>work type</strong> you picked, whether you want email alerts, and the time
        you gave consent.
      </p>

      <h2>Why</h2>
      <p>Only to send you daily job alerts that match your choices. We don&apos;t sell, rent or share your data.</p>

      <h2>Where it&apos;s stored</h2>
      <p>
        In a private database (Supabase) that only our server can access. Emails are sent through an email delivery
        provider. If you join our Telegram channel or WhatsApp group, those apps&apos; own privacy policies apply there.
      </p>

      <h2>Your choices</h2>
      <ul>
        <li>Every email has an unsubscribe link that stops emails immediately.</li>
        <li>
          To delete your data completely, email us from the address you signed up with and we&apos;ll remove it within 7
          days.
        </li>
      </ul>

      <h2>Job listings</h2>
      <p>
        Jobs link to each company&apos;s own career page or job board. We don&apos;t charge for applying, and we never
        ask for money. If anyone asks you to pay for a job, it&apos;s a scam.
      </p>
    </section>
  );
}
