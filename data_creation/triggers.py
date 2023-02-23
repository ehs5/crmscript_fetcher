from utility import create_file
from utility import create_json_file
from utility import safe_name


def create_trigger_files(triggers_directory: str, triggers: list[dict]) -> None:
    """Creates .crmscript files of Triggers in local directory"""
    for t in triggers:
        file_name_no_ext: str = t.get("description")
        if not file_name_no_ext:
            file_name_no_ext = f"Unnamed trigger (ID {t.get('unique_identifier')})"
        file_name_no_ext = safe_name(file_name_no_ext)

        # Create script body file
        create_file(triggers_directory, f'{file_name_no_ext}.crmscript', t.get("body"))

        # Create meta data file with script body omitted
        t.pop("body")
        create_json_file(triggers_directory, f'{file_name_no_ext}.json', t)
