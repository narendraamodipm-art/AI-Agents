import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";
import type { Job } from "./fields";
import { rest } from "./supabase";

export type DailyPost = { day: string; jobs: Job[] };

/** Local development: show the agent's last `run.py --dry-run` result if there is one. */
async function localPreview(): Promise<DailyPost | null> {
  if (process.env.NODE_ENV === "production") return null;
  try {
    const file = path.join(process.cwd(), "..", "agent", "state", "preview_post.json");
    return JSON.parse(await readFile(file, "utf-8")) as DailyPost;
  } catch {
    return null;
  }
}

/** The latest sample jobs for the website. Null until the agent's first run. */
export async function latestPost(): Promise<DailyPost | null> {
  const preview = await localPreview();
  if (preview) return preview;
  try {
    // The website only ever gets the sample jobs, never the full paid list.
    const rows = await rest<{ day: string; teaser: Job[] }[]>("daily_posts?select=day,teaser&order=day.desc&limit=1", {
      next: { revalidate: 300 },
    });
    return rows[0]?.teaser.length ? { day: rows[0].day, jobs: rows[0].teaser } : null;
  } catch (e) {
    console.error("latestPost failed", e);
    return null;
  }
}

export function niceDay(day: string) {
  return new Date(`${day}T00:00:00Z`).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}
