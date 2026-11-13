import type { Metadata } from "next";
import Link from "next/link";
import { FREE_JOIN_URL } from "@/lib/contact";
import { PAYMENTS_OPEN } from "@/lib/flags";
import { latestPost, niceDay } from "@/lib/jobs";
import ExperienceSections from "../components/ExperienceSections";

export const revalidate = 300;
export const metadata: Metadata = { title: "Sample jobs | JOB HUNTER" };

export default async function Today() {
  const post = await latestPost();
  return (
    <section className="section narrow">
      <h1 className="page-title">{post ? `Sample jobs · ${niceDay(post.day)}` : "Sample jobs"}</h1>
      <p className="lead">
        {post
          ? PAYMENTS_OPEN
            ? "A sample of today's list. Premium members get every job in our private Telegram channel at 10 AM & 6 PM IST."
            : "A sample of today's list. Join our Telegram channel free to get every job at 10 AM & 6 PM IST."
          : "No list yet: new jobs are added twice a day, at 10 AM & 6 PM IST."}
      </p>
      <p>
        {PAYMENTS_OPEN ? (
          <Link href="/#subscribe" className="btn primary">
            Subscribe for ₹99/month
          </Link>
        ) : (
          <a href={FREE_JOIN_URL} className="btn telegram" target="_blank" rel="noopener noreferrer">
            ✈️ Join the channel free
          </a>
        )}
      </p>
      {post?.jobs.length ? <ExperienceSections jobs={post.jobs} /> : null}
    </section>
  );
}
