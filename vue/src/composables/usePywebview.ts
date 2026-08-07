import type { FetchResult } from "@/types/FetchResult"
import type { TenantSettings } from "@/types/TenantSettings"

/**
 * Interface defining all available methods exposed in Python via pywebview's
 * js_api. Unlike Eel, each method resolves directly to a Promise (no double
 * call `()()` needed).
 */
export interface PywebviewApi {
  // Tenant settings CRUD methods
  get_all_tenants(initial_load?: boolean): Promise<TenantSettings[]>
  update_tenant(tenant: TenantSettings): Promise<void>
  add_tenant(tenant: TenantSettings): Promise<TenantSettings>
  delete_tenant(tenant_id: number): Promise<void>

  // Fetch methods
  fetch(tenant: TenantSettings): Promise<FetchResult>

  // Other utility methods
  get_fetcher_script(): Promise<string>
  ask_directory_path(): Promise<string>
  open_directory(directory_path: string): Promise<void>
  get_current_version(): Promise<string>
}

// pywebview injects window.pywebview (and populates .api) once the native
// window has finished loading the page - see the pywebviveready wait in main.ts.
declare global {
  interface Window {
    pywebview: {
      api: PywebviewApi
    }
  }
}

/**
 * Composable that provides type-safe access to all pywebview API methods.
 * Wraps the global 'window.pywebview.api' object with a more convenient camelCase API.
 */
export function usePywebview() {
  const api = window.pywebview.api

  return {
    getAllTenants: (initial_load: boolean = false) => api.get_all_tenants(initial_load),
    updateTenant: (tenant: TenantSettings) => api.update_tenant(tenant),
    addTenant: (tenant: TenantSettings) => api.add_tenant(tenant),
    deleteTenant: (tenant_id: number) => api.delete_tenant(tenant_id),
    fetch: (tenant: TenantSettings) => api.fetch(tenant),
    getFetcherScript: () => api.get_fetcher_script(),
    askDirectoryPath: () => api.ask_directory_path(),
    openDirectory: (directory_path: string) => api.open_directory(directory_path),
    getCurrentVersion: () => api.get_current_version(),
  }
}
