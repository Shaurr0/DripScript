const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const DEFAULT_TIMEOUT = 30000;
const activeRequests = new Map();

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

function requestKey(method, url, body) {
  return `${method}:${url}:${typeof body === 'string' ? body : ''}`;
}

export function createAbortController() {
  return new AbortController();
}

export async function apiRequest(path, options = {}) {
  const {
    method = 'GET',
    headers = {},
    body,
    token,
    timeout = DEFAULT_TIMEOUT,
    signal,
    dedupe = false,
  } = options;

  const url = `${API_BASE}${path}`;
  const key = dedupe ? requestKey(method, url, body) : null;

  if (key && activeRequests.has(key)) {
    return activeRequests.get(key);
  }

  const controller = new AbortController();
  const combinedSignal = signal
    ? AbortSignal.any
      ? AbortSignal.any([signal, controller.signal])
      : signal
    : controller.signal;

  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const requestHeaders = { ...headers };
  if (token) {
    requestHeaders['Authorization'] = `Bearer ${token}`;
  }

  const fetchOptions = {
    method,
    headers: requestHeaders,
    signal: combinedSignal,
  };
  if (body !== undefined) {
    fetchOptions.body = body;
  }

  const promise = (async () => {
    try {
      const response = await fetch(url, fetchOptions);

      let data;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (response.status === 401) {
        throw new ApiError('Session expired. Please log in again.', 401, data);
      }

      if (!response.ok) {
        const message = data?.error || `Request failed (${response.status}).`;
        throw new ApiError(message, response.status, data);
      }

      return data;
    } catch (err) {
      if (err instanceof ApiError) throw err;
      if (err.name === 'AbortError') {
        throw new ApiError('Request was cancelled.', 0, null);
      }
      if (err.name === 'TypeError' || err.message?.includes('fetch')) {
        throw new ApiError('Cannot reach the server. Check your connection.', 0, null);
      }
      throw new ApiError(err.message || 'An unexpected error occurred.', 0, null);
    } finally {
      clearTimeout(timeoutId);
      if (key) activeRequests.delete(key);
    }
  })();

  if (key) {
    activeRequests.set(key, promise);
  }

  return promise;
}

export async function apiPostJson(path, payload, options = {}) {
  return apiRequest(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    body: JSON.stringify(payload),
    ...options,
  });
}

export async function apiPostForm(path, formData, options = {}) {
  return apiRequest(path, {
    method: 'POST',
    body: formData,
    ...options,
  });
}

export { API_BASE, ApiError };
