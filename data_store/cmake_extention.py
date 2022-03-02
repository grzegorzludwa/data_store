import logging
from pathlib import Path
from typing import Union
import subprocess

from .extension import ConanExtension

class CmakeExtension(ConanExtension):
    def __init__(self, local_conan_cache: bool, name: str, datastore_root_folder: Path) -> None:
        super().__init__(local_conan_cache, name, datastore_root_folder)

    @property
    def default_config(self):
        config = {
            "package": "cmake/3.22.0@",
            "run_cmd": "cmake",
        }
        return config

    def install(self, package: Union[str, None] = None):
        if not package:
            package = self.config["package"]

        if not self.is_valid_pkg_reference(package):
            logging.error("Please provide valid conan package reference")
            return

        # TODO: Remove this quickfix
        if "@" not in package:
            package += "@"

        if not self.is_installed(package):
            if not self.check_in_remotes(package):
                logging.error(f"Your package: {package} could not be found in remotes.")
            else :
                subprocess.run(f"conan install {package} -g virtualenv -if {self.datastore.path}", shell=True) # TODO: Use conan api from xsteps here
                self.config["package"] = package
                self.config["uses_envs"] = True
                self.datastore.save_config(self.config)
        else:
            logging.warning(f"{package} already installed.")


    def execute(self, cmdline_options: list):
        package = self.config["package"]
        if not self.is_installed(package):
            logging.warning(f"{package} is not installed. Run \"install\" command first.")
            return

        if self.config["uses_envs"]:
            self.load_env_file()

        cmd = [self.config["run_cmd"]] + cmdline_options
        logging.debug(f"Executing command: {cmd}")
        subprocess.run(cmd)
