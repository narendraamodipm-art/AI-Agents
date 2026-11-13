// Payments are paused unless PAYMENTS_OPEN=true is set (in Vercel: Settings → Environment Variables, then redeploy).
export const PAYMENTS_OPEN = process.env.PAYMENTS_OPEN === "true";
