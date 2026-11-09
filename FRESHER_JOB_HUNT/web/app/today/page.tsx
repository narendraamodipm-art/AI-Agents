import type { Metadata } from "next";
import { latestPost, niceDay } from "@/lib/jobs";
import ExperienceSections from "../components/ExperienceSections";
import JoinButtons from "../components/JoinButtons";

export const revalidate = 300;
export const metadata: Metadata = { title: "Today's jobs | Fresher Job Hunt" };

export default async function Today() {
  const post = await latestPost();
  return (
    <section className="section narrow">
      <h1 className="page-title">{post ? `Today's jobs · ${niceDay(post.day)}` : "Today's jobs"}</h1>
      <p className="lead">
        {post
          ? `${post.jobs.length} openings in four sections: 0–2, 2–4, 4–6 and 6+ years. Tap Apply to open the company's page.`
          : "No list yet: the agent posts every day at 10:00 AM IST."}
      </p>
      <JoinButtons />
      {post?.jobs.length ? <ExperienceSections jobs={post.jobs} /> : null}
    </section>
  );
}
