import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";
import type { Job } from "./fields";
import { db } from "./supabase";

export type DailyPost = { day: string; jobs: Job[] };

/** Local development without Supabase: show the agent's last `run.py --dry-run` result. */
async function localPreview(): Promise<DailyPost | null> {
  if (process.env.NODE_ENV === "production") return null;
  try {
    const file = path.join(process.cwd(), "..", "agent", "state", "preview_post.json");
    return JSON.parse(await readFile(file, "utf-8")) as DailyPost;
  } catch {
    return null;
  }
}

/** The most recent daily post (what went out to Telegram / WhatsApp). */
export async function latestPost(): Promise<DailyPost | null> {
  const supabase = db();
  if (!supabase) return localPreview();
  const { data, error } = await supabase
    .from("daily_posts")
    .select("day, jobs")
    .order("day", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) {
    console.error("latestPost failed", error);
    return null;
  }
  return (data as DailyPost | null) ?? null;
}

export function niceDay(day: string) {
  return new Date(`${day}T00:00:00Z`).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}
