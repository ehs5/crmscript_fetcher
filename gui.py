from main import Fetch
from main import TenantSettingsJson

from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import sv_ttk
import subprocess

global app


# ON CLICK BUTTON ACTIONS
def button_folder_browse():
    directory = filedialog.askdirectory()
    if directory:
        label_local_directory_path.config(text=directory)
    else:
        pass


def tenant_is_valid_for_save(tenant_id, tenant_name, local_directory):
    ts = TenantSettingsJson()
    tenant_is_valid = True
    message = "Could not save tenant:\n"

    if tenant_name == "":
        message = message + "\n- Tenant name cannot be empty"
        tenant_is_valid = False

    if ts.local_directory_already_used_by_tenant(tenant_id, local_directory):
        message = message + "\n- The local directory is already used by another tenant."
        tenant_is_valid = False

    if tenant_is_valid:
        return True
    messagebox.showerror("Error", message)


def click_button_save():
    # Tenant must have a name, and local directly can't be used for another tenant. More validations are done at fetch.
    tenant_id = get_selected_tenant_in_tree().get("id")
    tenant_name = e_tenant_name.get()
    local_directory = label_local_directory_path.cget("text")

    if tenant_is_valid_for_save(tenant_id, tenant_name, local_directory):
        updated_tenant = {
            "id": tenant_id,
            "include_id": e_include_id.get(),
            "key": e_key.get(),
            "local_directory": local_directory,
            "tenant_name": tenant_name,
            "url": e_superoffice_url.get()
        }

        ts = TenantSettingsJson()
        ts.update_tenant_in_json(updated_tenant)

        # Reload tree in order to reflect any changes in tenant name. Then re-set focus to same tenant.
        tree_load_tenants()
        for child in tree.get_children():
            if tree.item(child)["values"][1] == tenant_id:
                tree.selection_set(child)
                break
        tenant_settings_buttons_normal_state()


def click_button_reset():
    tenant = get_selected_tenant_in_tree()
    load_tenant_settings_to_gui(tenant)

    # Disable save/reset buttons
    button_save.configure(state=DISABLED)
    button_reset.configure(state=DISABLED)

    # Activate fetch/file explorer buttons
    button_fetch.configure(state=NORMAL)
    button_open_file_explorer.configure(state=NORMAL)
    print("Changes reset")


def click_button_add_tenant():
    ts = TenantSettingsJson()
    new_tenant = ts.add_tenant_to_json()

    tree_load_tenants()
    tree_set_focus_to_last_child()
    load_tenant_settings_to_gui(new_tenant)
    tenant_settings_buttons_normal_state()
    print("Tenant added")


def click_button_delete_tenant():
    ts = TenantSettingsJson()
    if ts.get_no_of_tenants_in_json() > 1:
        if messagebox.askquestion("Delete tenant",
                                  "You are about to delete the tenant. Are you sure you want to continue?\n\n"
                                  "Note! Only the settings will be removed, not the local directory itself.") == "yes":
            ts.delete_tenant_from_json(get_selected_tenant_in_tree(), )

            tree_load_tenants()
            tree_set_focus_to_last_child()
            load_tenant_settings_to_gui(ts.get_last_tenant_in_json())
            tenant_settings_buttons_normal_state()
            print("Tenant deleted")
    else:
        messagebox.showinfo("Can't delete tenant",
                            "You are not allowed to delete the only tenant. "
                            "Consider changing the values of the selected tenant instead.")


def click_button_fetch():
    tenant = get_selected_tenant_in_tree()
    if tenant_is_valid_for_fetch(tenant):
        if messagebox.askquestion("Fetch CRMScripts",
                                  "You are about to fetch CRMScripts from SuperOffice.\n\n"
                                  "Note: Any files or folders inside the Scripts and Triggers folders "
                                  "that are not present in Superoffice will be deleted.\n\n"
                                  "Do you want to continue?") == "yes":

            fetch = Fetch(tenant)
            if fetch.fetch():
                messagebox.showinfo("Success", "CRMScripts fetched successfully!")
            else:
                messagebox.showerror("Error", "Could not fetch from CRMScripts from tenant.")


