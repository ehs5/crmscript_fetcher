/**
 * The result after fetching data from a tenant.
 */
export interface FetchResult {
  success: boolean
  validation_error: boolean
  error: string
  info: string
}
