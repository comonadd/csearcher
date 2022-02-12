import fire
from codesearch.searcher import CodeSearch, print_search_results
from codesearch.daemon import CodeSearchClient, CodeSearchDaemon
from typing import Optional


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

    def ref(self, symname):
        self.init_searcher()
        if self.client is not None:
            self.client.exec("ref", symname)
        else:
            print_search_results(self.searcher.ref(symname))

    def daemon(self):
        print("Running daemon")
        d = CodeSearchDaemon(self.dir)
        d.run()


def main():
    fire.Fire(CodeSearchCLI)
