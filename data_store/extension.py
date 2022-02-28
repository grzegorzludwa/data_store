from abc import ABC, abstractmethod
from conans.client.conan_api import Conan
from conans.errors import InvalidNameException, RecipeNotFoundException
import os
from pathlib import Path
from typing import List

from .data_store import DataStore

class ExtensionCore(ABC):
    def __init__(self, name: str, datastore_root_folder: Path = Path(".xsteps")) -> None:
        self._datastore = DataStore(name, datastore_root_folder)
        try:
            self._config = self._datastore.get_config()
        except FileNotFoundError:
            print(f"Warning: Could not find config file: {self.datastore.configfile}.")
            print("Creating default one...")
            self.datastore.save_config(self.default_config)
            self._config = self.default_config
            print(f"Default config file created: {self.datastore.configfile}")

    @property
    def datastore(self) -> DataStore:
        return self._datastore

    @property
    def config(self) -> dict:
        return self._config

    @property
    @abstractmethod
    def default_config(self) -> dict:
        pass

    @abstractmethod
    def is_installed(self, package: str) -> bool:
        pass

    @abstractmethod
    def install(self, package: str):
        pass

    @abstractmethod
    def execute(self, cmdline_options: list):
        pass


class ConanExtension(ExtensionCore):
    def __init__(self, conan_cache_in_datastore: bool, name: str, datastore_root_folder: Path = Path(".xsteps")) -> None:
        super().__init__(name, datastore_root_folder)
        self._conan_cache_in_datastore = conan_cache_in_datastore
        if self._conan_cache_in_datastore:
            os.environ["CONAN_USER_HOME"] = str(datastore_root_folder.resolve())
            print("CONAN_USER_HOME:", os.environ.get("CONAN_USER_HOME"))

        self.conan_app = Conan()
        self.conan_app.create_app()
        self._setup_conan()

    def _setup_conan(self):
        self._remote_names = ["conancenter"]
        # TODO: create this method
        # possible additional steps when run in ZF environment
        # curl -O https://repo-manager.emea.zf-world.com:443/artifactory/conan-config-frd/1.0.0/conan-config-xsteps.zip
        # conan config install conan-config-xsteps.zip
        # conan user add -p password -r remotes
        pass

    def available_remote_packages(self, search_pattern: str, remotes: List[str]) -> list:
        available_packages = []
        for remote in remotes:
            try:
                remote_results = self.conan_app.search_packages(search_pattern, remotes)["results"]
            except RecipeNotFoundException:
                print(f"Warning! Could not find any package matching pattern: {search_pattern} in remote: {remote}.")
            else:
                for result in remote_results:
                    available_packages += [item["recipe"]["id"] for item in result["items"]]

        return available_packages

    def check_if_exists(self, package: str) -> bool:
        return package in self.available_remote_packages(package, self._remote_names)

    def is_installed(self, package: str) -> bool:
        ret = False
        try:
            self.conan_app.search_packages(package)
        except RecipeNotFoundException:
            ret = False
        else:
            ret = True

        return ret

    def load_env_file(self):
        # we parse file line by line manually so there is no problem if we parse ps1 with bash
        with open(self.datastore.path / "environment.ps1.env", "r") as env_file:
            # load all variables to dict
            env_variables = {k: str(v) for k, v in (l.split('=') for l in env_file)}
            for env_var, path in env_variables.items():
                # if we need to prepend to actual variable or simply add one
                if ":$env:" in path:
                    path = path.split(":$env:")[0]
                    os.environ[env_var] = os.pathsep.join([os.path.join(path), os.environ['PATH']])
                else:
                    os.environ[env_var] = path
