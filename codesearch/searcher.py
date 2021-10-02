import json
import os
import pathlib
import re
import socket
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from socket import SO_REUSEADDR, SOL_SOCKET
from typing import Any, Dict, List, Optional
from codesearch.config import (
    Config,
    determine_included_files,
    load_config,
    merge_configs,
)
from codesearch.entry import Entry
from codesearch.handlers import handler_for_file_type

COL_PINK = "\033[95m"
COL_OKBLUE = "\033[94m"
COL_OKGREEN = "\033[92m"
COL_WARNING = "\033[93m"
COL_FAIL = "\033[91m"
COL_ENDC = "\033[0m"


def cmd_colgen(col: str):
    def cmd_out(text):
        return f"{col}{text}{COL_ENDC}"

    return cmd_out


cmd_green = cmd_colgen(COL_OKGREEN)
cmd_yellow = cmd_colgen(COL_WARNING)


Entries = Dict[str, List[Entry]]


def print_search_results(entries: Entries):
    found_something = False
    for f, fentries in entries.items():
        nothing_in_file = len(fentries) == 0
        if nothing_in_file:
            continue
        print(cmd_green(f))
        for entry in fentries:
            found_something = True
            pt = f"\t{entry.kind} [{entry.line}:{entry.col}]: "
            if entry.match is None:
                start, end = 0, 0
            elif isinstance(entry.match, tuple):
                start, end = entry.match
            elif isinstance(entry.match, list):
                [start, end] = entry.match
            elif isinstance(entry.match, re.Match):
                start, end = entry.match.span()
            t = entry.name
            pt += t[:start]
            pt += cmd_yellow(t[start:end])
            pt += t[end:]
            print(pt)
    if not found_something:
        print("Nothing found")
        return


