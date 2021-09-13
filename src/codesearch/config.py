import glob
import os
import sys
import re
import pathlib
import json
from pydoc import importfile
from dataclasses import dataclass, field
from typing import List, Set
from collections import defaultdict


CONFNAME = "code-searcher.json"

class InvalidConfig(Exception):
    def __str__(self):
        return "Invalid configuration file"

@dataclass
class Config:
    exclude: Set[str] = field(default_factory=set)
    source: bool = False

    @staticmethod
    def from_json(json_s: str):
        parsed = json.loads(json_s)
        if "exclude" in parsed:
            if type(parsed["exclude"]) != list:
                print(f"\"exclude\" must be a list, got {type(parsed['exclude'])}", file=sys.stderr)
                raise InvalidConfig
            parsed["exclude"] = set(parsed["exclude"])
        conf = Config(**parsed)
        return conf

default_config = Config(
    exclude=set([r"__main__.py", r"__init__.py", r"setup.py", r"__pycache__"]),
)

def merge_configs(a: Config, b: Config):
    return Config(exclude=set([*a.exclude, *b.exclude]))

def load_config(dirpath):
    p = pathlib.Path(dirpath, CONFNAME)
    print(p)
    if os.path.exists(p):
        with open(p, "r") as f:
            conf_json = f.read()
            conf = Config.from_json(conf_json)
        return merge_configs(default_config, conf)
    return default_config


