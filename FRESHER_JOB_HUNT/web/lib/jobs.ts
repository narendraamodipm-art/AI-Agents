import "server-only";
import type { Job } from "./fields";
import { db } from "./supabase";

export type DailyPost = { day: string; jobs: Job[] };

/** The most recent daily post (what went out to Telegram / WhatsApp). */
export async function latestPost(): Promise<DailyPost | null> {
  const supabase = db();
  if (!supabase) return null;
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
