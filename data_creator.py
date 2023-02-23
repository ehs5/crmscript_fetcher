from utility import create_folder
from utility import delete_folder
from utility import move_folder

from data_creation.scripts import create_scripts_hierarchy
from data_creation.triggers import create_trigger_files
from data_creation.screens import create_screens_hierarchy
from data_creation.screen_choosers import create_screen_chooser_files
from data_creation.scheduled_tasks import create_scheduled_tasks_files
from data_creation.tables import create_table_hierarchy

from typing import Optional
from typing import Callable


class DataCreator:
    """
    Creates files/folders based on data retrieved from SuperOffice
    """
    def __init__(self, data: dict, crmscript_version: int, tenant: dict):
        self.data: dict = data
        self.crmscript_version: int = crmscript_version
        self.tenant: dict = tenant

        # Key = Version of fetcher script in SuperOffice. Informs create() which creator method to use.
        self.creator_methods: dict[int, callable] = {
            1: self.creator_v1,
            2: self.creator_v2
        }

    def create(self) -> bool:
        """
        Calls different creator method depending on what version fetcher script in SuperOffice is.
        Returns true if folders/files were created successfully.
        Will delete all files/folders before recreating them from the JSON again.
        A backup temp folder is created in case script fails during execution.
        """
        creator_method: Optional[Callable] = self.creator_methods.get(self.crmscript_version)

        if not creator_method:
            return False  # Script version not supported or invalid

        creator_method()
        return True

    def creator_v1(self) -> None:
        """Used for fetcher script version 1"""
        temp_directory: str = f"{self.tenant.get('local_directory')}/temp"
        scripts_directory: str = f"{self.tenant.get('local_directory')}/Scripts"
        triggers_directory: str = f"{self.tenant.get('local_directory')}/Triggers"

        print("Trying to delete temp folder in case it was not deleted on previous fetch")
        delete_folder(temp_directory)

        print("Creating temp folder and moving existing folders and scripts to folder")
        create_folder(temp_directory)
        move_folder(scripts_directory, temp_directory)
        move_folder(triggers_directory, temp_directory)

        print("Creating folders and files from JSON")
        create_folder(scripts_directory)
        create_folder(triggers_directory)

        # Create a dict containing script folders and scripts since this was not a part of script version 1
        group_scripts: dict = {"script_folders": self.data["script_folders"], "scripts": self.data["scripts"]}
        create_scripts_hierarchy(scripts_directory, group_scripts)
        create_trigger_files(triggers_directory, self.data["triggers"])

        print("Deleting temp folder")
        delete_folder(temp_directory)

    def creator_v2(self) -> None:
        """Used for fetcher script version 2"""
        temp_directory: str = f"{self.tenant['local_directory']}/temp"
        scripts_directory: str = f"{self.tenant['local_directory']}/Scripts"
        triggers_directory: str = f"{self.tenant['local_directory']}/Triggers"
        screens_directory: str = f"{self.tenant['local_directory']}/Screens"
        screen_choosers_directory: str = f"{self.tenant['local_directory']}/ScreenChoosers"
        scheduled_tasks_directory: str = f"{self.tenant['local_directory']}/Scheduled tasks"
        tables_directory: str = f"{self.tenant['local_directory']}/Tables"

        print("Trying to delete temp folder in case it was not deleted on previous fetch")
        delete_folder(temp_directory)

        print("Creating temp folder and moving existing folders and scripts to folder")
        create_folder(temp_directory)
        move_folder(scripts_directory, temp_directory)
        move_folder(triggers_directory, temp_directory)
        move_folder(screens_directory, temp_directory)
        move_folder(screen_choosers_directory, temp_directory)
        move_folder(scheduled_tasks_directory, temp_directory)
        move_folder(tables_directory, temp_directory)

        print("Creating folders and files from JSON")
        if self.tenant["fetch_options"]["fetch_scripts"]:
            create_folder(scripts_directory)
            create_scripts_hierarchy(scripts_directory, self.data["group_scripts"])

        if self.tenant["fetch_options"]["fetch_triggers"]:
            create_folder(triggers_directory)
            create_trigger_files(triggers_directory, self.data["group_triggers"]["triggers"])

        if self.tenant["fetch_options"]["fetch_screens"]:
            create_folder(screens_directory)
            create_screens_hierarchy(screens_directory, self.data["group_screens"])

        if self.tenant["fetch_options"]["fetch_screen_choosers"]:
            create_folder(screen_choosers_directory)
            create_screen_chooser_files(screen_choosers_directory,
                                        self.data["group_screen_choosers"]["screen_choosers"])

        if self.tenant["fetch_options"]["fetch_scheduled_tasks"]:
            create_folder(scheduled_tasks_directory)
            create_scheduled_tasks_files(scheduled_tasks_directory, self.data["group_scheduled_tasks"])

        if self.tenant["fetch_options"]["fetch_extra_tables"]:
            create_folder(tables_directory)
            create_table_hierarchy(tables_directory, self.data["group_extra_tables"])

        print("Deleting temp folder")
        delete_folder(temp_directory)
