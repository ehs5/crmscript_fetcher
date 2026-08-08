export interface TenantSettings {
  id: number
  include_id: string
  key: string
  local_directory: string
  tenant_name: string
  url: string
  fetch_options: {
    fetch_scripts: boolean
    fetch_triggers: boolean
    fetch_screens: boolean
    fetch_screen_choosers: boolean
    fetch_scheduled_tasks: boolean
    fetch_extra_tables: boolean
  }
}
