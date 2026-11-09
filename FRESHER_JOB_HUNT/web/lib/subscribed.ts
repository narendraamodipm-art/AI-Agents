// Remembers in this browser that the visitor has subscribed, which unlocks the website's Apply buttons.
export const SUBSCRIBED_COOKIE = "premium_member";

export function hasSubscribed() {
  return document.cookie.split("; ").includes(`${SUBSCRIBED_COOKIE}=1`);
}

export function markSubscribed() {
  document.cookie = `${SUBSCRIBED_COOKIE}=1; path=/; max-age=2678400; samesite=lax`; // 31 days
}
