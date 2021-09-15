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
from functools import reduce


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

def gitignore_arr_to_glob(gitignore_arr: List[str], root_dir: pathlib.Path) -> List[str]:
    lines = gitignore_arr
    # remove comments and empty lines
    lines = filter(lambda line: not line.startswith("#") and not line == "", lines)
    lines = filter(lambda line: "/." not in line and "." not in line, lines)
    # rec
    lines = map(
                    lambda line: line if line.startswith("/") else "**/" + line,
                    lines)
    # add root dir
    lines = map(
                lambda line: f"{root_dir}{line}" if line.startswith("/") else f"{root_dir}/{line}",
                lines)
    def double(acc, line):
        acc.append(line)
        acc.append(line + "/**")
        return acc
    lines = reduce(double, lines, [])
    lines = map(lambda line: f"{{{line}}}", lines)
    # negate ignore statement
    lines = map(
            lambda line: line if line.startswith("!") else "!" + line,
            lines,
    )
    glob_pattern = list(lines)
    #print(glob_pattern)
    return glob_pattern

def gitignore_to_glob(gitignore_path: pathlib.Path, root_dir: pathlib.Path) -> List[str]:
    with open(gitignore_path, "r") as f:
        content = f.read()
    lines = content.split("\n")
    return gitignore_arr_to_glob(lines, root_dir)

def construct_default_config_for_dir(dirpath: pathlib.Path):
    exclude = [
        "__main__.py", "__init__.py", "setup.py", "__pycache__",
        "*.png", "*.jpg", "*.bin", "*.jar", "*.exe", "*.so", "*.dll",
        "*.ini", "*.xml", "*.html", "*.css", ".git", "Makefile", "*.json", "LICENSE", "*.md",
        "CHANGELOG", "bin", ".gitignore", ".github", "*.rst", ".coveragerc", ".pylintrc", "*.txt",
    ]
    default_config = Config(exclude=exclude)
    return default_config

def merge_configs(a: Config, b: Config) -> Config:
    return Config(exclude=set([*a.exclude, *b.exclude]))

def load_gitignore(gip: pathlib.Path, dirpath: pathlib.Path) -> Config:
    with open(gip, "r") as f:
        ignored = f.read().split("\n")
    ignored = filter(lambda line: not line.startswith("#") and not line == "", ignored)
    ignored = list(ignored)
    return Config(exclude=ignored)

def load_config(dirpath):
    p = pathlib.Path(dirpath, CONFNAME)
    cfg = construct_default_config_for_dir(dirpath)
    if os.path.exists(p):
        with open(p, "r") as f:
            conf_json = f.read()
            conf = Config.from_json(conf_json)
        cfg = merge_configs(cfg, conf)
    gip = pathlib.Path(dirpath, ".gitignore")
    if os.path.exists(gip):
        gitignore_cfg = load_gitignore(gip, dirpath)
        cfg = merge_configs(cfg, gitignore_cfg)
    return cfg

