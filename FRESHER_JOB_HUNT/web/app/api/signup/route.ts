import { randomBytes } from "node:crypto";
import { NextResponse } from "next/server";
import { z } from "zod";
import { FIELD_KEYS } from "@/lib/fields";
import { db } from "@/lib/supabase";

const Signup = z.object({
  name: z.string().trim().min(2, "Please enter your name").max(80),
  email: z.string().trim().toLowerCase().email("Please enter a valid email").max(254),
  fields: z.array(z.enum(FIELD_KEYS)).min(1, "Pick at least one field"),
  workModes: z.array(z.enum(["remote", "onsite"])).min(1, "Pick remote, office or both"),
  emailAlerts: z.boolean(),
  consent: z.literal(true, { message: "Please agree to receive job alerts" }),
  website: z.string().max(0, "Invalid request").optional(), // honeypot: real people leave it empty
  turnstileToken: z.string().optional(),
});

async function turnstileOk(token: string | undefined, ip: string | null) {
  const secret = process.env.TURNSTILE_SECRET_KEY;
  if (!secret) return true; // not configured: skip (e.g. local development)
  if (!token) return false;
  const body = new URLSearchParams({ secret, response: token, ...(ip ? { remoteip: ip } : {}) });
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body });
  const data = (await r.json()) as { success?: boolean };
  return data.success === true;
}

export async function POST(req: Request) {
  let input: unknown;
  try {
    input = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }

  const parsed = Signup.safeParse(input);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message ?? "Invalid details" }, { status: 400 });
  }
  const data = parsed.data;

  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? null;
  if (!(await turnstileOk(data.turnstileToken, ip))) {
    return NextResponse.json({ error: "Spam check failed. Please refresh and try again." }, { status: 400 });
  }

  const supabase = db();
  if (!supabase) {
    return NextResponse.json({ error: "Signups aren't open yet (database not configured)." }, { status: 503 });
  }

  const { error } = await supabase.from("users").insert({
    name: data.name,
    email: data.email,
    fields: data.fields,
    work_modes: data.workModes,
    email_alerts: data.emailAlerts,
    consent_at: new Date().toISOString(),
    token: randomBytes(24).toString("hex"),
  });

  if (error) {
    if (error.code === "23505") {
      return NextResponse.json({ ok: true, message: "You're already subscribed with this email. 🎉" });
    }
    console.error("signup insert failed", error);
    return NextResponse.json({ error: "Something went wrong. Please try again." }, { status: 500 });
  }
  return NextResponse.json({ ok: true, message: "You're in! Jobs for your fields start tomorrow at 10 AM. 🎉" });
}
