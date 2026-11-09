import { NextResponse } from "next/server";
import { razorpay, signatureValid, type RazorpayPayment, type RazorpaySubscription } from "@/lib/razorpay";
import { findBySubscription, grantAccess, recordPayment } from "@/lib/subscribers";

const BOT = process.env.TELEGRAM_BOT_USERNAME ?? "Naukaridede_bot";

/** Called by the checkout after payment. Only a correct Razorpay signature grants access. */
export async function POST(request: Request) {
  const body = (await request.json().catch(() => ({}))) as Record<string, unknown>;
  const paymentId = body.razorpay_payment_id;
  const subscriptionId = body.razorpay_subscription_id;
  if (
    typeof paymentId !== "string" ||
    typeof subscriptionId !== "string" ||
    !signatureValid(`${paymentId}|${subscriptionId}`, body.razorpay_signature, process.env.RAZORPAY_KEY_SECRET)
  ) {
    return NextResponse.json({ error: "Payment could not be verified." }, { status: 400 });
  }

  try {
    const subscriber = await findBySubscription(subscriptionId);
    if (!subscriber) return NextResponse.json({ error: "Subscription not found." }, { status: 404 });
    const [payment, subscription] = await Promise.all([
      razorpay<RazorpayPayment>(`payments/${encodeURIComponent(paymentId)}`),
      razorpay<RazorpaySubscription>(`subscriptions/${encodeURIComponent(subscriptionId)}`),
    ]);
    await recordPayment(subscriber, payment);
    await grantAccess(subscriber, subscription.current_end, payment);
    return NextResponse.json({ botUrl: `https://t.me/${BOT}?start=${subscriber.token}` });
  } catch (e) {
    console.error("verify failed", e);
    return NextResponse.json({ error: "Payment received, but we couldn't finish setup. Please retry." }, { status: 500 });
  }
}
