import "server-only";
import type { RazorpayPayment } from "./razorpay";
import { rest } from "./supabase";

export type Subscriber = {
  id: string;
  token: string;
  razorpay_subscription_id: string;
  status: string;
  paid_until: string | null;
  telegram_user_id: number | null;
};

const DAY_MS = 86_400_000;

async function findBy(column: string, value: string | number) {
  const rows = await rest<Subscriber[]>(`subscribers?select=*&${column}=eq.${encodeURIComponent(value)}&limit=1`);
  return rows[0] ?? null;
}

export const findByToken = (token: string) => findBy("token", token);
export const findBySubscription = (id: string) => findBy("razorpay_subscription_id", id);
export const findByTelegram = (userId: number) => findBy("telegram_user_id", userId);

/** True when too many checkouts were started recently, which stops one script creating subscriptions in a loop. */
export async function tooManyRecentCheckouts(limit: number, minutes: number) {
  const since = new Date(Date.now() - minutes * 60_000).toISOString();
  const rows = await rest<unknown[]>(`subscribers?select=id&status=eq.created&created_at=gte.${since}&limit=${limit}`);
  return rows.length >= limit;
}

export function createSubscriber(token: string, subscriptionId: string) {
  return rest("subscribers", {
    method: "POST",
    body: JSON.stringify({ token, razorpay_subscription_id: subscriptionId }),
  });
}

export function updateSubscriber(id: string, patch: Record<string, unknown>) {
  return rest(`subscribers?id=eq.${id}`, {
    method: "PATCH",
    body: JSON.stringify({ ...patch, updated_at: new Date().toISOString() }),
  });
}

/** Moves a Telegram account onto this subscription, e.g. someone re-subscribing after their old plan ended. */
export async function linkTelegram(subscriber: Subscriber, userId: number, username?: string) {
  await rest(`subscribers?telegram_user_id=eq.${userId}&id=neq.${subscriber.id}`, {
    method: "PATCH",
    body: JSON.stringify({ telegram_user_id: null }),
  });
  await updateSubscriber(subscriber.id, { telegram_user_id: userId, telegram_username: username ?? null });
}

export const hasAccess = (s: Subscriber) => Boolean(s.paid_until && new Date(s.paid_until).getTime() > Date.now());

/** Marks a successful charge. Access never moves backwards, so webhooks can arrive in any order. */
export async function grantAccess(subscriber: Subscriber, periodEnd: number | null | undefined, payment: RazorpayPayment) {
  const paidFor = periodEnd ? periodEnd * 1000 : Date.now() + 31 * DAY_MS;
  const current = subscriber.paid_until ? new Date(subscriber.paid_until).getTime() : 0;
  await updateSubscriber(subscriber.id, {
    status: "active",
    paid_until: new Date(Math.max(paidFor, current)).toISOString(),
    removed_at: null,
    ...(payment.email ? { email: payment.email } : {}),
    ...(payment.contact ? { phone: payment.contact } : {}),
  });
}

/** Saves a payment once. Razorpay can send the same event repeatedly. */
export function recordPayment(subscriber: Subscriber, payment: RazorpayPayment, raw?: unknown) {
  const status = payment.status === "failed" ? "failed" : payment.status === "refunded" ? "refunded" : "captured";
  return rest("payments?on_conflict=razorpay_payment_id", {
    method: "POST",
    headers: { Prefer: "resolution=ignore-duplicates,return=minimal" },
    body: JSON.stringify({
      subscriber_id: subscriber.id,
      razorpay_payment_id: payment.id,
      razorpay_subscription_id: subscriber.razorpay_subscription_id,
      amount_paise: payment.amount,
      currency: payment.currency,
      status,
      method: payment.method ?? null,
      paid_at: payment.created_at ? new Date(payment.created_at * 1000).toISOString() : null,
      raw: raw ?? payment,
    }),
  });
}
