/** "Why this channel exists": the story behind JOB HUNTER, shown on the home page. */
export default function WhySection() {
  return (
    <section className="section why">
      <div className="why-story card">
        <p className="kicker">💙 Why this channel exists</p>
        <h2>Helping you find a job in a tough market</h2>
        <p>
          The job market is tough right now, so this is a small effort from us to help you find a job, especially if
          you&apos;re a <strong>fresher</strong>.
        </p>
        <p>
          Many openings are never listed on portals like Naukri or LinkedIn. They&apos;re posted only on the{" "}
          <strong>company&apos;s own careers page</strong>. We bring you those openings, with links straight to the
          company&apos;s portal.
        </p>
      </div>

      <div className="why-grid">
        <div className="card why-card">
          <span className="why-icon" aria-hidden="true">🏢</span>
          <h3>Straight from company portals</h3>
          <p>Every Apply link goes to the company&apos;s own careers page, not a job board.</p>
        </div>
        <div className="card why-card">
          <span className="why-icon" aria-hidden="true">🕙</span>
          <h3>Twice a day</h3>
          <p>Fresh jobs at 10 AM and 6 PM IST, sorted by experience: 0–2, 2–4, 4–6 and 6+ years.</p>
        </div>
        <div className="card why-card">
          <span className="why-icon" aria-hidden="true">🏭</span>
          <h3>Mass recruiters marked</h3>
          <p>Jobs from big fresher recruiters are tagged, so they&apos;re easy to spot.</p>
        </div>
        <div className="card why-card">
          <span className="why-icon" aria-hidden="true">🆓</span>
          <h3>Completely free</h3>
          <p>No signup and no fees. Just join the Telegram channel.</p>
        </div>
      </div>

      <p className="scam-note" role="note">
        🚫 <strong>We never charge for jobs.</strong> If anyone asks you to pay for a job, it&apos;s a scam.
      </p>
    </section>
  );
}
