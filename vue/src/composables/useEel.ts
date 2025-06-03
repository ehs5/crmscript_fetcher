import type { FetchResult } from "@/types/FetchResult"
import type { TenantSettings } from "@/types/TenantSettings"

/**
 * Interface defining all available methods exposed in Python via Eel.
 * Each method returns a function that returns a Promise, hence the two ()()s.
 */
export interface Eel {
  // The localhost path to the eel server
  _host: string

  // Tenant settings CRUD methods
  get_all_tenants(initial_load?: boolean): () => Promise<TenantSettings[]>
  update_tenant(tenant: TenantSettings): () => Promise<void>
  add_tenant(tenant: TenantSettings): () => Promise<TenantSettings>
  delete_tenant(tenant_id: number): () => Promise<void>

  // Fetch methods
  fetch(tenant: TenantSettings): () => Promise<FetchResult>

  // Other utility methods
  get_fetcher_script(): () => Promise<string>
  ask_directory_path(): () => Promise<string>
  open_directory(directory_path: string): () => Promise<void>
  get_current_version(): () => Promise<string>
}

// Tell TypeScript that 'eel' exists (it's been imported in index.html)
export declare const eel: Eel

/**
 * Composable that provides type-safe access to all Eel API methods.
 * Wraps the global 'eel' object with a more convenient API that also lets us know about the types of the methods.
 */
export function useEel() {
  return {
    getAllTenants: (initial_load: boolean = false) => eel.get_all_tenants(initial_load)(),
    updateTenant: (tenant: TenantSettings) => eel.update_tenant(tenant)(),
    addTenant: (tenant: TenantSettings) => eel.add_tenant(tenant)(),
    deleteTenant: (tenant_id: number) => eel.delete_tenant(tenant_id)(),
    fetch: (tenant: TenantSettings) => eel.fetch(tenant)(),
    getFetcherScript: () => eel.get_fetcher_script()(),
    askDirectoryPath: () => eel.ask_directory_path()(),
    openDirectory: (directory_path: string) => eel.open_directory(directory_path)(),
    getCurrentVersion: () => eel.get_current_version()(),
  }
}
