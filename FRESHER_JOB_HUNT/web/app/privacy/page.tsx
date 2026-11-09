import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy | JOB HUNTER" };

export default function Privacy() {
  return (
    <section className="section narrow prose">
      <h1 className="page-title">Privacy policy</h1>
      <p className="muted">Last updated: 9 November 2026</p>

      <h2>What we collect</h2>
      <p>
        Browsing the site needs no account, and we don&apos;t ask for your details. If you buy a Premium subscription, we store your <strong>email</strong>, <strong>phone number</strong>,
        <strong> Telegram ID and username</strong>, and your <strong>payment records</strong> (payment ID, amount,
        method, status and date).
      </p>

      <h2>Why</h2>
      <p>
        Only to run your subscription: to confirm payments, let you into the private channel, and remove access when a
        subscription ends. We don&apos;t sell or rent your data.
      </p>

      <h2>Where it&apos;s stored</h2>
      <p>
        In a private database (Supabase) that only our server can access. Payments are handled by Razorpay, and we never
        see or store your card or UPI details. Razorpay&apos;s and Telegram&apos;s own privacy policies apply to their
        services. Our hosting provider may keep standard technical logs.
      </p>

      <h2>Job listings</h2>
      <p>
        Jobs link to each company&apos;s own career page or job board. Our only charge is the optional Premium
        subscription to this job list. We never charge for a job or take money to get you hired. If anyone asks you to
        pay for a job offer, it&apos;s a scam.
      </p>
    </section>
  );
}