def click_button_open_file_explorer():
    local_directory = get_selected_tenant_in_tree().get("local_directory").replace("/", "\\")
    subprocess.Popen(f'explorer "{local_directory}"')
    print(f"Opened folder in File Explorer: {local_directory}")


def click_button_copy_fetcher_script():
    try:
        with open("crmscript_fetcher.crmscript") as f:
            app.clipboard_clear()
            app.clipboard_append(f.read())
    except FileNotFoundError:
        try:
            with open("CRMScript Fetcher.crmscript") as f:
                app.clipboard_clear()
                app.clipboard_append(f.read())
        except FileNotFoundError:
            messagebox.showerror("Could not copy fetcher script to clipboard",
                                 "Could not find the fetcher script."
                                 " The script must be in this app's root folder"
                                 " with the name \"crmscript_fetcher.crmscript\".")


# OTHER FUNCTIONS
# Disables save/reset buttons and activates fetch/file explorer buttons
def tenant_settings_buttons_normal_state():
    button_save.configure(state=DISABLED, style="TButton")
    button_reset.configure(state=DISABLED)
    button_fetch.configure(state=NORMAL)
    button_open_file_explorer.configure(state=NORMAL)


def get_selected_tenant_in_tree():
    ts = TenantSettingsJson()
    values = tree.item(tree.selection()).get("values")
    if len(values) > 0:
        tenant_id = values[1]
        return ts.get_tenant_by_id(tenant_id)


def tenant_is_valid_for_fetch(tenant):
    tenant_is_valid = True
    message = "Can not fetch CRMScripts because tenant settings are invalid:\n"

    if tenant.get("include_id") == "":
        message = message + "\n- Script include ID cannot be empty"
        tenant_is_valid = False

    if tenant.get("key") == "":
        message = message + "\n- Script key cannot be empty"
        tenant_is_valid = False

    if tenant.get("url") == "":
        message = message + "\n- SuperOffice Service URL cannot be empty"
        tenant_is_valid = False

    if tenant.get("local_directory") == "":
        message = message + "\n- Local directory path cannot be empty"
        tenant_is_valid = False

    if tenant_is_valid:
        return True
    messagebox.showerror("Error", message)


def tree_set_focus_to_last_child():
    last_child_id = tree.get_children()[-1]
    tree.focus(last_child_id)
    tree.selection_set(last_child_id)


# EVENT CALLBACKS
# Navbar callback when clicking a tenant. Returns selected tenant dict from json
def tree_click(event):
    tenant = get_selected_tenant_in_tree()
    load_tenant_settings_to_gui(tenant)
    tenant_settings_buttons_normal_state()


# Callback when having changed settings of a tenant, turns button clickable
def tenant_settings_changed(event):
    button_save.configure(state=NORMAL, style="Accent.TButton")
    button_reset.configure(state=NORMAL)

    # Disable fetch and file explorer buttons to make sure user don't try to fetch/open from unsaved changes
    button_fetch.configure(state=DISABLED)
    button_open_file_explorer.configure(state=DISABLED)


# FUNCTIONS FOR LOADING DATA INTO GUI
# Load the fields for the given tenant into the tenant settings section of the screen
def load_tenant_settings_to_gui(tenant):
    e_tenant_name.delete(0, last=END)
    e_tenant_name.insert(0, tenant.get("tenant_name"))

    e_superoffice_url.delete(0, last=END)
    e_superoffice_url.insert(0, tenant.get("url"))

    e_include_id.delete(0, last=END)
    e_include_id.insert(0, tenant.get("include_id"))

    e_key.delete(0, last=END)
    e_key.insert(0, tenant.get("key"))

    folder_path = tenant.get("local_directory")
    label_local_directory_path.configure(text=folder_path)


