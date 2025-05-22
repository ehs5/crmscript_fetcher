# Using eel, this file exposes Python functions so that Vue.js can call them
import tkinter

import eel
from tenant_service import TenantService
from tkinter import filedialog
import sv_ttk

# Exposing Tenant Service methods
tenant_service = TenantService()
eel.expose(tenant_service.get_all_tenants)
eel.expose(tenant_service.add_tenant)
eel.expose(tenant_service.update_tenant)

# Other methods
@eel.expose
def ask_directory_path() -> str:
    """
    Opens a tkinter dialog box and returns the folder path that user selected.
    #TODO: Should this be in gui.py file maybe?
    """
    #root = tkinter.Tk
    #root.withdraw()
    #sv_ttk.use_light_theme()
    return filedialog.askdirectory() #TODO How's this looking on Windows?
