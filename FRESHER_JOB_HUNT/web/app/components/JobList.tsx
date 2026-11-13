import { FIELDS, type Job } from "@/lib/fields";
import { PAYMENTS_OPEN } from "@/lib/flags";
import ApplyButton from "./ApplyButton";

const MODE: Record<string, string> = { remote: "Remote", hybrid: "Hybrid", onsite: "On-site" };

export default function JobList({ jobs, limit }: { jobs: Job[]; limit?: number }) {
  const shown = limit ? jobs.slice(0, limit) : jobs;
  const groups = FIELDS.map((f) => ({
    ...f,
    jobs: shown.filter((j) => (j.fields?.[0] ?? "software_engineer") === f.key),
  })).filter((g) => g.jobs.length);

  return (
    <div className="groups">
      {groups.map((g) => (
        <section key={g.key} className="group">
          <h3>
            {g.emoji} {g.label}
          </h3>
          <ul className="jobs">
            {g.jobs.map((j) => (
              <li key={j.id} className="job">
                <div>
                  <div className="job-title">{j.title}</div>
                  <div className="job-meta">
                    {j.company} · {(j.location ?? "India").split(" / ")[0]} ·{" "}
                    <span className={`mode ${j.work_mode ?? "onsite"}`}>{MODE[j.work_mode ?? "onsite"]}</span>
                  </div>
                </div>
                <ApplyButton id={j.id} title={j.title} paymentsOpen={PAYMENTS_OPEN} />
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