# Load all tenants that exists in json into tree. Can either be used for loading first time or reloading
def tree_load_tenants():
    # Delete the tenants in the gui
    for child in tree.get_children():
        tree.delete(child)

    # Insert tenants from tenant settings JSON
    ts = TenantSettingsJson()
    for t in ts.tenant_settings:
        tree.insert("", "end", values=(t.get("tenant_name"), t.get("id")), tags="cb")


# Navbar column, top
class NavBarListFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        # Treeview
        global tree
        tree = ttk.Treeview(self,
                            selectmode="browse",
                            columns=("1", "2"),
                            show="headings",
                            displaycolumns="1",
                            height=11
                            )

        # tree.grid(column=0, row=0)
        tree.pack(expand=True, fill="both", side="left")
        tree.column("1", anchor='w')
        tree.column("2")
        tree.heading("1", text="--Tenants--")
        tree.heading("2", text="id")

        # Scrollbar
        tree_scrollbar = ttk.Scrollbar(self, orient="vertical", command=tree.yview)
        # tree_scrollbar.grid(column=1, row=0, rowspan="2", sticky="nsw")
        tree_scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=tree_scrollbar.set)

        # Event binding for treeview
        tree.tag_bind("<1>", tree_click)
        tree.bind("<ButtonRelease-1>", tree_click)


# Navbar column, bottom
class NavBarButtonsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        global button_add_tenant
        add_tenant = ttk.Button(self, text="Add tenant", command=click_button_add_tenant)
        add_tenant.grid(column=0, row=0)

        global button_delete_tenant
        delete_tenant = ttk.Button(self, text="Delete tenant", command=click_button_delete_tenant)
        delete_tenant.grid(column=1, row=0, padx=5)


# Left column, nav bar frame
class NavBarFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        label_heading = ttk.Label(self, text="Your tenants", font="Segoe_UI 12 bold")
        label_heading.grid(column=0, row=0, sticky="nw", ipady=10)

        # Treeview
        navbar_list_frame = NavBarListFrame(self)
        navbar_list_frame.grid(column=0, row=1, sticky="nw")

        navbar_buttons_frame = NavBarButtonsFrame(self)
        navbar_buttons_frame.grid(column=0, row=2, sticky="sw")


# Tenant save/reset buttons frame
class TenantButtonsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        global button_save
        button_save = ttk.Button(self,
                                 text="Save settings",
                                 command=click_button_save,
                                 style="TButton",
                                 state=DISABLED, )

        button_save.grid(row=6, column=0, sticky="w")

        global button_reset
        button_reset = ttk.Button(self,
                                  text="Reset settings",
                                  command=click_button_reset,
                                  style="TButton",
                                  state=DISABLED)

        button_reset.grid(row=6, column=1, sticky="w", padx=5)


