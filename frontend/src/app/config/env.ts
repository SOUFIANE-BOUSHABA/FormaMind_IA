import { z } from "zod";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

const envSchema = z.object({
  VITE_API_BASE_URL: z.string().url(),
});

export const env = envSchema.parse({
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
});
