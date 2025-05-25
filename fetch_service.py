import json
import requests
from requests import Response
from data_creator import DataCreator

CURRENT_CRMSCRIPT_VERSION = 2

class FetchService:
    """
    Coordinates the fetch operation at the service level.
    Handles tenant validation, fetch execution, and response formatting.
    """

    @staticmethod
    def build_script_url(tenant: dict) -> str:
        """Builds the URL we call SuperOffice with to fetch data."""
        script_url: str = (
            f"{tenant.get('url')}/scripts/customer.fcgi?action=safeParse"
            f"&includeId={tenant.get('include_id')}"
            f"&key={tenant.get('key')}"
        )

        # Append fetch options to URL
        for key, value in tenant["fetch_options"].items():
            script_url += f"&{key}={str(value)}"

        return script_url

    def get_superoffice_data(self, tenant: dict) -> tuple[dict | None, str]:
        """
        Fetches JSON data from SuperOffice.
        Returns tuple of (data, error_message).
        """
        script_url = self.build_script_url(tenant)
        print(f"Getting JSON data from SuperOffice using endpoint: {script_url}")

        try:
            # Do GET request to Superoffice
            response: Response = requests.get(script_url)
            response.raise_for_status()  # Raises exception for any bad HTTP status

        except requests.ConnectionError as e:
            error = f"Failed to connect to SuperOffice: {str(e)}"
            print(error)
            return None, error
        except requests.Timeout as e:
            error = f"Request to SuperOffice timed out: {str(e)}"
            print(error)
            return None, error
        except requests.HTTPError as e:
            error = f"HTTP error occurred: {str(e)}"
            print(error)
            return None, error
        except requests.RequestException as e:
            error = f"Failed to fetch data from SuperOffice: {str(e)}"
            print(error)
            return None, error

        # Parse JSON and return data as dictionary from method
        try:
            data: dict = json.loads(response.text)
            print("JSON fetched!")
            return data, ""
        except json.JSONDecodeError as e:
            error: str = f"Invalid JSON response from server: {str(e)}"
            print(error)
            return None, error

    @staticmethod
    def validate_tenant(tenant: dict) -> str:
        """
        Validates tenant configuration.
        Returns error message if invalid, empty string if valid.
        """
        errors = []

        if tenant.get("include_id") == "":
            errors.append("Script include ID cannot be empty")

        if tenant.get("key") == "":
            errors.append("Script key cannot be empty")

        if tenant.get("url") == "":
            errors.append("SuperOffice Service URL cannot be empty")

        if tenant.get("local_directory") == "":
            errors.append("Local directory path cannot be empty")

        if all(not option for option in tenant.get("fetch_options").values()):
            errors.append("You must check at least one fetch option")

        if errors:
            return "Can not fetch CRMScripts because tenant settings are invalid:\n" + \
                "\n".join(f"- {error}" for error in errors)

        return ""

    def fetch(self, tenant) -> dict:
        """
        Main entry point for fetching data from SuperOffice for a specific tenant.
        """

        # The result that is returned to frontend
        result: dict = {
            "success": False,
            "validation_error": False,
            "error": "",
            "info": ""
        }

        try:
            # Make sure tenant is valid before trying to fetch
            validation_error: str = self.validate_tenant(tenant)
            if validation_error:
                result["validation_error"] = True
                result["error"] = validation_error
                return result

            # Fetch data from SuperOffice
            data: dict | None
            error: str
            data, error = self.get_superoffice_data(tenant)

            if error:
                result["error"] = error
                return result

            if not data:
                raise Exception("No data returned from GET request")

            # Get script version
            # Version 1 had no script_version key in JSON, so we default to that if none is present
            script_version: int = data.get("script_version", 1)

            if CURRENT_CRMSCRIPT_VERSION > script_version:
                result["info"] = (f"Note! The fetcher CRMScript in use is not of the latest version. "
                                  f"Updating the script is recommended. Current script version is: {CURRENT_CRMSCRIPT_VERSION}")

            # Create files and folder based on the JSON returned
            try:
                data_creator = DataCreator(data, script_version, tenant)
                success: bool = data_creator.create()

                if not success:
                    raise Exception("Failed to create local data files. Might be due to invalid script version?")

            except Exception as e:
                result["error"] = f"Error creating local files: {str(e)}"
                return result

            # Fetch and data creation was successful
            result["success"] = True
            return result

        # Something went wrong somewhere, return error to frontend
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            return result
