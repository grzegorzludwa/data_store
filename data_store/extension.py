from abc import ABC, abstractmethod
import os
from pathlib import Path

from .data_store import DataStore

class ExtensionCore(ABC):
    def __init__(self, name: str, datastore_root_folder: Path = Path(".xsteps")) -> None:
        self._datastore = DataStore(name, datastore_root_folder)
        try:
            self._config = self._datastore.get_config()
        except FileNotFoundError:
            print(f"Warning: Could not find config file: {self.datastore.configfile}.")
            print("Creating default one")
            self.datastore.save_config(self.default_config())
            self._config = self.default_config()

    @property
    def datastore(self) -> DataStore:
        return self._datastore

    @property
    def config(self) -> dict:
        return self._config

    @property
    def installed(self) -> bool:
        try:
            ret = self.config["installed"]
        except (KeyError, TypeError):
            ret = False

        return ret

    @installed.setter
    def installed(self, state: bool):
        self.config["installed"] = state
        self.datastore.save_config(self.config)

    @abstractmethod
    def default_config(self) -> dict:
        pass

    @abstractmethod
    def install(self):
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
