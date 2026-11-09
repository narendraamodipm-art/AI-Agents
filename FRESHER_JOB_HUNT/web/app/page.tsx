import { EXPERIENCE, FIELDS } from "@/lib/fields";
import { latestPost, niceDay } from "@/lib/jobs";
import ExperienceSections from "./components/ExperienceSections";
import SubscribeCard from "./components/SubscribeCard";

export const revalidate = 300; // refresh the jobs preview every 5 minutes

export default async function Home() {
  const post = await latestPost();

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="pill">
            <span className="dot" /> New jobs every day at 10:00 AM IST
          </p>
          <h1>
            Tech jobs for every stage, <span className="grad">delivered daily.</span>
          </h1>
          <p className="lead">
            10–12 filtered openings per experience level, from <strong>freshers to 6+ years</strong>, remote and
            office roles in India. Every link goes straight to the company&apos;s apply page. No spam.
          </p>
          <div className="fields">
            {EXPERIENCE.map((e) => (
              <span key={e.key} className="tag exp">
                {e.emoji} {e.label}
              </span>
            ))}
          </div>
          <div className="fields">
            {FIELDS.map((f) => (
              <span key={f.key} className="tag">
                {f.emoji} {f.label}
              </span>
            ))}
          </div>
          <ul className="how">
            <li>
              <b>1.</b> Subscribe and join our private Telegram channel
            </li>
            <li>
              <b>2.</b> Our agent scans company career pages every morning
            </li>
            <li>
              <b>3.</b> You get 10–12 fresh jobs per level, every day at 10 AM
            </li>
          </ul>
        </div>
        <div id="subscribe">
          <SubscribeCard />
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>{post ? `Sample jobs · ${niceDay(post.day)}` : "Sample jobs"}</h2>
        </div>
        {post?.jobs.length ? (
          <ExperienceSections jobs={post.jobs} limitPerSection={3} />
        ) : (
          <p className="muted card">The first daily list appears here after the agent&apos;s next 10 AM run.</p>
        )}
      </section>
    </>
  );
}
