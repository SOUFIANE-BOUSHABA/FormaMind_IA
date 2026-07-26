import { env } from "@/app/config/env";

export type ApiRequestOptions = Omit<RequestInit, "body"> & {
  accessToken?: string;
  json?: unknown;
};

const API_REQUEST_TIMEOUT_MS = 15_000;

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

export class ApiNetworkError extends Error {
  constructor(message = "API request failed before receiving a response") {
    super(message);
    this.name = "ApiNetworkError";
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
  const { accessToken, json, signal, ...fetchOptions } = options;
  const headers = new Headers(options.headers);
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, API_REQUEST_TIMEOUT_MS);

  signal?.addEventListener(
    "abort",
    () => {
      controller.abort();
    },
    { once: true },
  );

  const requestInit: RequestInit = {
    ...fetchOptions,
    credentials: fetchOptions.credentials ?? "include",
    headers,
    signal: controller.signal,
  };

  if (accessToken !== undefined) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  if (json !== undefined) {
    headers.set("Content-Type", "application/json");
    requestInit.body = JSON.stringify(json);
  }

  let response: Response;

  try {
    response = await fetch(`${env.VITE_API_BASE_URL}${path}`, requestInit);
  } catch (error) {
    throw new ApiNetworkError(
      error instanceof DOMException && error.name === "AbortError"
        ? "API request timed out"
        : undefined,
    );
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readResponsePayload(response));
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await readResponsePayload(response)) as TResponse;
}
