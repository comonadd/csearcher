# codesearch

WIP: Utility for searching code in your project.

Currently supported languages: C++, C, Python.

Search by:

- function name
- class name

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
