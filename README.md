# Agency Termux

A lightweight terminal browser for the Markdown agents in [Agency Agents](https://github.com/msitarzewski/agency-agents), adapted for Android/Termux.

## Install and run

In Termux, run:

```bash
pkg update -y
pkg install -y git
git clone https://github.com/damirus-papirus/agency-termux.git
cd agency-termux
chmod +x start.sh
./start.sh
```

The launcher installs Python and Git if needed and downloads the upstream project into `agency-agents/`. The upstream repository is kept separate from this wrapper.

## Features

- Browse agent Markdown files by category.
- Search agent names and instruction contents.
- Read instructions in the terminal.
- Export selected instructions into `exported/`.
- Optional clipboard copy when Termux:API is installed.
- Update the upstream agent catalogue with Git.

## Notes

This is a browser/exporter for agent instructions, not an AI model or autonomous agent runtime. To execute an agent's workflow, use its Markdown instructions with a compatible AI tool.
