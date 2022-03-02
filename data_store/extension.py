from abc import ABC, abstractmethod
from conans.client.conan_api import Conan
from conans.errors import RecipeNotFoundException
import logging
import os
from pathlib import Path
import re
from typing import List

from .data_store import DataStore

class ExtensionCore(ABC):
    def __init__(self, name: str, datastore_root_folder: Path = Path(".xsteps")) -> None:
        self._datastore = DataStore(name, datastore_root_folder)
        try:
            self._config = self._datastore.get_config()
        except FileNotFoundError:
            logging.warning(f"Could not find config file: {self.datastore.configfile}.")
            logging.warning("Creating default one...")
            self.datastore.save_config(self.default_config)
            self._config = self.default_config
            logging.info(f"Default config file created: {self.datastore.configfile}")

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
            logging.debug("CONAN_USER_HOME: %s", os.environ.get("CONAN_USER_HOME"))

        self.conan_app = Conan()
        self.conan_app.create_app()
        self._setup_conan()

    def _setup_conan(self):
        self._remote_names = ["conancenter"]
        # TODO: fill this method
        # possible additional steps when run in ZF environment
        # curl -O https://repo-manager.emea.zf-world.com:443/artifactory/conan-config-frd/1.0.0/conan-config-xsteps.zip
        # conan config install conan-config-xsteps.zip
        # conan user add -p password -r remotes

    def available_remote_packages(self, search_pattern: str, remotes: List[str]) -> list:
        available_packages = []
        for remote in remotes:
            remote_results = self.conan_app.search_recipes(search_pattern, remote_name=remote)["results"]
            for result in remote_results:
                available_packages += [item["recipe"]["id"] for item in result["items"]]

        return available_packages

    def check_in_remotes(self, package: str) -> bool:
        for available_package in self.available_remote_packages(package, self._remote_names):
            # available_package does not contains "@" sign at the end
            if package.startswith(available_package):
                return True

        return False

    @staticmethod
    def is_valid_pkg_reference(reference: str) -> bool:
        regex_pattern = r"^\w[a-zA-Z0-9_\+\.-]{1,50}\/(\w+)(\.\w+){0,2}"
        return bool(re.match(regex_pattern, reference))

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

    def _install(self, package: str, install_folder: Path, use_virtualenv_generator: bool = True):
        # TODO: implement it
        pass
