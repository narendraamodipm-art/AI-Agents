import Link from "next/link";
import { EXPERIENCE, experienceOf, type Job } from "@/lib/fields";
import JobList from "./JobList";

/** Jobs split into the four experience sections, with a jump bar at the top. */
export default function ExperienceSections({ jobs, limitPerSection }: { jobs: Job[]; limitPerSection?: number }) {
  const sections = EXPERIENCE.map((e) => ({ ...e, jobs: jobs.filter((j) => experienceOf(j) === e.key) }));

  return (
    <>
      <nav className="exp-nav" aria-label="Experience sections">
        {sections.map((s) => (
          <a key={s.key} href={`#exp-${s.key}`} className={`exp-chip ${s.jobs.length ? "" : "empty"}`}>
            {s.emoji} {s.label} <span className="count">{s.jobs.length}</span>
          </a>
        ))}
      </nav>
      {sections.map((s) => (
        <section key={s.key} id={`exp-${s.key}`} className="exp-section">
          <div className="exp-head">
            <h2>
              {s.emoji} {s.label}
            </h2>
            <span className="exp-sub">{s.heading}</span>
            {limitPerSection && s.jobs.length > limitPerSection && (
              <Link href={`/today#exp-${s.key}`} className="link exp-more">
                See all {s.jobs.length} →
              </Link>
            )}
          </div>
          {s.jobs.length ? (
            <JobList jobs={s.jobs} limit={limitPerSection} />
          ) : (
            <p className="muted card slim">No new jobs in this section today. Check back tomorrow at 10 AM.</p>
          )}
        </section>
      ))}
    </>
  );
}
