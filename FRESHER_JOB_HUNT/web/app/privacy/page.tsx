import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy | Fresher Job Hunt" };

export default function Privacy() {
  return (
    <section className="section narrow prose">
      <h1 className="page-title">Privacy policy</h1>
      <p className="muted">Last updated: 9 November 2026</p>

      <h2>What we collect</h2>
      <p>
        Nothing. This site has no accounts or signup forms and doesn&apos;t ask for your name, email or phone number.
      </p>

      <h2>Hosting and Telegram</h2>
      <p>
        Like most websites, our hosting provider may keep standard technical logs. If you join our Telegram channel,
        Telegram&apos;s own privacy policy applies there.
      </p>

      <h2>Job listings</h2>
      <p>
        Jobs link to each company&apos;s own career page or job board. We don&apos;t charge for applying, and we never
        ask for money. If anyone asks you to pay for a job, it&apos;s a scam.
      </p>
    </section>
  );
}
