from dataclasses import asdict, dataclass
from enum import IntEnum
from typing import Optional, Tuple, Dict, List


class EntryKind(IntEnum):
    Function = 0
    Class = 1
    Call = 2

    def __str__(self):
        return entry_kind_to_str[self]


entry_kind_to_str = {
    EntryKind.Function: "Fun",
    EntryKind.Class: "Class",
    EntryKind.Call: "Call",
}


@dataclass
class Entry:
    line: int
    kind: EntryKind
    name: str
    col: int = 0
    match: Optional[Tuple[int, int]] = None
    source: Optional[str] = None

    def __str__(self):
        return f'<{self.kind} [{self.line}:{self.col}] "{self.name}">'

    def __hash__(self):
        return self.__str__().__hash__()

    def to_dict(self):
        return {
            "line": self.line,
            "kind": int(self.kind),
            "name": self.name,
            "col": self.col,
            "match": self.match,
        }

    @classmethod
    def from_dict(cls, d):
        res = cls(**d)
        res.kind = EntryKind(d["kind"])
        return res


# Mapping of absolute file path to the list of entries for that file
Entries = Dict[str, List[Entry]]
