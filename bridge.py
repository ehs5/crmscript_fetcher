# Bridge between frontend (Vue.js) and backend (Python)
# Exposes Python functions called by Vue.js.
import eel
from tenant_service import TenantService

# Tenant Settings Service methods
tenant_service = TenantService()
eel.expose(tenant_service.get_all_tenants)
eel.expose(tenant_service.add_tenant)
eel.expose(tenant_service.update_tenant)