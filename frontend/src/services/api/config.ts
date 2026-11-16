/**
 * API configuration.
 *
 * VITE_API_BASE_URL  – where your FastAPI app runs (default http://localhost:8000)
 * VITE_API_KEY       – optional, sent as X-API-Key (backend QS_API_KEY)
 * VITE_USE_MOCK_DATA – "true" (default) serves the bundled demo data;
 *                      set to "false" to call the real backend.
 */
export const API_BASE_URL: string =
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "http://localhost:8000";

/** Optional. Sent as the X-API-Key header; must equal QS_API_KEY on the backend. Visible to anyone who opens the site: demos only. */
export const API_KEY: string = (import.meta.env["VITE_API_KEY"] as string | undefined) ?? "";

export const USE_MOCK_DATA: boolean =
  (import.meta.env["VITE_USE_MOCK_DATA"] as string | undefined) !== "false";
