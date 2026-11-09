import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { TELEGRAM_URL } from "@/lib/links";
import "./globals.css";

export const metadata: Metadata = {
  title: "Fresher Job Hunt | Daily tech jobs for 0–2, 2–4, 4–6 and 6+ years",
  description:
    "Free daily tech job alerts for freshers to 6+ years of experience in AI, ML, Data Engineering, Data Analytics, Full Stack and Software Engineering. Remote and office roles in India, every day at 10 AM.",
};

export const viewport: Viewport = { themeColor: "#0d0718", colorScheme: "dark" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="nav">
          <Link href="/" className="brand">
            <span className="logo">FJ</span> Fresher Job Hunt
          </Link>
          <nav>
            <Link href="/today">Today&apos;s jobs</Link>
            <a href={TELEGRAM_URL} className="nav-cta" target="_blank" rel="noopener noreferrer">
              Join Telegram
            </a>
          </nav>
        </header>
        <main>{children}</main>
        <footer className="footer">
          <p>
            Free daily tech job alerts, freshers to 6+ years · <Link href="/privacy">Privacy</Link>
          </p>
          <p className="muted">Jobs link to the company&apos;s own career page. Always check details before applying.</p>
        </footer>
      </body>
    </html>
  );
}
