from pathlib import Path
import subprocess

from .extension import ConanExtension

class CmakeExtension(ConanExtension):
    def __init__(self, local_conan_cache: bool, name: str, datastore_root_folder: Path) -> None:
        super().__init__(local_conan_cache, name, datastore_root_folder)

    def default_config(self):
        config = {
            "conan_reference": "cmake/3.22.0@",
            "run_cmd": "cmake",
        }
        return config

    def install(self, reference: str = None):
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
            self.load_env_file()

        cmd = [self.config["run_cmd"]] + cmdline_options
        print("Executing CMake command:", cmd)
        subprocess.run(cmd)
