// Remembers in this browser that the visitor clicked a Telegram join link.
// Telegram can't tell the site who joined without a Telegram login, so this records the click only.
export const JOINED_COOKIE = "tg_joined";

export function hasJoined() {
  return document.cookie.split("; ").includes(`${JOINED_COOKIE}=1`);
}

export function markJoined() {
  document.cookie = `${JOINED_COOKIE}=1; path=/; max-age=31536000; samesite=lax`;
}
