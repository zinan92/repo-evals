# Tinytool

A tiny command-line utility for smoke-testing markdown parsers.

![version](https://img.shields.io/badge/version-0.2.1-blue)

## Features

- Reads a markdown file and extracts headings
- Supports 3 output formats (text, json, yaml)
- Handles files up to 10 MB
- Fails clearly on unknown input

## Commands

| Command | Description |
|---------|-------------|
| `tinytool list` | List headings in the input file |
| `tinytool convert` | Convert between output formats |
| `tinytool validate` | Check the file for parse errors |

## Installation

```bash
pip install tinytool
```

See the [full docs](./does-not-exist.md) for advanced usage.

## License

MIT
