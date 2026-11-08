"use client";

import Script from "next/script";
import { useState } from "react";
import { EXPERIENCE, FIELDS } from "@/lib/fields";
import { TELEGRAM_URL } from "@/lib/links";

const SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;

export default function SignupForm() {
  const [fields, setFields] = useState<string[]>([]);
  const [modes, setModes] = useState<string[]>(["remote", "onsite"]);
  const [experience, setExperience] = useState<string[]>(["0-2"]);
  const [status, setStatus] = useState<{ kind: "idle" | "busy" | "ok" | "err"; msg?: string }>({ kind: "idle" });

  const toggle = (list: string[], set: (v: string[]) => void, key: string) =>
    set(list.includes(key) ? list.filter((k) => k !== key) : [...list, key]);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setStatus({ kind: "busy" });
    try {
      const r = await fetch("/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.get("name"),
          email: form.get("email"),
          phone: form.get("phone") || undefined,
          fields,
          workModes: modes,
          experience,
          emailAlerts: form.get("emailAlerts") === "on",
          consent: form.get("consent") === "on",
          website: form.get("website") || undefined,
          turnstileToken: form.get("cf-turnstile-response") || undefined,
        }),
      });
      const data = (await r.json()) as { ok?: boolean; message?: string; error?: string };
      if (r.ok && data.ok) setStatus({ kind: "ok", msg: data.message });
      else setStatus({ kind: "err", msg: data.error ?? "Something went wrong." });
    } catch {
      setStatus({ kind: "err", msg: "Network error. Please try again." });
    }
  }

  if (status.kind === "ok") {
    return (
      <div className="card success" role="status">
        <h3>{status.msg}</h3>
        {TELEGRAM_URL ? (
          <>
            <p>Join our Telegram channel: every morning at 10 AM we post new job links there for each experience level.</p>
            <a className="btn telegram block" href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer">
              ✈️ Join Telegram for daily job links
            </a>
          </>
        ) : (
          <p>Also join the daily post on Telegram or WhatsApp so you never miss a day.</p>
        )}
      </div>
    );
  }

  return (
    <form className="card form" onSubmit={submit} noValidate>
      {SITE_KEY && <Script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer />}
      <h3>Get jobs for your field</h3>

      <label className="lbl">
        Name
        <input name="name" required minLength={2} maxLength={80} autoComplete="name" placeholder="Your name" />
      </label>
      <label className="lbl">
        Email
        <input name="email" type="email" required autoComplete="email" placeholder="you@example.com" />
      </label>
      <label className="lbl">
        <span>
          Phone number <span className="optional">(optional)</span>
        </span>
        <input
          name="phone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          maxLength={20}
          placeholder="+91 98765 43210"
        />
      </label>

      {TELEGRAM_URL && (
        <a className="tg-callout" href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer">
          <span className="tg-icon" aria-hidden="true">✈️</span>
          <span>
            <strong>Get job links on Telegram</strong>
            <br />
            Join our channel: 10–12 job links per experience level, every day at 10 AM.
          </span>
          <span className="tg-go" aria-hidden="true">Join →</span>
        </a>
      )}

      <fieldset>
        <legend>Fields you want</legend>
        <div className="chips">
          {FIELDS.map((f) => (
            <button
              type="button"
              key={f.key}
              className={`chip ${fields.includes(f.key) ? "on" : ""}`}
              aria-pressed={fields.includes(f.key)}
              onClick={() => toggle(fields, setFields, f.key)}
            >
              {f.emoji} {f.label}
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend>Your experience</legend>
        <div className="chips">
          {EXPERIENCE.map((x) => (
            <button
              type="button"
              key={x.key}
              className={`chip ${experience.includes(x.key) ? "on" : ""}`}
              aria-pressed={experience.includes(x.key)}
              onClick={() => toggle(experience, setExperience, x.key)}
            >
              {x.emoji} {x.label}
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend>Work type</legend>
        <div className="chips">
          {[
            ["remote", "🏠 Remote"],
            ["onsite", "🏢 Office / Hybrid"],
          ].map(([key, label]) => (
            <button
              type="button"
              key={key}
              className={`chip ${modes.includes(key) ? "on" : ""}`}
              aria-pressed={modes.includes(key)}
              onClick={() => toggle(modes, setModes, key)}
            >
              {label}
            </button>
          ))}
        </div>
      </fieldset>

      {/* honeypot: hidden from people, bots fill it in */}
      <input name="website" tabIndex={-1} autoComplete="off" className="hp" aria-hidden="true" />

      <label className="check">
        <input type="checkbox" name="emailAlerts" defaultChecked />
        <span>Email me jobs matching my fields and experience daily (10–12 jobs)</span>
      </label>
      <label className="check">
        <input type="checkbox" name="consent" required />
        <span>
          I agree to receive job alerts and accept the <a href="/privacy">privacy policy</a>. I can unsubscribe any
          time.
        </span>
      </label>

      {SITE_KEY && <div className="cf-turnstile" data-sitekey={SITE_KEY} data-theme="auto" />}

      {status.kind === "err" && (
        <p className="error" role="alert">
          {status.msg}
        </p>
      )}
      <button className="btn primary" type="submit" disabled={status.kind === "busy"}>
        {status.kind === "busy" ? "Signing you up…" : "Sign up free"}
      </button>
    </form>
  );
}
