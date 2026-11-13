import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { FREE_JOIN_URL } from "@/lib/contact";
import { PAYMENTS_OPEN } from "@/lib/flags";
import "./globals.css";

export const metadata: Metadata = {
  title: "JOB HUNTER | Daily tech jobs for 0–2, 2–4, 4–6 and 6+ years",
  description:
    "Daily tech job alerts on Telegram for freshers to 6+ years of experience in AI, ML, Data Engineering, Data Analytics, Full Stack and Software Engineering. Remote and office roles in India, twice a day at 10 AM and 6 PM.",
};

export const viewport: Viewport = { themeColor: "#0d0718", colorScheme: "dark" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="nav">
          <Link href="/" className="brand">
            <span className="logo">JH</span> JOB HUNTER
          </Link>
          <nav>
            <Link href="/today">Sample jobs</Link>
            {PAYMENTS_OPEN ? (
              <Link href="/#subscribe" className="nav-cta">
                Subscribe
              </Link>
            ) : (
              <a href={FREE_JOIN_URL} className="nav-cta" target="_blank" rel="noopener noreferrer">
                Join free
              </a>
            )}
          </nav>
        </header>
        <main>{children}</main>
        <footer className="footer">
          <p>
            Daily tech job alerts, freshers to 6+ years
          </p>
          <p>
            <Link href="/terms">Terms</Link> · <Link href="/refunds">Cancellation &amp; Refunds</Link> ·{" "}
            <Link href="/privacy">Privacy</Link> · <Link href="/contact">Contact</Link>
          </p>
          <p className="muted">Jobs link to the company&apos;s own career page. Always check details before applying.</p>
        </footer>
      </body>
    </html>
  );
}
