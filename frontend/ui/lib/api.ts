export const API_BASE = (process.env.NEXT_PUBLIC_TORQUE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try { response = await fetch(API_BASE + path, { ...options, credentials: 'include', cache: 'no-store' }); }
  catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiError('Cannot reach Torque. Check that the backend API is running.', 0);
  }
  const data = await response.json();
  if (!response.ok) throw new ApiError(typeof data.detail === 'string' ? data.detail : 'Request failed. Check your input and try again.', response.status);
  return data as T;
}
export const githubLogin = () => { window.location.assign(API_BASE + '/api/auth/github/connect'); };
