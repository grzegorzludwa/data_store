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

    def get_config(self) -> dict:
        return self._load(self._configfile)

    def save_config(self, config: dict):
        self._save(self._configfile, config)

    def append_config(self, to_append: dict, override: bool = False):
        current_data = self.get_config()
        output_data = {**current_data, **to_append}
        if not override:
            # check if number of keys changed == we overriden some keys
            len_before_merge = len(current_data.keys()) + len(to_append.keys())
            len_after_merge = len(output_data)
            if len_before_merge != len_after_merge:
                raise ValueError("You try to override some values in config, but override option disabled")

        self.save_config(output_data)

    def _load(self, configfile: Path) -> dict:
        data = {}
        try:
            data = yaml.load(configfile.read_text(), Loader=Loader)
        except FileNotFoundError as e:
            raise FileNotFoundError("Could not find config file: {configfile}.") from e
            # print(f"Warning! Could not find config file: {configfile}. Creating default one...")
            # self._save(self._configfile, data)

        return data

    def _save(self, configfile: Path, config: dict):
        with open(configfile, "w") as f:
            yaml.dump(config, f)
