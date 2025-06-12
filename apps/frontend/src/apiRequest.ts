// Centralized API utility for backend requests
// Uses fetch API and handles authentication, errors, etc.

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const url = `${baseUrl}${endpoint}`;

  const res = await fetch(url, {
    credentials: 'include', // send cookies for auth if needed
    headers: {
      'Content-Type': 'application/json',
      'x-user-email': 'dev@local', // TODO: replace with real user or env var in production
      'x-user-role': 'admin',      // TODO: replace with real role or env var in production
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    // Optionally handle auth errors, redirects, etc.
    const error = await res.text();
    throw new Error(error || res.statusText);
  }
  if (res.status === 204) return undefined as any;
  return res.json();
}

// Example usage:
// const data = await apiRequest('/incidents/');
