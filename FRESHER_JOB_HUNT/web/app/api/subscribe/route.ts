import { randomBytes } from "node:crypto";
import { NextResponse } from "next/server";
import { razorpay, type RazorpaySubscription } from "@/lib/razorpay";
import { createSubscriber, tooManyRecentCheckouts } from "@/lib/subscribers";

/** Starts a ₹99/month subscription. Razorpay's checkout collects the buyer's email and phone. */
export async function POST() {
  try {
    if (await tooManyRecentCheckouts(30, 10)) {
      return NextResponse.json({ error: "Too many people are checking out. Please try again shortly." }, { status: 429 });
    }
    const token = randomBytes(24).toString("hex");
    const subscription = await razorpay<RazorpaySubscription>("subscriptions", {
      plan_id: process.env.RAZORPAY_PLAN_ID,
      total_count: 120, // up to 10 years of monthly renewals, until cancelled
      quantity: 1,
      customer_notify: 1,
    });
    await createSubscriber(token, subscription.id);
    return NextResponse.json({ subscriptionId: subscription.id, keyId: process.env.RAZORPAY_KEY_ID });
  } catch (e) {
    console.error("subscribe failed", e);
    return NextResponse.json({ error: "Couldn't start the payment. Please try again." }, { status: 500 });
  }
}
