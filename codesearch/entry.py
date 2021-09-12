from enum import Enum
from dataclasses import dataclass

class EntryKind(Enum):
    Function = 0
    Class = 1

    def __str__(self):
        return entry_kind_to_str[self]

entry_kind_to_str = { EntryKind.Function: "Fun", EntryKind.Class: "Cls" }

@dataclass
class Entry:
    line: int
    kind: EntryKind
    name: str
    col: int = 0

    def __str__(self):
        return f"\t{self.kind} [{self.line}:{self.col}]: {self.name}"

    def __hash__(self):
        return self.__str__().__hash__()
