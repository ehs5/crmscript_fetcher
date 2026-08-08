from utility import create_json_file
from utility import safe_name


def remove_schedule_keys(schedule: dict) -> dict:
    """
    Removes keys from a single dictionary that are either unnecessary or keys that would cause constant
    updates to Git.
    Fields are still kept in CRMScript fetcher file in case we want to change this at some point.
    """
    keys: list[str] = ["asap", "next_execution", "last_execution", "execution_time", "lock_expire", "lock_pid",
                       "lock_ttl", "error_message", "last_error", "retries", "retry_interval"]
    for key in keys:
        schedule.pop(key)
    return schedule


def create_scheduled_tasks_files(directory: str, group_scheduled_tasks: dict) -> None:
    """Creates JSON files of scheduled tasks in local directory"""
    scheduled_tasks: list[dict] = group_scheduled_tasks["scheduled_task"]
    schedules: list[dict] = [remove_schedule_keys(s) for s in group_scheduled_tasks["schedule"]]

    # Create a JSON of each "scheduled_task" entry also containing corresponding "schedule" entry
    for task in scheduled_tasks:
        # Insert schedule entry
        task["schedule"]: dict = [s for s in schedules if s.get("id") == task.get("schedule_id")][0]

        # Create JSON File
        schedule_name: str = task["schedule"]["name"]
        file_name: str = f"{safe_name(schedule_name)}.json"
        create_json_file(directory, file_name, task)
