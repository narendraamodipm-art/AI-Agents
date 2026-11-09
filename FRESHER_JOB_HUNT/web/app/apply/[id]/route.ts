import { NextResponse, type NextRequest } from "next/server";
import { latestPost } from "@/lib/jobs";
import { SUBSCRIBED_COOKIE } from "@/lib/subscribed";

/** Sends subscribers on to the company's page. Everyone else goes to the Subscribe card. */
export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const subscribe = NextResponse.redirect(new URL("/#subscribe", request.url));
  if (request.cookies.get(SUBSCRIBED_COOKIE)?.value !== "1") return subscribe;

  const { id } = await params;
  const post = await latestPost();
  const job = post?.jobs.find((j) => String(j.id) === id);
  return job && /^https?:\/\//.test(job.url) ? NextResponse.redirect(job.url) : subscribe;
}
