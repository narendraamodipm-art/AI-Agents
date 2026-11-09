"use client";

import { useEffect, useRef, useState } from "react";
import { hasSubscribed } from "@/lib/subscribed";

/**
 * Opens the job only for subscribers; everyone else is asked to subscribe.
 * Takes the job's id, not its URL, so company links never reach the page. /apply/[id] redirects to them.
 */
export default function ApplyButton({ id, title }: { id: number; title: string }) {
  const [asking, setAsking] = useState(false);

  function apply() {
    if (hasSubscribed()) window.open(`/apply/${id}`, "_blank", "noopener,noreferrer");
    else setAsking(true);
  }

  return (
    <>
      <button type="button" className="btn small" onClick={apply} aria-label={`Apply: ${title}`}>
        Apply →
      </button>
      {asking && <SubscribeDialog onClose={() => setAsking(false)} />}
    </>
  );
}

function SubscribeDialog({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    ref.current?.showModal();
  }, []);

  return (
    <dialog ref={ref} className="join-dialog" onClose={onClose} aria-labelledby="join-dialog-title">
      <h3 id="join-dialog-title">Subscribe to apply</h3>
      <p>Apply links are for Premium members. For ₹99/month you get every job in our private Telegram channel.</p>
      <a className="btn primary" href="/#subscribe" onClick={() => ref.current?.close()}>
        See Premium
      </a>
      <button type="button" className="dialog-later" onClick={() => ref.current?.close()}>
        Not now
      </button>
    </dialog>
  );
}
