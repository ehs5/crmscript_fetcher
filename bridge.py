# Using eel, this file exposes Python functions so that Vue.js can call them
import eel

from fetch_service import FetchService
from tenant_service import TenantService
from utility import get_fetcher_script
from utility import ask_directory_path
from utility import open_directory

# Exposing Tenant Service methods
tenant_service = TenantService()
eel.expose(tenant_service.get_all_tenants)
eel.expose(tenant_service.add_tenant)
eel.expose(tenant_service.update_tenant)
eel.expose(tenant_service.delete_tenant)

# Exposing Fetch Service methods
fetch_service = FetchService()
eel.expose(fetch_service.fetch)

# Utility methods
eel.expose(get_fetcher_script)
eel.expose(ask_directory_path)
eel.expose(open_directory)