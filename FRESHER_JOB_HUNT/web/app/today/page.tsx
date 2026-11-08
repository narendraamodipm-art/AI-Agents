import type { Metadata } from "next";
import Link from "next/link";
import { latestPost, niceDay } from "@/lib/jobs";
import JobList from "../components/JobList";
import JoinButtons from "../components/JoinButtons";

export const revalidate = 300;
export const metadata: Metadata = { title: "Today's fresher jobs | Fresher Job Hunt" };

export default async function Today() {
  const post = await latestPost();
  return (
    <section className="section narrow">
      <h1 className="page-title">{post ? `Fresher jobs · ${niceDay(post.day)}` : "Today's fresher jobs"}</h1>
      <p className="lead">
        {post
          ? `${post.jobs.length} openings for 0–2 years, grouped by field. Tap Apply to open the company's page.`
          : "No list yet: the agent posts every day at 10:00 AM IST."}
      </p>
      <JoinButtons />
      {post?.jobs.length ? <JobList jobs={post.jobs} /> : null}
      <p className="muted center">
        Want only your fields by email? <Link href="/#signup">Sign up free</Link>
      </p>
    </section>
  );
}
