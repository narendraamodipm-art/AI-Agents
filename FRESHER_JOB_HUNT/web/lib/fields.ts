// Keep in sync with FIELDS in agent/config.py
export const FIELDS = [
  { key: "ai_engineer", label: "AI Engineer", emoji: "🤖" },
  { key: "ml_engineer", label: "ML Engineer", emoji: "🧠" },
  { key: "data_engineer", label: "Data Engineer", emoji: "🛠" },
  { key: "data_analyst", label: "Data Analyst", emoji: "📊" },
  { key: "full_stack", label: "Full Stack", emoji: "🌐" },
  { key: "software_engineer", label: "Software Engineer", emoji: "💻" },
] as const;

export function fieldInfo(key: string) {
  return FIELDS.find((f) => f.key === key) ?? { key, label: key, emoji: "💼" };
}

// Keep in sync with EXPERIENCE in agent/config.py
export const EXPERIENCE = [
  { key: "0-2", label: "0–2 yrs", emoji: "🎓", heading: "Freshers & interns" },
  { key: "2-4", label: "2–4 yrs", emoji: "🚀", heading: "Early career" },
  { key: "4-6", label: "4–6 yrs", emoji: "⭐", heading: "Mid-level" },
  { key: "6+", label: "6+ yrs", emoji: "🏆", heading: "Senior & lead" },
] as const;

/** Jobs saved before experience sections existed were all 0–2. */
export const experienceOf = (job: Job) => job.experience ?? "0-2";

export type Job = {
  id: number;
  title: string;
  company: string;
  location: string | null;
  work_mode: string | null;
  fields: string[] | null;
  experience?: string | null;
  url: string;
  posted_at: string | null;
};
