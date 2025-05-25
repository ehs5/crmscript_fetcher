from data_creator import DataCreator

from typing import Optional
import json
import requests

CURRENT_CRMSCRIPT_VERSION: int = 2


class Fetch:
    """
    Responsible for getting JSON from SuperOffice, then calling DataCreator
    """
    def __init__(self, tenant: dict):
        self.data: Optional[dict] = None
        self.tenant: dict = tenant
        self.script_url: str = self.build_script_url()
        self.crmscript_version: Optional[int] = None

    def build_script_url(self) -> str:
        script_url: str = f"{self.tenant.get('url')}/scripts/customer.fcgi?action=safeParse" \
                          f"&includeId={self.tenant.get('include_id')}" \
                          f"&key={self.tenant.get('key')}"

        # Append fetch options to URL
        for key in self.tenant["fetch_options"]:
            value: str = str(self.tenant['fetch_options'][key])
            script_url += f"&{key}={value}"

        return script_url

    def get_json_from_superoffice(self) -> None:
        """Does a request to the SuperOffice CRMScript endpoint and saves the JSON response"""
        try:
            response = requests.get(self.script_url)
        except requests.HTTPError as e:
            print(f"Could not get data from SuperOffice: {e}")
        except requests.ReadTimeout as e:
            print(f"Could not get data from SuperOffice: {e}")
        except requests.Timeout as e:
            print(f"Could not get data from SuperOffice: {e}")
        except requests.TooManyRedirects as e:
            print(f"Could not get data from SuperOffice: {e}")
        except requests.ConnectionError as e:
            print(f"Could not get data from SuperOffice: {e}")
        except requests.RequestException as e:
            print(f"Could not get data from SuperOffice: {e}")
        else:
            try:
                data: dict = json.loads(response.text)
                print("JSON fetched!")
            except json.JSONDecodeError:
                print("Invalid JSON file")
            else:
                self.data = data

    def determine_script_version(self) -> int:
        """ Returns and sets version of fetcher CRMScript from returned JSON """
        self.crmscript_version: int = self.data.get("script_version")
        if not self.crmscript_version:
            self.crmscript_version = 1  # Version 1 had no script_version key in JSON

        return self.crmscript_version

    def fetch(self) -> dict:
        """
        Main fetch method that handles the complete fetch operation.
        Returns structured response with success status, errors and version info.
        """
        try:
            if validation_error := self.validate_tenant():
                return {
                    "success": False,
                    "validation_error": True,
                    "error": validation_error
                }

            self.get_json_from_superoffice()
            if not self.data:
                return {
                    "success": False,
                    "error": self.last_error or "Failed to fetch data"
                }

            self.determine_script_version()

            # Create data in local directory
            data_creator = DataCreator(self.data, self.crmscript_version, self.tenant)
            success = data_creator.create()

            return {
                "success": success,
                "error": self.last_error if not success else None,
                "crmscript_version": self.crmscript_version,
                "current_version": CURRENT_CRMSCRIPT_VERSION
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }