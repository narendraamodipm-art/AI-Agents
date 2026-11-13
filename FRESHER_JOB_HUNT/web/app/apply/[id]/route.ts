import { NextResponse, type NextRequest } from "next/server";
import { PAYMENTS_OPEN } from "@/lib/flags";
import { latestPost } from "@/lib/jobs";
import { SUBSCRIBED_COOKIE } from "@/lib/subscribed";

/** Sends visitors on to the company's page: everyone while the channel is free, only subscribers once payments open. */
export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const subscribe = NextResponse.redirect(new URL("/#subscribe", request.url));
  if (PAYMENTS_OPEN && request.cookies.get(SUBSCRIBED_COOKIE)?.value !== "1") return subscribe;

  const { id } = await params;
  const post = await latestPost();
  const job = post?.jobs.find((j) => String(j.id) === id);
  return job && /^https?:\/\//.test(job.url) ? NextResponse.redirect(job.url) : subscribe;
}
