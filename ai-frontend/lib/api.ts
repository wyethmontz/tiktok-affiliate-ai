import { getSupabase } from "./supabase";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/**
 * Returns headers with the current Supabase access token attached as Bearer.
 * Use for any backend route that is auth-gated server-side (generate-ad,
 * regenerate-video, upload-image, upload-video).
 */
export async function authHeaders(): Promise<Record<string, string>> {
  if (typeof window === "undefined") return {};
  try {
    const { data } = await getSupabase().auth.getSession();
    const token = data?.session?.access_token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}
