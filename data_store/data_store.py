from pathlib import Path
import yaml
from yaml.loader import Loader


class DataStore():
    def __init__(self, name: str, root_location: Path = Path(".xsteps")):
        self._name = name
        self._location = root_location
        self._datastore_path = root_location / name
        if not self._datastore_path.is_dir():
            self._datastore_path.mkdir(parents=True)
        self._configfile = self._datastore_path / "config.yaml"

    @property
    def path(self) -> Path:
        return self._datastore_path

    @property
    def configfile(self) -> Path:
        return self._configfile

    @configfile.setter
    def configfile(self, configfile: Path):
        self._configfile = configfile

    def get_config(self) -> dict:
        return self.load(self._configfile)

    def save_config(self, config: dict):
        self.save(self._configfile, config)

    def load(self, configfile: Path) -> dict:
        data = {}
        try:
            data = yaml.load(configfile.read_text(), Loader=Loader)
        except FileNotFoundError as e:
            raise FileNotFoundError("Could not find config file: {configfile}.") from e

        return data

    def save(self, configfile: Path, config: dict):
        with open(configfile, "w") as f:
            yaml.dump(config, f)
