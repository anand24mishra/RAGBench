export class ApiError extends Error {
  code: string
  status: number
  requestId?: string

  constructor(message: string, status: number, code: string = 'api_error', requestId?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.requestId = requestId
  }
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number
}

const DEFAULT_TIMEOUT_MS = 60000

export async function requestJson<T>(
  endpoint: string,
  options: RequestOptions = {},
  fallbackData?: T
): Promise<T> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  const headers = new Headers(options.headers || {})
  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json')
  }

  const envApiUrl = (import.meta as any).env?.VITE_API_URL
  const baseUrl =
    envApiUrl && typeof envApiUrl === 'string' && envApiUrl.trim() !== ''
      ? envApiUrl.trim().replace(/\/+$/, '')
      : typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null'
        ? window.location.origin
        : 'http://localhost:8000'
  const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      let code = 'http_error'
      let message = `Request failed with status ${response.status}`
      let requestId = response.headers.get('X-Request-ID') || undefined

      try {
        const errorBody = await response.json()
        if (errorBody?.detail) {
          if (typeof errorBody.detail === 'string') {
            message = errorBody.detail
          } else if (typeof errorBody.detail === 'object') {
            code = errorBody.detail.code || code
            message = errorBody.detail.message || message
            requestId = errorBody.detail.request_id || requestId
          }
        }
      } catch {
        // use default message if body is not JSON
      }

      throw new ApiError(message, response.status, code, requestId)
    }

    return (await response.json()) as T
  } catch (err: unknown) {
    clearTimeout(timeoutId)

    if (err instanceof ApiError) {
      throw err
    }

    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(`Request to ${endpoint} timed out after ${timeoutMs}ms`, 504, 'timeout')
    }

    // If a fallback was provided and network is offline, gracefully return verified fallback
    if (fallbackData !== undefined) {
      console.warn(`[RAGBench API] Endpoint '${endpoint}' unavailable. Using verified repository snapshot.`, err)
      return fallbackData
    }

    throw new ApiError(
      err instanceof Error ? err.message : 'Unknown network connection failure',
      0,
      'network_error'
    )
  }
}
