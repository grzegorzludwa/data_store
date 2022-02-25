#! /usr/bin/env python3

from pathlib import Path
import os
import subprocess
import yaml
from yaml.loader import Loader

class DataStore():
    def __init__(self, name: str, root_location: Path):
        self._name = name
        self._location = root_location
        self._datastore_path = root_location / name
        if not self._datastore_path.is_dir():
            self._datastore_path.mkdir(parents=True)
        self._datafile = self._datastore_path / "config.yaml"

    @property
    def path(self) -> Path:
        return self._datastore_path

    def get_config(self) -> dict:
        return self._load(self._datafile)

    def save_config(self, config: dict):
        self._save(self._datafile, config)

    def append_config(self, config: dict, override: bool = False):
        current_data = self.get_config()
        output_data = {**current_data, **config}
        if not override:
            # check if number of keys changed == we overriden some keys
            len_before_merge = len(current_data.keys()) + len(config.keys())
            len_after_merge = len(output_data)
            if len_before_merge != len_after_merge:
                raise ValueError("You try to override some values in config, but override option disabled")

        self.save_config(output_data)

    def _load(self, datafile: Path) -> dict:
        data = {}
        try:
            data = yaml.load(datafile.read_text(), Loader=Loader)
        except FileNotFoundError:
            print(f"Warning! Could not find config file: {datafile}. Creating empty one...")
            open(datafile, 'w').close()

        return data

    def _save(self, datafile: Path, config: dict):
        with open(datafile, "w") as f:
            yaml.dump(config, f)


# TODO: will be changed to abstract class later
class ExtensionCore():
    def __init__(self, datastore_name: str, home_folder: Path) -> None:
        self._configuration_folder = home_folder / "xsteps"
        self._datastore = DataStore(datastore_name, self._configuration_folder)
        self._config = self._datastore.get_config()

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
        except KeyError:
            ret = False

        return ret

    @installed.setter
    def installed(self, state: bool):
        self.config["installed"] = state
        self.datastore.save_config(self.config)

    def install(self):
        raise NotImplementedError

    def execute(self, cmdline_options: list):
        raise NotImplementedError


class ConanExtension(ExtensionCore):
    def __init__(self, custom_conan_home: bool, datastore_name: str, home_folder: Path) -> None:
        super().__init__(datastore_name, home_folder)
        self._custom_conan_home = custom_conan_home
        if self._custom_conan_home:
            os.environ["CONAN_USER_HOME"] = str(self._configuration_folder.resolve())
            print("CONAN_USER_HOME:", os.environ.get("CONAN_USER_HOME"))

    def load_env_file(self, override: bool = False):
        # we parse file line by line manually so there is no problem if we parse ps1 with bash
        with open(self.datastore.path / "environment.ps1.env", "r") as env_file:
            # load all variables to dict
            env_variables = {k:str(v) for k, v in (l.split('=') for l in env_file)}
            for env_var, path in env_variables.items():
                # if we need to prepend to actual variable or simply add one
                if ":$env:" in path:
                    path = path.split(":$env:")[0]
                    os.environ[env_var] = os.pathsep.join([os.path.join(path), os.environ['PATH']])
                else:
                    os.environ[env_var] = path


class CmakeExtension(ConanExtension):
    def __init__(self, custom_conan_home: bool, datastore_name: str, home_folder: Path) -> None:
        super().__init__(custom_conan_home, datastore_name, home_folder)

    def install(self):
        # possible additional steps when run in ZF environment
        # curl -O https://repo-manager.emea.zf-world.com:443/artifactory/conan-config-frd/1.0.0/conan-config-xsteps.zip
        # conan config install conan-config-xsteps.zip
        # conan user add -p password -r remotes

        if not self.installed:
            subprocess.run(f"conan install cmake/3.22.0@ -g virtualenv -if {self.datastore.path}", shell=True)
            self.installed = True
            self.config["uses_envs"] = True
            self.config["run_cmd"] = "cmake" # should be also moved as ExternsionCore property (same as installed)
            self.datastore.save_config(self.config)
        else:
            print("CMake already installed")


    def execute(self, cmdline_options: list):
        if not self.installed:
            print("CMake package is not installed")
            return

        if self.config["uses_envs"]:
            self.load_env_file(override=True)

        cmd = [self.config["run_cmd"]] + cmdline_options
        print("Executing CMake command:", cmd)
        subprocess.run(cmd)


def main():
    cmake = CmakeExtension(True, "cmake", Path())
    cmake.install()
    cmake.execute(["--version"])

if __name__ == "__main__":
    main()

