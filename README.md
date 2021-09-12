# code-search

Utility for searching code in your project.

## Usage

To set up a project, you need to create a configuration file `code-search.json`

```json
{}
```

Find all functions containing "print"
`code-search --function *print*`

Find all symbols containing print
`code-search *print*`
