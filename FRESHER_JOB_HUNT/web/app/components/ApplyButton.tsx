"use client";

import { useEffect, useRef, useState } from "react";
import { hasJoined } from "@/lib/joined";
import TelegramLink from "./TelegramLink";

/**
 * Opens the job only once the visitor has clicked a Telegram join link; otherwise asks them to join first.
 * Takes the job's id, not its URL, so company links never reach the page. /apply/[id] redirects to them.
 */
export default function ApplyButton({ id, title }: { id: number; title: string }) {
  const [asking, setAsking] = useState(false);

  function apply() {
    if (hasJoined()) window.open(`/apply/${id}`, "_blank", "noopener,noreferrer");
    else setAsking(true);
  }

  return (
    <>
      <button type="button" className="btn small" onClick={apply} aria-label={`Apply: ${title}`}>
        Apply →
      </button>
      {asking && <JoinDialog id={id} onClose={() => setAsking(false)} />}
    </>
  );
}

function JoinDialog({ id, onClose }: { id: number; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [joined, setJoined] = useState(false);

  useEffect(() => {
    ref.current?.showModal();
  }, []);

  return (
    <dialog ref={ref} className="join-dialog" onClose={onClose} aria-labelledby="join-dialog-title">
      <span className="tg-icon" aria-hidden="true">
        ✈️
      </span>
      {joined ? (
        <>
          <h3 id="join-dialog-title">Thanks for joining! 🎉</h3>
          <p>Apply links are unlocked. New jobs reach you on Telegram every day at 10 AM.</p>
          <a
            className="btn primary"
            href={`/apply/${id}`}
            target="_blank"
            rel="noopener noreferrer nofollow"
            onClick={() => ref.current?.close()}
          >
            Continue to apply →
          </a>
        </>
      ) : (
        <>
          <h3 id="join-dialog-title">Join our Telegram channel to apply</h3>
          <p>Apply links unlock after you join. It&apos;s free, and new jobs reach you every day at 10 AM.</p>
          <TelegramLink className="btn telegram block" onJoin={() => setJoined(true)}>
            Join the Telegram channel
          </TelegramLink>
          <button type="button" className="dialog-later" onClick={() => ref.current?.close()}>
            Not now
          </button>
        </>
      )}
    </dialog>
  );
}
