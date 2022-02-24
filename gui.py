import subprocess
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

import main


# BUTTON ACTIONS
def button_folder_browse():
    directory = filedialog.askdirectory()
    if directory:
        label_local_directory_path.config(text=directory)
    else:
        pass


def tenant_is_valid_for_save(tenant_id, tenant_name, local_directory):
    ts = main.TenantSettingsJson()
    tenant_is_valid = True
    message = "Could not save tenant:\n"

    if tenant_name == "":
        message = message + "\n• Tenant name cannot be empty"
        tenant_is_valid = False

    if ts.local_directory_already_used_by_tenant(tenant_id, local_directory):
        message = message + "\n• The local directory is already used by another tenant."
        tenant_is_valid = False

    if tenant_is_valid:
        return True
    messagebox.showerror("Error", message)


def button_save():
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

        ts = main.TenantSettingsJson()
        ts.update_tenant_in_json(updated_tenant)

        # Reload tree in order to reflect any changes in tenant name. Then re-set focus to same tenant.
        tree_load_tenants()
        for child in tree.get_children():
            if tree.item(child)["values"][1] == tenant_id:
                tree.selection_set(child)
                break
        tenant_settings_buttons_normal_state()


def button_reset():
    tenant = get_selected_tenant_in_tree()
    load_tenant_settings_to_gui(tenant)

    # Disable save/reset buttons
    button_save.configure(state=DISABLED, background="#F0F0F0", foreground="black")
    button_reset.configure(state=DISABLED)

    # Activate fetch/file explorer buttons
    button_fetch.configure(state=NORMAL)
    button_open_file_explorer.configure(state=NORMAL)
    print("Changes reset")


def button_add_tenant():
    ts = main.TenantSettingsJson()
    new_tenant = ts.add_tenant_to_json()

    tree_load_tenants()
    tree_set_focus_to_last_child()
    load_tenant_settings_to_gui(new_tenant)
    tenant_settings_buttons_normal_state()
    print("Tenant added")


def button_delete_tenant():
    ts = main.TenantSettingsJson()
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


def button_fetch():
    tenant = get_selected_tenant_in_tree()
    if tenant_is_valid_for_fetch(tenant):
        if messagebox.askquestion("Fetch CRMScripts",
                                  "You are about to fetch CRMScripts from SuperOffice.\n\n"
                                  "Note: Any files or folders inside the Scripts and Triggers folders "
                                  "that are not present in Superoffice will be deleted.\n\n"
                                  "Do you want to continue?") == "yes":

            so_data = main.SuperOfficeData()
            if so_data.fetch(tenant):
                messagebox.showinfo("Success", "CRMScripts fetched successfully!")
            else:
                messagebox.showerror("Error", "Could not fetch from CRMScripts from tenant.")


def button_open_file_explorer():
    local_directory = get_selected_tenant_in_tree().get("local_directory").replace("/", "\\")
    subprocess.Popen(f'explorer "{local_directory}"')
    print(f"Opened folder in File Explorer: {local_directory}")


# OTHER FUNCTIONS
# Disables save/reset buttons and activates fetch/file explorer buttons
def tenant_settings_buttons_normal_state():
    button_save.configure(state=DISABLED, background="#F0F0F0", foreground="black")
    button_reset.configure(state=DISABLED)
    button_fetch.configure(state=NORMAL)
    button_open_file_explorer.configure(state=NORMAL)


def get_selected_tenant_in_tree():
    ts = main.TenantSettingsJson()
    values = tree.item(tree.selection()).get("values")
    if len(values) > 0:
        tenant_id = values[1]
        return ts.get_tenant_by_id(tenant_id)
    else:
        return None


def tenant_is_valid_for_fetch(tenant):
    tenant_is_valid = True
    message = "Can not fetch CRMScripts because tenant settings are invalid:\n"

    if tenant.get("include_id") == "":
        message = message + "\n• Script include ID cannot be empty"
        tenant_is_valid = False

    if tenant.get("key") == "":
        message = message + "\n• Script key cannot be empty"
        tenant_is_valid = False

    if tenant.get("url") == "":
        message = message + "\n• SuperOffice Service URL cannot be empty"
        tenant_is_valid = False

    if tenant.get("local_directory") == "":
        message = message + "\n• Local directory path cannot be empty"
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


# Callback when having changed settings of a tenant
def tenant_settings_changed(event):
    button_save.configure(state=NORMAL, background="#1FAA59", foreground="white")
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
    ts = main.TenantSettingsJson()
    for t in ts.tenant_settings:
        tree.insert("", "end", values=(t.get("tenant_name"), t.get("id")), tags="cb")


# DEFINITION OF GUI STARTS HERE
root = Tk()
root.title("CRMScript Fetcher")
root.minsize(width=900, height=400)
root.iconbitmap("icon.ico")

# FRAMES
# Frame: Main
frame_main = LabelFrame(root, text="CRMScript Fetcher")
frame_main.pack(side=LEFT, fill=BOTH)

# Frame: Left column - Tenants navbar
frame_list_box = LabelFrame(frame_main, padx=5, pady=5)
frame_list_box.pack(side=LEFT, anchor="n", fill=Y)

# Frame: Left column - Tenants navbar (top)
frame_tenants_navbar = LabelFrame(frame_list_box)
frame_tenants_navbar.pack(side=TOP, fill=Y)

# Frame: Left column - List box buttons (bottom)
frame_list_box_buttons = LabelFrame(frame_list_box)
frame_list_box_buttons.pack(side=BOTTOM, fill=Y, anchor="w")

