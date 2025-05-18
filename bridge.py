import eel
from tenant_settings import TenantSettingsJson


@eel.expose()
def get_tenant_settings() -> list[dict]:
    # TODO: Should we load it just once, across methods?
    ts = TenantSettingsJson(add_fetch_options=True)
    return ts.tenant_settings