import { RESUME_TOOL_URL } from "@/lib/contact";

/** Promotes the free Resume Match + Cover Letter app next to the main call to action. */
export default function ResumeToolCard() {
  return (
    <div className="card resume-card">
      <span className="resume-icon" aria-hidden="true">
        📄
      </span>
      <div>
        <h3>Check your resume before you apply</h3>
        <p>Free AI tool: see your match score for any job, the skills you&apos;re missing, and get a cover letter.</p>
      </div>
      <a className="btn resume-btn block" href={RESUME_TOOL_URL} target="_blank" rel="noopener noreferrer">
        Resume Match + Cover Letter →
      </a>
    </div>
  );
}
