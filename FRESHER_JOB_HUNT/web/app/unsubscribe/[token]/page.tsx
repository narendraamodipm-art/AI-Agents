import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { db } from "@/lib/supabase";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Unsubscribe | Fresher Job Hunt", robots: { index: false } };

const TOKEN = /^[a-f0-9]{48}$/;

async function unsubscribe(formData: FormData) {
  "use server";
  const token = String(formData.get("token") ?? "");
  if (!TOKEN.test(token)) redirect("/");
  const supabase = db();
  if (supabase) {
    await supabase.from("users").update({ status: "unsubscribed" }).eq("token", token);
  }
  redirect(`/unsubscribe/${token}?done=1`);
}

export default async function Unsubscribe({
  params,
  searchParams,
}: {
  params: Promise<{ token: string }>;
  searchParams: Promise<{ done?: string }>;
}) {
  const { token } = await params;
  const { done } = await searchParams;

  if (done) {
    return (
      <section className="section narrow center">
        <div className="card">
          <h1 className="page-title">You&apos;re unsubscribed</h1>
          <p className="lead">You won&apos;t get any more job emails from us. Good luck with your job hunt! 🍀</p>
        </div>
      </section>
    );
  }

  return (
    <section className="section narrow center">
      <form className="card" action={unsubscribe}>
        <h1 className="page-title">Stop job emails?</h1>
        <p className="lead">You&apos;ll stop receiving daily job emails. You can sign up again any time.</p>
        <input type="hidden" name="token" value={token} />
        <button className="btn primary" type="submit">
          Unsubscribe
        </button>
      </form>
    </section>
  );
}
