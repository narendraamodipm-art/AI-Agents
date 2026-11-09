import { NextResponse } from "next/server";
import { razorpay } from "@/lib/razorpay";
import {
  findByTelegram,
  findByToken,
  hasAccess,
  linkTelegram,
  updateSubscriber,
} from "@/lib/subscribers";

type From = { id: number; username?: string };
type Update = {
  message?: { text?: string; chat: { id: number; type: string }; from?: From };
  chat_join_request?: { chat: { id: number }; from: From };
};

async function telegram<T = unknown>(method: string, body: unknown): Promise<T> {
  const r = await fetch(`https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}/${method}`, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = (await r.json()) as { ok: boolean; result: T; description?: string };
  if (!data.ok) throw new Error(`Telegram ${method}: ${r.status} ${data.description}`);
  return data.result;
}

const say = (chat_id: number, text: string, extra: object = {}) => telegram("sendMessage", { chat_id, text, ...extra });

/** Someone opened the bot from the link shown after payment. */
async function handleStart(chatId: number, from: From, token: string | undefined) {
  const subscriber = token ? await findByToken(token) : null;
  if (!subscriber || !hasAccess(subscriber)) {
    return say(chatId, "I couldn't find an active subscription for this link. Please subscribe on our website first.");
  }
  if (subscriber.telegram_user_id && subscriber.telegram_user_id !== from.id) {
    return say(chatId, "This subscription is already linked to another Telegram account.");
  }
  await linkTelegram(subscriber, from.id, from.username);

  const channel = process.env.TELEGRAM_PAID_CHANNEL_ID;
  if (!channel) {
    return say(chatId, "✅ Payment confirmed! The premium channel opens soon. Open this same link again then to join.");
  }
  // A join-request link, so it only works for this paid account even if it's forwarded.
  const invite = await telegram<{ invite_link: string }>("createChatInviteLink", {
    chat_id: channel,
    creates_join_request: true,
    expire_date: Math.floor(Date.now() / 1000) + 86_400,
  });
  return say(chatId, "✅ Payment confirmed! Tap below to join the premium channel.", {
    reply_markup: { inline_keyboard: [[{ text: "Join premium channel", url: invite.invite_link }]] },
  });
}

/** /cancel asks first; /confirmcancel stops renewals. Access continues until the end of the paid month. */
async function handleCancel(chatId: number, from: From, confirmed: boolean) {
  const subscriber = await findByTelegram(from.id);
  if (!subscriber || !hasAccess(subscriber)) {
    return say(chatId, "I couldn't find an active subscription for this Telegram account.");
  }
  if (!confirmed) {
    return say(chatId, "Stop your ₹99/month subscription? You keep access until the paid period ends. Send /confirmcancel to confirm.");
  }
  try {
    await razorpay(`subscriptions/${subscriber.razorpay_subscription_id}/cancel`, { cancel_at_cycle_end: 1 });
  } catch (e) {
    console.error("cancel failed", e);
    return say(chatId, "I couldn't cancel that just now. It may already be cancelled. Please try again later.");
  }
  const until = new Date(subscriber.paid_until!).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
  return say(chatId, `✅ Cancelled. You won't be charged again, and you keep access until ${until}.`);
}

/** Only paid accounts are let in, whichever invite link they used. */
async function handleJoinRequest(chatId: number, from: From) {
  if (String(chatId) !== process.env.TELEGRAM_PAID_CHANNEL_ID) return;
  const subscriber = await findByTelegram(from.id);
  if (subscriber && hasAccess(subscriber)) {
    await telegram("approveChatJoinRequest", { chat_id: chatId, user_id: from.id });
    await updateSubscriber(subscriber.id, { joined_at: new Date().toISOString() });
  } else {
    await telegram("declineChatJoinRequest", { chat_id: chatId, user_id: from.id });
  }
}

export async function POST(request: Request) {
  const secret = process.env.TELEGRAM_WEBHOOK_SECRET;
  if (!secret || request.headers.get("x-telegram-bot-api-secret-token") !== secret) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }
  const update = (await request.json()) as Update;
  const { message, chat_join_request: join } = update;

  if (join) {
    await handleJoinRequest(join.chat.id, join.from);
  } else if (message?.from && message.chat.type === "private" && message.text) {
    const [command, argument] = message.text.trim().split(/\s+/);
    if (command === "/start") await handleStart(message.chat.id, message.from, argument);
    else if (command === "/cancel") await handleCancel(message.chat.id, message.from, false);
    else if (command === "/confirmcancel") await handleCancel(message.chat.id, message.from, true);
  }
  return NextResponse.json({ ok: true });
}