# Frame: Right column - Main content
frame_content = LabelFrame(frame_main, padx=5, pady=5)
frame_content.pack(side=RIGHT, anchor="n", fill=BOTH)

# Frame: Right column - Tenant content (top)
frame_content_tenant_settings = LabelFrame(frame_content)
frame_content_tenant_settings.pack(side=TOP, anchor="n")

# Frame: Right column Tenant settings info
frame_content_tenant_settings_info = LabelFrame(frame_content_tenant_settings, text="Tenant settings")
frame_content_tenant_settings_info.pack(side=TOP)

# Frame: Right column Tenant settings buttons
frame_content_tenant_settings_buttons = LabelFrame(frame_content_tenant_settings)
frame_content_tenant_settings_buttons.pack(side=BOTTOM, anchor="sw")

# Frame: Right column Tenant content (bottom) - fetch button
frame_content_tenant_bottom = LabelFrame(frame_content)
frame_content_tenant_bottom.pack(side=BOTTOM, anchor="sw")

# LABELS, ENTRY FIELDS AND BUTTONS
# Tenant navbar Tree (top)
tree = ttk.Treeview(frame_tenants_navbar, selectmode="browse")
tree.pack(side=LEFT, fill=Y)
tree["columns"] = ("1", "2")
tree["show"] = "headings"
tree["displaycolumns"] = "1"
tree.column("1", width=150, anchor='w')
tree.column("2")
tree.heading("1", text="--Tenants--")
tree.heading("2", text="id")

# Scrollbar
tree_scrollbar = ttk.Scrollbar(frame_tenants_navbar, orient="vertical", command=tree.yview)
tree_scrollbar.pack(side=RIGHT, fill=Y)
tree.configure(yscrollcommand=tree_scrollbar.set)

# Tenant navbar buttons (bottom)
button_add_tenant = Button(frame_list_box_buttons, text="Add tenant", command=button_add_tenant)
button_add_tenant.pack(side=LEFT)

button_delete_tenant = Button(frame_list_box_buttons, text="Delete tenant", command=button_delete_tenant)
button_delete_tenant.pack(side=RIGHT)

# Tenant settings info grid
# Row 0 - Tenant name
label_tenant_name = Label(frame_content_tenant_settings_info, text="Tenant name")
label_tenant_name.grid(row=0, column=0, sticky="w")

e_tenant_name = Entry(frame_content_tenant_settings_info, width=50)
e_tenant_name.grid(row=0, column=1, sticky="w")

# Row 1 - SuperOffice Service URL
label_superoffice_url = Label(frame_content_tenant_settings_info, text="SuperOffice Service URL")
label_superoffice_url.grid(row=1, column=0, sticky="w")

e_superoffice_url = Entry(frame_content_tenant_settings_info, width=50)
e_superoffice_url.grid(row=1, column=1, sticky="w")

# Row 2 - Script Include ID
label_include_id = Label(frame_content_tenant_settings_info, text="Script include ID")
label_include_id.grid(row=2, column=0, sticky="w")

e_include_id = Entry(frame_content_tenant_settings_info, width=50)
e_include_id.grid(row=2, column=1, sticky="w")

# Row 3 - Script key
label_key = Label(frame_content_tenant_settings_info, text="Script key")
label_key.grid(row=3, column=0, sticky="w")

e_key = Entry(frame_content_tenant_settings_info, width=50)
e_key.grid(row=3, column=1, sticky="w")

# Row 4 - Local directory
label_local_directory = Label(frame_content_tenant_settings_info, text="Local directory")
label_local_directory.grid(row=4, column=0, sticky="w")

label_local_directory_path = Label(frame_content_tenant_settings_info)
label_local_directory_path.grid(row=4, column=1, sticky="w")

button_local_directory = Button(frame_content_tenant_settings_info, text="Browse", command=button_folder_browse)
button_local_directory.grid(row=4, column=3, sticky="w")

# Tenant save/reset settings buttons
button_save = Button(frame_content_tenant_settings_buttons, text="Save settings", command=button_save, state=DISABLED)
button_save.pack(side=LEFT)

button_reset = Button(frame_content_tenant_settings_buttons, text="Reset settings", command=button_reset,
                      state=DISABLED)
button_reset.pack(side=RIGHT)

# Tenant fetch / open explorer buttons
button_fetch = Button(frame_content_tenant_bottom, text="Fetch CRMScripts", command=button_fetch)
button_fetch.grid(row=0, column=0, sticky="w")
button_fetch.configure(background="#383CC1", foreground="white")

button_open_file_explorer = Button(frame_content_tenant_bottom, text="Open in File Explorer",
                                   command=button_open_file_explorer)
button_open_file_explorer.grid(row=0, column=1, padx=10)


# EVENT BINDINGS
# Event when selecting a tenant
tree.tag_bind("<1>", tree_click)
tree.bind("<ButtonRelease-1>", tree_click)

# Event when changing fields
e_tenant_name.bind('<KeyPress>', tenant_settings_changed)
e_superoffice_url.bind('<KeyPress>', tenant_settings_changed)
e_include_id.bind('<KeyPress>', tenant_settings_changed)
e_key.bind('<KeyPress>', tenant_settings_changed)
button_local_directory.bind('<ButtonRelease>', tenant_settings_changed)

# FIRST LOAD OF TENANT DATA UPON OPENING CRMSCRIPT FETCHER
# Load tenants to left side tree (navbar), set focus to first tenant and load its tenant settings
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

root.mainloop()