class InvalidDirectoryPath(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'Invalid directory path specified: "{self.path}"'


@dataclass
class CodeSearchIndex:
    by_file: Dict[pathlib.Path, Any] = field(default_factory=dict)


class CodeSearch:
    index: CodeSearchIndex

    def __init__(self, dir=".", source=None, use_index=False):
        if not os.path.exists(dir):
            raise InvalidDirectoryPath(dir)
        self.dir = dir
        sys.path.append(dir)
        self.config = load_config(dir)
        if self.config.source is not None:
            self.config.source = source
        self.files = determine_included_files(self.config, dir)
        self.use_index = use_index
        if use_index:
            self.index = CodeSearchIndex()
            self.build_index()

    def build_index(self):
        print("Building index")
        for f in self.files:
            handler = handler_for_file_type(f)
            if handler is not None:
                idx = handler.index_file(f)
                self.index.by_file[f] = idx
        print("Done")

    def for_all_files_execute_handler(
        self, handler_key: str, search_pattern: str
    ) -> Entries:
        pattern = re.compile(search_pattern)
        entries: Any = defaultdict(dict)
        for f in self.files:
            idx = self.index.by_file.get(f, None) if self.use_index else None
            handler = handler_for_file_type(f)
            if handler is not None:
                fun = handler.__dict__[handler_key].__func__
                fentries = list(fun(handler, self.config, f, pattern, index=idx))
                entries[str(f)] = fentries
        return entries

    def cls(self, classname):
        return self.for_all_files_execute_handler("cls", classname)

    def fun(self, funname):
        return self.for_all_files_execute_handler("fun", funname)


DAEMON_PORT = 32458
N = 2048
ENCODING = "utf-8"


class NetworkMessageType(IntEnum):
    ENTRIES_MSG = 0
    DAEMON_SEARCH = 1


@dataclass
class NetworkMessage:
    type: NetworkMessageType

    def _to_dict(self):
        return {"type": self.type}

    def pack(self):
        d = self._to_dict()
        j = json.dumps(d)
        return j.encode(ENCODING)

    @classmethod
    def from_bytes(cls, b):
        j = b.decode(ENCODING)
        d = json.loads(j)
        ttc = {
            NetworkMessageType.DAEMON_SEARCH: DaemonSearchReqMsg,
            NetworkMessageType.ENTRIES_MSG: EntriesMessage,
        }
        c = ttc[d["type"]]
        del d["type"]
        return c.from_dict(d)


@dataclass
class EntriesMessage(NetworkMessage):
    entries: Dict[str, Entry]

    def _to_dict(self):
        return {
            **NetworkMessage._to_dict(self),
            "entries": {
                k: list(map(lambda e: e.to_dict(), v))
                for [k, v] in self.entries.items()
            },
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            entries={
                k: [Entry.from_dict(e) for e in v] for [k, v] in d["entries"].items()
            }
        )

    def __init__(self, entries):
        NetworkMessage.__init__(self, NetworkMessageType.ENTRIES_MSG)
        self.entries = entries


@dataclass
class DaemonSearchReqMsg(NetworkMessage):
    handler_key: str
    params: List[Any]

    def _to_dict(self):
        return {
            **NetworkMessage._to_dict(self),
            "params": [p for p in self.params],
            "handler_key": self.handler_key,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def __init__(self, handler_key, params):
        NetworkMessage.__init__(self, NetworkMessageType.DAEMON_SEARCH)
        self.handler_key = handler_key
        self.params = params


class Socket:
    read_query: List[Any] = []
    write_query: List[Any] = []
    sock: Optional[socket.socket] = None

    def __init__(self, *args, **kwargs):
        self.sock = socket.socket(*args, **kwargs)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    @classmethod
    def from_socket(cls, socket: socket.socket):
        obj = cls.__new__(cls)
        obj.sock = socket
        return obj

    def accept(self):
        while True:
            (clientsocket, address) = self.sock.accept()
            yield Socket.from_socket(clientsocket)

    def read_msg(self):
        chunks = []
        bytes_recd = 0
        msg = None
        while True:
            chunk = self.sock.recv(N)
            if len(chunk) == 0:
                continue
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
            if len(chunk) != N:
                # last chunk
                break
        bb = b"".join(chunks)
        msg = NetworkMessage.from_bytes(bb)
        return msg

    def send_msg(self, msg):
        self.sock.sendall(msg.pack())

    def listen(self, *args, **kwargs):
        self.sock.listen(*args, **kwargs)

    def bind(self, *args, **kwargs):
        self.sock.bind(*args, **kwargs)

    def connect(self, *args, **kwargs):
        self.sock.connect(*args, **kwargs)

    def close(self, *args, **kwargs):
        self.sock.close(*args, **kwargs)


class CodeSearchDaemon:
    searcher: CodeSearch
    sock: Socket
    index: CodeSearchIndex

    def __init__(self, dir):
        self.sock = Socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((socket.gethostname(), DAEMON_PORT))
        self.searcher = CodeSearch(dir, use_index=True)

    def run(self):
        self.sock.listen(5)
        for clientsocket in self.sock.accept():
            msg = clientsocket.read_msg()
            handler_key = msg.handler_key
            params = msg.params
            entries = self.searcher.for_all_files_execute_handler(handler_key, *params)
            clientsocket.send_msg(EntriesMessage(entries=entries))


class FailedToConnectToDaemon(Exception):
    def __str__(self):
        return "Failed to connect. Is the daemon running?"


class CodeSearchClient:
    sock: Socket

    def __init__(self, dir, source):
        self.sock = Socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((socket.gethostname(), DAEMON_PORT))
        except ConnectionRefusedError:
            raise FailedToConnectToDaemon

    def exec(self, handler_key: str, *params):
        self.sock.send_msg(DaemonSearchReqMsg(handler_key, params))
        entries_msg = self.sock.read_msg()
        print_search_results(entries_msg.entries)


class CodeSearchCLI:
    client: Optional[CodeSearchClient] = None
    searcher: CodeSearch
    use_client: bool = False
    dir: str = "."

    def __init__(self, dir=".", source=False, client=False):
        self.dir = dir
        self.use_client = client
        self.show_source = source

    def init_searcher(self):
        if self.use_client:
            self.client = CodeSearchClient(self.dir, self.show_source)
        else:
            self.searcher = CodeSearch(self.dir, self.show_source)

    def cls(self, classname):
        self.init_searcher()
        if self.client is not None:
            self.client.exec("cls", classname)
        else:
            print_search_results(self.searcher.cls(classname))

    def fun(self, funname):
        self.init_searcher()
        if self.client is not None:
            self.client.exec("fun", funname)
        else:
            print_search_results(self.searcher.fun(funname))

    def daemon(self):
        print("Running daemon")
        d = CodeSearchDaemon(self.dir)
        d.run()
