import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "JOB HUNTER | Daily tech jobs for 0–2, 2–4, 4–6 and 6+ years",
  description:
    "Daily tech job alerts on Telegram for freshers to 6+ years of experience in AI, ML, Data Engineering, Data Analytics, Full Stack and Software Engineering. Remote and office roles in India, every day at 10 AM.",
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
            <Link href="/#subscribe" className="nav-cta">
              Subscribe
            </Link>
          </nav>
        </header>
        <main>{children}</main>
        <footer className="footer">
          <p>
            Daily tech job alerts, freshers to 6+ years · <Link href="/privacy">Privacy</Link>
          </p>
          <p className="muted">Jobs link to the company&apos;s own career page. Always check details before applying.</p>
        </footer>
      </body>
    </html>
  );
}
