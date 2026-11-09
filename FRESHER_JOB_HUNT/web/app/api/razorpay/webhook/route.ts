import { NextResponse } from "next/server";
import { signatureValid, type RazorpayPayment, type RazorpaySubscription } from "@/lib/razorpay";
import { findBySubscription, grantAccess, recordPayment, updateSubscriber } from "@/lib/subscribers";

const STATUS: Record<string, string> = {
  "subscription.pending": "past_due",
  "subscription.halted": "past_due",
  "subscription.cancelled": "cancelled",
  "subscription.completed": "expired",
};

/** Razorpay's server-to-server events: monthly renewals, failed renewals and cancellations. */
export async function POST(request: Request) {
  const raw = await request.text();
  if (!signatureValid(raw, request.headers.get("x-razorpay-signature"), process.env.RAZORPAY_WEBHOOK_SECRET)) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }
  const event = JSON.parse(raw) as {
    event: string;
    payload?: { subscription?: { entity: RazorpaySubscription }; payment?: { entity: RazorpayPayment } };
  };

  const entity = event.payload?.subscription?.entity;
  const subscriber = entity ? await findBySubscription(entity.id) : null;
  if (!entity || !subscriber) return NextResponse.json({ ok: true });

  const payment = event.payload?.payment?.entity;
  if (event.event === "subscription.charged" && payment) {
    await recordPayment(subscriber, payment, event);
    await grantAccess(subscriber, entity.current_end, payment);
  } else if (STATUS[event.event]) {
    await updateSubscriber(subscriber.id, { status: STATUS[event.event] }); // access runs until paid_until
  }
  return NextResponse.json({ ok: true });
}
