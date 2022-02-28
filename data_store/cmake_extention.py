from pathlib import Path
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

    def install(self, package: str = None):
        if not package:
            package = self.config["package"]

        if not self.is_installed(package):
            if not self.check_if_exists(package):
                print(f"ERROR! Your package: {package} could not be found in remotes.")
                return
            subprocess.run(f"conan install {package} -g virtualenv -if {self.datastore.path}", shell=True)
            self.config["package"] = package
            self.config["uses_envs"] = True
            self.config["run_cmd"] = "cmake"
            self.datastore.save_config(self.config)
        else:
            print("CMake already installed")


    def execute(self, cmdline_options: list):
        if not self.is_installed(self.config["package"]):
            print("CMake package is not installed. Run \"install\" command first.")
            return

        if self.config["uses_envs"]:
            self.load_env_file()

        cmd = [self.config["run_cmd"]] + cmdline_options
        print("Executing CMake command:", cmd)
        subprocess.run(cmd)
