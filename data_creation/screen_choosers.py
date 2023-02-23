from utility import create_file
from utility import create_json_file
from utility import safe_name


def create_screen_chooser_files(screen_choosers_directory: str, screen_choosers: list[dict]) -> None:
    """
    For each ScreenChooser, creates two files:
    1. A .crmscript file with the ScreenChooser Script body
    2. A .json file with ScreenChooser metadata
    """
    for sc in screen_choosers:
        file_name_no_ext: str = sc.get("description")
        if not file_name_no_ext:
            file_name_no_ext = f"Unnamed ScreenChooser (ID {sc.get('unique_identifier')})"
        file_name_no_ext = safe_name(file_name_no_ext)

        # Create script body file
        create_file(screen_choosers_directory, f'{file_name_no_ext}.crmscript', sc.get("body"))

        # Create meta data file with script body omitted
        sc.pop("body")
        create_json_file(screen_choosers_directory, f'{file_name_no_ext}.json', sc)
