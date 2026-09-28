# nas-smb-cli

English | [简体中文](README.md)

A NAS SMB file management CLI built on [smbprotocol](https://github.com/jborean93/smbprotocol), designed for both terminal users and AI agents. No network drive mounting required — browse, transfer, and manage files on your NAS share directly from the command line.

## Features

- **11 subcommands**: `ls` / `tree` / `stat` / `download` / `upload` / `mkdir` / `delete` / `move` / `read` / `find` / `df`
- **Pure CLI, zero interaction**: all arguments supplied up front, plain-text output — ideal for scripts and AI agents
- **Clear errors**: missing configuration is reported at startup with the exact variable names and how to set them; deleting a directory requires an explicit `--recursive` flag
- **Zero hardcoded secrets**: all connection settings come from environment variables; no real credentials in code or docs

## Requirements

- Python 3.10+
- [smbprotocol](https://pypi.org/project/smbprotocol/) (installed automatically)

## Installation

PyPI release coming soon. Install from source for now:

```bash
git clone https://github.com/OstrichHermit/nas-smb-cli.git
cd nas-smb-cli
pip install .
```

This installs a `nas` command on your PATH.

## Configuration

Provide NAS connection details via 4 environment variables — all required:

| Environment variable | Meaning | Example (placeholder) |
|----------------------|---------|------------------------|
| `NAS_HOST` | NAS address (IP or hostname) | `192.168.1.100` |
| `NAS_USER` | SMB username | `user` |
| `NAS_PASSWORD` | SMB password | `pass` |
| `NAS_SHARE` | Share name | `share` |

Windows (persistent, applies to newly started processes):

```powershell
setx NAS_HOST "192.168.1.100"
setx NAS_USER "user"
setx NAS_PASSWORD "pass"
setx NAS_SHARE "share"
```

Linux / macOS:

```bash
export NAS_HOST="192.168.1.100"
export NAS_USER="user"
export NAS_PASSWORD="pass"
export NAS_SHARE="share"
```

If any variable is missing, every subcommand fails immediately (exit 1) and lists what is missing:

```text
error: missing NAS connection environment variables: NAS_HOST, NAS_SHARE
required: NAS_HOST NAS_USER NAS_PASSWORD NAS_SHARE
example: setx NAS_HOST "192.168.1.100"; ...
```

## Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `nas ls` | `[path]` | List a directory (dirs first, sorted by name); defaults to share root |
| `nas tree` | `[path]` `--depth N` | Directory tree, depth 3 by default |
| `nas stat` | `<path>` | File/directory info: type, size, created/modified/accessed times |
| `nas download` | `<remote> <local>` | Download a file; if `local` is a directory, the remote filename is kept |
| `nas upload` | `<local> <remote>` | Upload a file |
| `nas mkdir` | `<path>` | Create a directory (parents included) |
| `nas delete` | `<path>` `--recursive` | Delete a file; directories require `--recursive` (alias `--rmrf`) |
| `nas move` | `<src> <dst>` | Rename/move |
| `nas read` | `<path>` `--bytes N` | Read a text file (UTF-8); `--bytes N` reads only the first N bytes |
| `nas find` | `[path]` `--name <pattern>` | Recursive name search with fnmatch patterns (e.g. `*.jpg`), case-insensitive |
| `nas df` | — | NAS total/used/available capacity |

Examples:

```bash
nas ls                                # list share root
nas ls Downloads                      # list a subdirectory
nas tree Backup --depth 2             # directory tree
nas stat Downloads/example.bin        # file/directory info
nas download nas_path local_path      # download
nas upload local_path nas_path        # upload
nas mkdir path/to/dir                 # create directory (parents included)
nas delete path --recursive           # delete a directory tree
nas move old new                      # rename/move
nas read doc.txt --bytes 4096         # read a text file
nas find . --name "*.jpg"             # find by name
nas df                                # capacity
```

## Security Notes

- Prefer a **read-only or least-privilege account** for this CLI to protect important data
- Never put real credentials in code, scripts, or version control — always use environment variables
- `delete` requires an explicit `--recursive` for directories, but still use it with care

## License

[MIT](LICENSE)
