import json
import socket
from dataclasses import dataclass
from enum import IntEnum
from socket import SO_REUSEADDR, SOL_SOCKET
from typing import Any, Dict, List, Optional
from codesearch.logger import configure_loggers, logger
from codesearch.entry import Entry
from codesearch.searcher import CodeSearch, CodeSearchIndex, print_search_results

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


class FailedToConnectToDaemon(Exception):
    def __str__(self):
        return "Failed to connect. Is the daemon running?"


class CodeSearchDaemon:
    searcher: CodeSearch
    sock: Socket
    index: CodeSearchIndex

    def __init__(self, dir):
        self.sock = Socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((socket.gethostname(), DAEMON_PORT))
        self.searcher = CodeSearch(dir, use_index=True)
        configure_loggers(daemon=True)

    def run(self):
        self.sock.listen(5)
        for clientsocket in self.sock.accept():
            msg = clientsocket.read_msg()
            handler_key = msg.handler_key
            params = msg.params
            entries = self.searcher.for_all_files_execute_handler(handler_key, *params)
            clientsocket.send_msg(EntriesMessage(entries=entries))


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
