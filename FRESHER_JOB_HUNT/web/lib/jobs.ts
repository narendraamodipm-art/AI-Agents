import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";
import type { Job } from "./fields";
import { rest, supabaseConfigured } from "./supabase";

export type DailyPost = { day: string; jobs: Job[] };

// Written by the daily agent and committed by the GitHub Action, so the site updates without a redeploy.
const POST_URL =
  "https://raw.githubusercontent.com/narendraamodipm-art/AI-Agents/main/FRESHER_JOB_HUNT/data/latest_post.json";

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

/** The most recent daily post (what went out to Telegram). Null until the agent's first run. */
export async function latestPost(): Promise<DailyPost | null> {
  const preview = await localPreview();
  if (preview) return preview;
  try {
    if (supabaseConfigured()) {
      // Paid mode: the website only ever gets the free teaser, never the full list.
      const rows = await rest<{ day: string; teaser: Job[] }[]>("daily_posts?select=day,teaser&order=day.desc&limit=1", {
        next: { revalidate: 300 },
      });
      if (rows[0]?.teaser.length) return { day: rows[0].day, jobs: rows[0].teaser };
    }
    const r = await fetch(POST_URL, { next: { revalidate: 300 } });
    return r.ok ? ((await r.json()) as DailyPost) : null;
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
