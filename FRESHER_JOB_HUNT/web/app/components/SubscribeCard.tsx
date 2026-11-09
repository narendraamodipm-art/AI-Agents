"use client";

import Script from "next/script";
import { useEffect, useState } from "react";
import { markSubscribed } from "@/lib/subscribed";

type Checkout = new (options: Record<string, unknown>) => { open(): void };
type Handled = { razorpay_payment_id: string; razorpay_subscription_id: string; razorpay_signature: string };
declare global {
  interface Window {
    Razorpay?: Checkout;
  }
}

const SAVED = "premium_bot_url"; // lets a buyer who closes the tab still reach the bot

export default function SubscribeCard() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [botUrl, setBotUrl] = useState("");

  useEffect(() => {
    try {
      const saved = localStorage.getItem(SAVED);
      if (saved) setBotUrl(saved);
    } catch {
      // storage blocked: the button still works
    }
  }, []);

  async function verify(response: Handled) {
    const r = await fetch("/api/subscribe/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(response),
    });
    const data = (await r.json()) as { botUrl?: string; error?: string };
    if (!r.ok || !data.botUrl) throw new Error(data.error ?? "Verification failed");
    markSubscribed();
    try {
      localStorage.setItem(SAVED, data.botUrl);
    } catch {
      // storage blocked: the link is still shown now
    }
    setBotUrl(data.botUrl);
  }

  async function subscribe() {
    setBusy(true);
    setError("");
    try {
      const r = await fetch("/api/subscribe", { method: "POST" });
      const data = (await r.json()) as { subscriptionId?: string; keyId?: string; error?: string };
      if (!r.ok || !data.subscriptionId || !window.Razorpay) throw new Error(data.error ?? "Checkout didn't load");
      new window.Razorpay({
        key: data.keyId,
        subscription_id: data.subscriptionId,
        name: "JOB HUNTER",
        description: "₹99 per month",
        theme: { color: "#7c3aed" },
        modal: { ondismiss: () => setBusy(false) },
        handler: (response: Handled) => {
          verify(response)
            .catch((e: Error) => setError(e.message))
            .finally(() => setBusy(false));
        },
      }).open();
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  if (botUrl) {
    return (
      <div className="card tg-card premium" role="status">
        <h3>You&apos;re subscribed 🎉</h3>
        <p>Open our Telegram bot to get your invite to the premium channel.</p>
        <a className="btn telegram block" href={botUrl} target="_blank" rel="noopener noreferrer">
          Open Telegram to join
        </a>
      </div>
    );
  }

  return (
    <div className="card tg-card premium">
      <Script src="https://checkout.razorpay.com/v1/checkout.js" strategy="lazyOnload" />
      <h3>Premium: every job, every day</h3>
      <p className="price">
        <b>₹99</b> / month
      </p>
      <ul>
        <li>The full list: up to 12 jobs per experience level</li>
        <li>Private Telegram channel, posted at 10 AM IST</li>
        <li>Pay by UPI or card</li>
      </ul>
      <button type="button" className="btn primary" onClick={subscribe} disabled={busy}>
        {busy ? "Opening checkout…" : "Subscribe for ₹99/month"}
      </button>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <p className="fine">
        Renews automatically every month. Cancel any time by sending /cancel to our Telegram bot. Payments are processed
        by Razorpay, and your statement shows the merchant&apos;s registered name.
      </p>
    </div>
  );
}
