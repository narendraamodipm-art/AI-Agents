import "server-only";

/** Supabase REST call using the server-only secret key. Row Level Security blocks every other key. */
export async function rest<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error("Supabase is not configured");
  const r = await fetch(`${url.replace(/\/$/, "")}/rest/v1/${path}`, {
    ...(init.next ? {} : { cache: "no-store" as const }),
    ...init,
    headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json", ...init.headers },
  });
  if (!r.ok) throw new Error(`Supabase ${init.method ?? "GET"} ${path.split("?")[0]}: ${r.status} ${await r.text()}`);
  const text = await r.text();
  return (text ? JSON.parse(text) : null) as T;
}
