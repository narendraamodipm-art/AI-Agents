// Keep in sync with FIELDS in agent/config.py
export const FIELDS = [
  { key: "ai_engineer", label: "AI Engineer", emoji: "🤖" },
  { key: "ml_engineer", label: "ML Engineer", emoji: "🧠" },
  { key: "data_engineer", label: "Data Engineer", emoji: "🛠" },
  { key: "data_analyst", label: "Data Analyst", emoji: "📊" },
  { key: "full_stack", label: "Full Stack", emoji: "🌐" },
  { key: "software_engineer", label: "Software Engineer", emoji: "💻" },
] as const;

export type FieldKey = (typeof FIELDS)[number]["key"];
export const FIELD_KEYS = FIELDS.map((f) => f.key) as [FieldKey, ...FieldKey[]];

export function fieldInfo(key: string) {
  return FIELDS.find((f) => f.key === key) ?? { key, label: key, emoji: "💼" };
}

export type Job = {
  id: number;
  title: string;
  company: string;
  location: string | null;
  work_mode: string | null;
  fields: string[] | null;
  url: string;
  posted_at: string | null;
};
