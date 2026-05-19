const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function apiFetch(path, options = {}) {
  const token = localStorage.getItem('access_token')
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  return res.json()
}
