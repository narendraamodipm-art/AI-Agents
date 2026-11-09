import { NextResponse, type NextRequest } from "next/server";
import { JOINED_COOKIE } from "@/lib/joined";
import { latestPost } from "@/lib/jobs";

/** Sends visitors who clicked a Telegram join link on to the company's page. Everyone else goes to the join card. */
export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const home = NextResponse.redirect(new URL("/", request.url));
  if (request.cookies.get(JOINED_COOKIE)?.value !== "1") return home;

  const { id } = await params;
  const post = await latestPost();
  const job = post?.jobs.find((j) => String(j.id) === id);
  return job && /^https?:\/\//.test(job.url) ? NextResponse.redirect(job.url) : home;
}
