import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Fresher Job Hunt | Daily jobs for 0–2 years",
  description:
    "Free daily job and internship alerts for freshers (0–2 years) in AI, ML, Data Engineering, Data Analytics, Full Stack and Software Engineering. Remote and office roles in India, every day at 10 AM.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f7f8fc" },
    { media: "(prefers-color-scheme: dark)", color: "#0b0f19" },
  ],
};

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
            <Link href="/#signup" className="nav-cta">
              Sign up
            </Link>
          </nav>
        </header>
        <main>{children}</main>
        <footer className="footer">
          <p>
            Free daily job alerts for freshers · <Link href="/privacy">Privacy</Link>
          </p>
          <p className="muted">Jobs link to the company&apos;s own career page. Always check details before applying.</p>
        </footer>
      </body>
    </html>
  );
}
