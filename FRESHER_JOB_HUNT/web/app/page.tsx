import Link from "next/link";
import { FIELDS } from "@/lib/fields";
import { latestPost, niceDay } from "@/lib/jobs";
import JobList from "./components/JobList";
import JoinButtons from "./components/JoinButtons";
import SignupForm from "./components/SignupForm";

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
            Fresher jobs &amp; internships, <span className="grad">delivered daily.</span>
          </h1>
          <p className="lead">
            10–12 hand-filtered openings for <strong>0–2 years</strong> experience, remote and office roles in India.
            Every link goes straight to the company&apos;s apply page. Free, no spam.
          </p>
          <div className="fields">
            {FIELDS.map((f) => (
              <span key={f.key} className="tag">
                {f.emoji} {f.label}
              </span>
            ))}
          </div>
          <JoinButtons />
          <ul className="how">
            <li>
              <b>1.</b> Sign up and pick your fields
            </li>
            <li>
              <b>2.</b> Our agent scans company career pages every morning
            </li>
            <li>
              <b>3.</b> You get 10–12 fresh jobs on Telegram, WhatsApp and email
            </li>
          </ul>
        </div>
        <div id="signup">
          <SignupForm />
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>{post ? `Today's jobs · ${niceDay(post.day)}` : "Today's jobs"}</h2>
          {post && post.jobs.length > 6 && (
            <Link href="/today" className="link">
              See all {post.jobs.length} →
            </Link>
          )}
        </div>
        {post?.jobs.length ? (
          <JobList jobs={post.jobs} limit={6} />
        ) : (
          <p className="muted card">The first daily list appears here after the agent&apos;s next 10 AM run.</p>
        )}
      </section>
    </>
  );
}