# Main content frame, top
class TenantContentFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        # Row 0 - Heading
        label_heading = ttk.Label(self, text="Tenant settings", font="Segoe_UI 12 bold")
        label_heading.grid(column=0, row=0, sticky="w", ipady=10)

        # Row 1 - Tenant name
        label_tenant_name = ttk.Label(self, text="Tenant name")
        label_tenant_name.grid(row=1, column=0, sticky="w")

        global e_tenant_name
        e_tenant_name = ttk.Entry(self, width=50)
        e_tenant_name.grid(row=1, column=1, sticky="w")

        # Row 2 - SuperOffice Service URL
        label_superoffice_url = ttk.Label(self, text="SuperOffice Service URL   ")
        label_superoffice_url.grid(row=2, column=0, sticky="w")

        global e_superoffice_url
        e_superoffice_url = ttk.Entry(self, width=50)
        e_superoffice_url.grid(row=2, column=1, sticky="w")

        # Row 3 - Script Include ID
        label_include_id = ttk.Label(self, text="Script include ID")
        label_include_id.grid(row=3, column=0, sticky="w")

        global e_include_id
        e_include_id = ttk.Entry(self, width=50)
        e_include_id.grid(row=3, column=1, sticky="w")

        # Row 4 - Script key
        label_key = ttk.Label(self, text="Script key")
        label_key.grid(row=4, column=0, sticky="w")

        global e_key
        e_key = ttk.Entry(self, width=50)
        e_key.grid(row=4, column=1, sticky="w")

        # Row 5 - Local directory
        label_local_directory = ttk.Label(self, text="Local directory")
        label_local_directory.grid(row=5, column=0, sticky="w")

        global label_local_directory_path
        label_local_directory_path = ttk.Label(self)
        label_local_directory_path.grid(row=5, column=1, sticky="w")

        button_local_directory = ttk.Button(self, text="Browse", command=button_folder_browse, style="TButton")
        button_local_directory.grid(row=5, column=3, sticky="w", padx=10)

        # Event bindings for entry fields
        e_tenant_name.bind('<KeyPress>', tenant_settings_changed)
        e_superoffice_url.bind('<KeyPress>', tenant_settings_changed)
        e_include_id.bind('<KeyPress>', tenant_settings_changed)
        e_key.bind('<KeyPress>', tenant_settings_changed)
        button_local_directory.bind('<ButtonRelease>', tenant_settings_changed)

        # Row 6 - Tenant save/reset settings buttons frame
        frame_tenant_buttons = TenantButtonsFrame(self)
        frame_tenant_buttons.grid(row=6, column=0, columnspan=2, sticky="w")


# Main content frame, bottom
class ContentBottomButtons(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        global button_fetch
        button_fetch = ttk.Button(self,
                                  text="Fetch CRMScripts",
                                  style="Accent.TButton",
                                  command=click_button_fetch)
        button_fetch.grid(column=0, row=0)

        global button_open_file_explorer
        button_open_file_explorer = ttk.Button(self,
                                               text="Open in File Explorer",
                                               style="TButton",
                                               command=click_button_open_file_explorer)
        button_open_file_explorer.grid(row=0, column=1, padx=5)

        button_copy_fetcher_script = ttk.Button(self,
                                                text="Copy Fetcher script to clipboard",
                                                style="TButton",
                                                command=click_button_copy_fetcher_script)

        spacer = ttk.Label(self, text="")
        spacer.grid(row=0, column=2, ipadx=50)

        button_copy_fetcher_script.grid(row=0, column=3)


# Right column, main content frame
class ContentFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        frame_tenant_content = TenantContentFrame(self)
        frame_tenant_content.grid(column=0, row=0, ipady=51)

        frame_content_bottom_buttons = ContentBottomButtons(self)
        frame_content_bottom_buttons.grid(column=0, row=1, sticky="sw")


# Main frame, provides outer padding as defined in App class
class MainFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        frame_navbar = NavBarFrame(self)
        frame_navbar.grid(column=0, row=0, sticky="nw", padx=10, ipadx=5, ipady=5)

        frame_content = ContentFrame(self)
        frame_content.grid(column=1, row=0, sticky="nw")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CRMScript Fetcher")
        self.iconbitmap("icon.ico")
        self.minsize(width=870, height=400)
        self.resizable(0, 0)
        sv_ttk.use_light_theme()

        self.create_widgets()
        self.load_tenants()

    def create_widgets(self):
        main_frame = MainFrame(self)
        main_frame.grid(column=0, row=0, padx=10)

    @staticmethod
    def load_tenants():
        """Loads all available tenants to left side tree(navbar),
        sets focus to first tenant and then loads its tenant settings"""

        tree_load_tenants()
        tree_children = tree.get_children()
        if len(tree_children) > 0:
            child_id = tree_children[0]

            # Set focus in tree
            tree.focus(child_id)
            tree.selection_set(child_id)

            # Load tenant settings for selected tenant
            selected_tenant = get_selected_tenant_in_tree()
            load_tenant_settings_to_gui(selected_tenant)


if __name__ == "__main__":
    app = App()
    app.mainloop()
