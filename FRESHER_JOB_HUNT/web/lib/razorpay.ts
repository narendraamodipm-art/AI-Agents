import "server-only";
import { createHmac, timingSafeEqual } from "node:crypto";

export type RazorpayPayment = {
  id: string;
  amount: number;
  currency: string;
  status: string;
  method?: string;
  email?: string;
  contact?: string;
  created_at?: number;
};

export type RazorpaySubscription = { id: string; status: string; current_end?: number | null };

export async function razorpay<T>(path: string, body?: unknown): Promise<T> {
  const auth = Buffer.from(`${process.env.RAZORPAY_KEY_ID}:${process.env.RAZORPAY_KEY_SECRET}`).toString("base64");
  const r = await fetch(`https://api.razorpay.com/v1/${path}`, {
    method: body ? "POST" : "GET",
    cache: "no-store",
    headers: { Authorization: `Basic ${auth}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`Razorpay ${path.split("/")[0]}: ${r.status} ${await r.text()}`);
  return (await r.json()) as T;
}

/** True when `signature` is the HMAC-SHA256 of `message` under `secret`. */
export function signatureValid(message: string, signature: unknown, secret: string | undefined) {
  if (!secret || typeof signature !== "string") return false;
  const expected = Buffer.from(createHmac("sha256", secret).update(message).digest("hex"));
  const given = Buffer.from(signature);
  return expected.length === given.length && timingSafeEqual(expected, given);
}
