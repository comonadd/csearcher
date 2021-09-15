# codesearch

WIP: Command-line utility for searching code.

Currently supported languages: C/C++, JavaScript, Python.

Currently can search by:

- function name
- class name

TODO:

- Reference search
- TypeScript
- Generic symbol search

## Usage

You can use this tool without any configuration.

**Find all functions containing "print" in the current directory**

```bash
csr fun print
```

**Search by class name**

```bash
csr cls Manager
```

## Configuration

To set up a project, you need to create a configuration file `code-search.json`

```json
{
  // Exclude specified glob patterns
  "exclude": ["docs/", "**/*.test.py", "__pycache__"]
}
```
