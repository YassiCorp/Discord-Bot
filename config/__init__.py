from libs import logger
from enum import Enum
import yaml

path = "config/config.yaml"

log = logger.ConsoleLogger(log_name="config", log_color="pink")

class ConfigLoader:
    def __init__(self, path=path):
        self.path = path
        self.config = self.load_config()
        self.create_config_classes(self.config)

    def load_config(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
        except FileNotFoundError:
            log.error("Config file not found.")
            raise FileNotFoundError
        except yaml.YAMLError as e:
            log.error(f"Error parsing YAML: {e}")
            raise yaml.YAMLError
        return config

    def create_config_classes(self, config):
        for section, values in config.items():
            section_class = type(section, (object,), values)
            setattr(self, section, section_class)

config = ConfigLoader()