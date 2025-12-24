import nuke 
import json
import os



def read_yaml(path):
    """Read YAML config"""


def read_json(path):
    """
    Read JSON file safely
    """
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    """
    Write JSON data safely
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
