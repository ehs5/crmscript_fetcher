from fetch import CURRENT_CRMSCRIPT_VERSION
from fetch import Fetch
from tenant_settings import TenantSettingsJson
from tenant_settings import construct_fetch_options

from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import sv_ttk
import subprocess


def tenant_settings_buttons_normal_state():
    """Disables save/reset buttons and activates fetch/file explorer buttons"""
    button_save.configure(state=DISABLED, style="TButton")
    button_reset.configure(state=DISABLED)
    button_fetch.configure(state=NORMAL)
    button_open_file_explorer.configure(state=NORMAL)


def get_selected_tenant_in_tree() -> dict | None:
    ts = TenantSettingsJson()
    values = tree.item(tree.selection()).get("values")
    if len(values) > 0:
        tenant_id = values[1]
        return ts.get_tenant_by_id(tenant_id)


def tree_set_focus_to_last_child():
    last_child_id = tree.get_children()[-1]
    tree.focus(last_child_id)
    tree.selection_set(last_child_id)


def tenant_is_valid_for_save(tenant_id, tenant_name, local_directory):
    ts = TenantSettingsJson()
    tenant_is_valid = True
    message = "Could not save tenant:\n"

    if tenant_name == "":
        message = message + "\n- Tenant name cannot be empty"
        tenant_is_valid = False

    if ts.local_directory_taken(tenant_id, local_directory):
        message = message + "\n- The local directory is already used by another tenant."
        tenant_is_valid = False

    if tenant_is_valid:
        return True
    else:
        messagebox.showerror("Error", message)
        return False


def tenant_is_valid_for_fetch(tenant):
    tenant_is_valid = True
    message = "Can not fetch CRMScripts because tenant settings are invalid:\n"

    if tenant.get("include_id") == "":
        message += "\n- Script include ID cannot be empty"
        tenant_is_valid = False

    if tenant.get("key") == "":
        message += "\n- Script key cannot be empty"
        tenant_is_valid = False

    if tenant.get("url") == "":
        message += "\n- SuperOffice Service URL cannot be empty"
        tenant_is_valid = False

    if tenant.get("local_directory") == "":
        message += "\n- Local directory path cannot be empty"
        tenant_is_valid = False

    if all(not option for option in tenant.get("fetch_options").values()):
        message += "\n- You must check at least one fetch option"
        tenant_is_valid = False

    if tenant_is_valid:
        return True

    messagebox.showerror("Error", message)


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
    # Clear out any tenants in GUI
    for child in tree.get_children():
        tree.delete(child)

    # Insert tenants from tenant settings JSON
    ts = TenantSettingsJson(add_fetch_options=True)
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

        tree.pack(expand=True, fill="both", side="left")
        tree.column("1", anchor='w')
        tree.column("2")
        tree.heading("1", text="--Tenants--")
        tree.heading("2", text="id")

        # Scrollbar
        tree_scrollbar = ttk.Scrollbar(self, orient="vertical", command=tree.yview)
        tree_scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=tree_scrollbar.set)

        # Event binding for treeview
        tree.tag_bind("<1>", self.callback_tree_click)
        tree.bind("<ButtonRelease-1>", self.callback_tree_click)

    @staticmethod
    def callback_tree_click(event):
        """Navbar callback when clicking a tenant. Returns selected tenant dict from json"""
        tenant: dict = get_selected_tenant_in_tree()
        load_tenant_settings_to_gui(tenant)
        tenant_settings_buttons_normal_state()


