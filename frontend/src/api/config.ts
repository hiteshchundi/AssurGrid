// Empty means same-origin: Vite proxies locally; Vercel forwards to Render when hosted.
export const baseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ?? '';
export const requestTimeout = 75000; // Allow a free Render instance to wake from idle.
