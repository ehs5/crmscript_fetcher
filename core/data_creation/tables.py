from utility import create_folder
from utility import create_json_file
from utility import safe_name


def create_extra_tables_in_folder(directory: str, folder_id: int, group_extra_tables: dict) -> None:
    """Creates JSON files of extra tables + fields in local directory"""
    extra_tables: list[dict] = group_extra_tables["extra_tables"]
    extra_fields: list[dict] = group_extra_tables["extra_fields"]

    for extra_table in [et for et in extra_tables if et.get("hierarchy_id") == folder_id]:
        table: dict = {
            "extra_table": extra_table,
            "extra_fields": [f for f in extra_fields if f["extra_table"] == extra_table["id"]]
        }

        file_name: str = f"{extra_table['name']}.json"
        create_json_file(directory, safe_name(file_name), table)


def create_extra_tables_hierarchy(directory: str, group_extra_tables: dict, lookup_parent_id: int = -1) -> None:
    """Creates folders and files of extra tables with extra fields in local directory"""

    # Create tables in root folder
    if lookup_parent_id == -1:
        create_extra_tables_in_folder(directory, lookup_parent_id, group_extra_tables)

    # Recursively create folder structure with tables as JSON files
    created_folders: list[dict] = []
    for folder in [f for f in group_extra_tables["extra_table_folders"] if f["parent_id"] == lookup_parent_id]:
        if folder in created_folders:
            continue

        path: str = f"{directory}/{safe_name(folder.get('name'))}"
        create_folder(path)
        created_folders.append(folder)

        create_extra_tables_in_folder(path, folder["id"], group_extra_tables)
        create_extra_tables_hierarchy(path, group_extra_tables, folder["id"])  # Create child folders


def create_default_table_files(directory: str, extra_fields: list[dict]) -> None:
    """Creates JSON files of default tables' extra fields"""

    # Key = Domain ID as found in extra_field table. Value = Table name
    domains: dict[int, str] = {
        1: "Contact",
        2: "Company",
        4: "Request",
        8: "Message",
        32: "User",
        64: "Category",
        128: "FAQ entry",
        256: "FAQ category"
    }

    # For each default table (domain), create JSON file with extra fields
    for domain in domains.keys():
        table: dict = {
            "extra_fields": [field for field in extra_fields if field["domain"] == domain]
        }
        create_json_file(directory, f"{domains[domain]}.json", table)


def create_table_hierarchy(directory: str, group_extra_tables: dict) -> None:
    create_extra_tables_hierarchy(directory, group_extra_tables)
    create_default_table_files(directory, group_extra_tables["extra_fields"])