# Navbar column, bottom
class NavBarButtonsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        global button_add_tenant
        add_tenant = ttk.Button(self, text="Add tenant", command=self.click_button_add_tenant)
        add_tenant.grid(column=0, row=0)

        global button_delete_tenant
        delete_tenant = ttk.Button(self, text="Delete tenant", command=self.click_button_delete_tenant)
        delete_tenant.grid(column=1, row=0, padx=5)

    @staticmethod
    def click_button_add_tenant():
        ts = TenantSettingsJson()
        new_tenant = ts.add_tenant()

        tree_load_tenants()
        tree_set_focus_to_last_child()
        load_tenant_settings_to_gui(new_tenant)
        tenant_settings_buttons_normal_state()

    @staticmethod
    def click_button_delete_tenant():
        ts = TenantSettingsJson()
        if ts.get_no_of_tenants() > 1:
            question = "You are about to delete the tenant. Are you sure you want to continue?\n\n"\
                       "Note! Only the settings will be removed, not the local directory itself."
            if messagebox.askquestion("Delete tenant", question) == "yes":
                ts.delete_tenant(get_selected_tenant_in_tree())

                tree_load_tenants()
                tree_set_focus_to_last_child()
                load_tenant_settings_to_gui(ts.get_last_tenant())
                tenant_settings_buttons_normal_state()
        else:
            messagebox.showinfo("Can't delete tenant",
                                "You are not allowed to delete the only tenant. "
                                "Consider changing the values of the selected tenant instead.")


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
                                 command=self.click_button_save,
                                 style="TButton",
                                 state=DISABLED, )

        button_save.grid(row=6, column=0, sticky="w")

        global button_reset
        button_reset = ttk.Button(self,
                                  text="Reset settings",
                                  command=self.click_button_reset,
                                  style="TButton",
                                  state=DISABLED)

        button_reset.grid(row=6, column=1, sticky="w", padx=5)

        global button_fetch_options
        button_fetch_options = ttk.Button(self,
                                          text="Fetch options",
                                          command=self.click_button_fetch_options,
                                          style="TButton")
        button_fetch_options.grid(row=6, column=2, sticky="w", padx=5)

    @staticmethod
    def click_button_save():
        # Tenant must have a name, and local directly can't be used for another tenant.
        # More validations are done at fetch.
        tenant_id = get_selected_tenant_in_tree().get("id")
        tenant_name = e_tenant_name.get()
        local_directory = label_local_directory_path.cget("text")

        if not tenant_is_valid_for_save(tenant_id, tenant_name, local_directory):
            # Revert original tenant settings in tree
            selected_tenant = get_selected_tenant_in_tree()
            load_tenant_settings_to_gui(selected_tenant)
            tenant_settings_buttons_normal_state()
            return

        # Proceed to update tenant in tenant_settings.json
        updated_tenant = {
            "id": tenant_id,
            "include_id": e_include_id.get(),
            "key": e_key.get(),
            "local_directory": local_directory,
            "tenant_name": tenant_name,
            "url": e_superoffice_url.get()
        }
        ts = TenantSettingsJson()
        ts.update_tenant(updated_tenant)

        tenant_settings_buttons_normal_state()
        tree_load_tenants()

        # Reload tree in order to reflect any changes in tenant name. Then re-set focus to same tenant.
        tree_load_tenants()
        for child in tree.get_children():
            if tree.item(child)["values"][1] == tenant_id:
                tree.selection_set(child)
                break
        tenant_settings_buttons_normal_state()

    @staticmethod
    def click_button_reset():
        tenant: dict = get_selected_tenant_in_tree()
        load_tenant_settings_to_gui(tenant)

        # Disable save/reset buttons
        button_save.configure(state=DISABLED)
        button_reset.configure(state=DISABLED)

        # Activate fetch/file explorer buttons
        button_fetch.configure(state=NORMAL)
        button_open_file_explorer.configure(state=NORMAL)
        print("Changes reset")

    # Create popup window with tenant's fetch options
    @staticmethod
    def click_button_fetch_options():
        popup = FetchOptionsPopup(app)


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

        button_local_directory = ttk.Button(self, text="Browse", command=self.button_folder_browse, style="TButton")
        button_local_directory.grid(row=5, column=3, sticky="w", padx=10)

        # Event bindings for entry fields
        e_tenant_name.bind('<KeyPress>', self.callback_tenant_settings_changed)
        e_superoffice_url.bind('<KeyPress>', self.callback_tenant_settings_changed)
        e_include_id.bind('<KeyPress>', self.callback_tenant_settings_changed)
        e_key.bind('<KeyPress>', self.callback_tenant_settings_changed)
        button_local_directory.bind('<ButtonRelease>', self.callback_tenant_settings_changed)

        # Row 6 - Tenant save/reset settings buttons frame
        frame_tenant_buttons = TenantButtonsFrame(self)
        frame_tenant_buttons.grid(row=6, column=0, columnspan=2, sticky="w")

    @staticmethod
    def callback_tenant_settings_changed(event):
        """Turns save/reset buttons clickable and fetch/file explorer button non-clickable"""
        button_save.configure(state=NORMAL, style="Accent.TButton")
        button_reset.configure(state=NORMAL)

        # Disable fetch and file explorer buttons to make sure user don't try to fetch/open from unsaved changes
        button_fetch.configure(state=DISABLED)
        button_open_file_explorer.configure(state=DISABLED)

    @staticmethod
    def button_folder_browse():
        directory = filedialog.askdirectory()
        if directory:
            label_local_directory_path.config(text=directory)


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
                                  command=self.click_button_fetch)
        button_fetch.grid(column=0, row=0)

        global button_open_file_explorer
        button_open_file_explorer = ttk.Button(self,
                                               text="Open in File Explorer",
                                               style="TButton",
                                               command=self.click_button_open_file_explorer)
        button_open_file_explorer.grid(row=0, column=1, padx=5)

        button_copy_fetcher_script = ttk.Button(self,
                                                text="Copy Fetcher script to clipboard",
                                                style="TButton",
                                                command=self.click_button_copy_fetcher_script)

        spacer = ttk.Label(self, text="")
        spacer.grid(row=0, column=2, ipadx=50)

        button_copy_fetcher_script.grid(row=0, column=3)

    @staticmethod
    def click_button_fetch() -> None:
        tenant: dict = get_selected_tenant_in_tree()
        if not tenant_is_valid_for_fetch(tenant):
            return

        question: str = "You are about to fetch data from SuperOffice.\n\n" \
                        "Note: Any files or folders inside folders generated by CRMScript Fetcher " \
                        "that are not present in Superoffice will be deleted.\n\n" \
                        "Do you want to continue?"

        if messagebox.askquestion("Fetch CRMScripts", question) == "yes":
            fetch = Fetch(tenant)
            fetch_success: bool = fetch.fetch()

            if fetch.crmscript_version and fetch.crmscript_version < CURRENT_CRMSCRIPT_VERSION:
                messagebox.showinfo("CRMScript version",
                                    "The fetcher CRMScript in use is not of the latest version.\n"
                                    "Updating the script is recommended.")

            if fetch_success:
                messagebox.showinfo("Success", "Fetch successful!")
            else:
                messagebox.showerror("Error", "Could not fetch data from tenant.")

    @staticmethod
    def click_button_open_file_explorer():
        local_directory = get_selected_tenant_in_tree().get("local_directory").replace("/", "\\")
        subprocess.Popen(f'explorer "{local_directory}"')

    @staticmethod
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


class FetchOptionsPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Fetch Options")
        self.grab_set()  # Deactivates other windows
        self.focus_force()  # Sets focus to this window

        # Position popup window on top of main app window
        size_x: int = 250
        size_y: int = 235
        pos_x: int = app.winfo_x() + 250
        pos_y: int = app.winfo_y() + 80
        self.geometry(f"{size_x}x{size_y}+{pos_x}+{pos_y}")
        self.resizable(0, 0)

        self.tenant: dict = get_selected_tenant_in_tree()
        self.fetch_options: dict = self.tenant["fetch_options"]

        # Bound variables of each checkbutton
        # Load value of each fetch option in selected tenant
        self.fetch_scripts: BooleanVar = BooleanVar(self, self.fetch_options["fetch_scripts"])
        self.fetch_triggers: BooleanVar = BooleanVar(self, self.fetch_options["fetch_triggers"])
        self.fetch_screens: BooleanVar = BooleanVar(self, self.fetch_options["fetch_screens"])
        self.fetch_screen_choosers: BooleanVar = BooleanVar(self, self.fetch_options["fetch_screen_choosers"])
        self.fetch_scheduled_tasks: BooleanVar = BooleanVar(self, self.fetch_options["fetch_scheduled_tasks"])
        self.fetch_extra_tables: BooleanVar = BooleanVar(self, self.fetch_options["fetch_extra_tables"])

        self.create_widgets()

    def create_widgets(self):
        # Check button for each fetch option
        checkbutton_scripts = ttk.Checkbutton(self, text="Scripts", variable=self.fetch_scripts)
        checkbutton_scripts.grid(column=0, row=0, sticky="nw", padx=10, ipadx=5, ipady=5)

        checkbutton_triggers = ttk.Checkbutton(self, text="Triggers", variable=self.fetch_triggers)
        checkbutton_triggers.grid(column=0, row=1, sticky="nw", padx=10, ipadx=5, ipady=0)

        checkbutton_screens = ttk.Checkbutton(self, text="Screens", variable=self.fetch_screens)
        checkbutton_screens.grid(column=0, row=2, sticky="nw", padx=10, ipadx=5, ipady=0)

        checkbutton_screen_choosers = ttk.Checkbutton(self, text="ScreenChoosers", variable=self.fetch_screen_choosers)
        checkbutton_screen_choosers.grid(column=0, row=3, sticky="nw", padx=10, ipadx=5, ipady=0)

        checkbutton_scheduled_tasks = ttk.Checkbutton(self, text="Scheduled tasks", variable=self.fetch_scheduled_tasks)
        checkbutton_scheduled_tasks.grid(column=0, row=4, sticky="nw", padx=10, ipadx=5, ipady=0)

        checkbutton_extra_tables = ttk.Checkbutton(self, text="Tables", variable=self.fetch_extra_tables)
        checkbutton_extra_tables.grid(column=0, row=5, sticky="nw", padx=10, ipadx=5, ipady=0)

        # Save and cancel button
        button_fetch_options_save = ttk.Button(self,
                                               text="Save",
                                               command=self.click_button_save_fetch_options,
                                               style="TButton")
        button_fetch_options_save.grid(column=0, row=6, sticky="w", padx=10, pady=10, ipadx=5, ipady=0)

        button_fetch_options_cancel = ttk.Button(self,
                                                 text="Cancel",
                                                 command=lambda: self.destroy(),
                                                 style="TButton")
        # NOTE: Button padx is set by pixel
        button_fetch_options_cancel.grid(column=0, row=6, sticky="w", padx=85, pady=10, ipadx=5, ipady=0)

    def click_button_save_fetch_options(self):
        ts = TenantSettingsJson()
        ts.update_tenant_fetch_options(self.tenant["id"],
                                       construct_fetch_options(fetch_scripts=self.fetch_scripts.get(),
                                                               fetch_triggers=self.fetch_triggers.get(),
                                                               fetch_screens=self.fetch_screens.get(),
                                                               fetch_screen_choosers=self.fetch_screen_choosers.get(),
                                                               fetch_scheduled_tasks=self.fetch_scheduled_tasks.get(),
                                                               fetch_extra_tables=self.fetch_extra_tables.get()))
        self.destroy()


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
            selected_tenant: dict = get_selected_tenant_in_tree()
            load_tenant_settings_to_gui(selected_tenant)


if __name__ == "__main__":
    app = App()
    app.mainloop()
