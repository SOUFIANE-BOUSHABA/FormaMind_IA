import { env } from "@/app/config/env";

export type ApiRequestOptions = Omit<RequestInit, "body"> & {
  accessToken?: string;
  json?: unknown;
};

export class ApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(status: number, payload: unknown) {
    super(`API request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

async function readResponsePayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

export async function apiRequest<TResponse>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<TResponse> {
  const headers = new Headers(options.headers);
  const requestInit: RequestInit = {
    ...options,
    credentials: options.credentials ?? "include",
    headers,
  };

  if (options.accessToken !== undefined) {
    headers.set("Authorization", `Bearer ${options.accessToken}`);
  }

  if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
    requestInit.body = JSON.stringify(options.json);
  }

  const response = await fetch(`${env.VITE_API_BASE_URL}${path}`, requestInit);

  if (!response.ok) {
    throw new ApiError(response.status, await readResponsePayload(response));
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await readResponsePayload(response)) as TResponse;
}
