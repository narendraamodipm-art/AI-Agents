"use client";

import { markJoined } from "@/lib/joined";
import { TELEGRAM_URL } from "@/lib/links";

/** A link to the Telegram channel. Clicking it unlocks the Apply buttons. */
export default function TelegramLink({
  className,
  onJoin,
  children,
}: {
  className?: string;
  onJoin?: () => void;
  children: React.ReactNode;
}) {
  return (
    <a
      className={className}
      href={TELEGRAM_URL}
      target="_blank"
      rel="noopener noreferrer"
      onClick={() => {
        markJoined();
        onJoin?.();
      }}
    >
      {children}
    </a>
  );
}
