<p align="center">
  <img src="assets/logo.svg" alt="Scribe CLI logo" />
</p>

<p align="center">
  <strong>A lightweight, fully local command-line AI writing assistant</strong>
  <br>
  Powered by <a href="https://ollama.com">Ollama</a> and small open-source models.
  <br>
  Correct grammar, improve sentences, and rewrite text in any style — completely offline and private.
</p>

<p align="center">
  <a href="https://python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python">
  </a>
  <a href="https://ollama.com">
    <img src="https://img.shields.io/badge/ollama-required-red.svg" alt="Ollama">
  </a>
</p>

---

## ✨ Features

| Feature                  | Description                                                                              |
| ------------------------ | ---------------------------------------------------------------------------------------- |
| **Grammar & Spelling**   | Fix errors with minimal changes                                                          |
| **Sentence Improvement** | Get better phrasing suggestions                                                          |
| **Rewrite Modes**        | 8 tones: formal, casual, professional, concise, expanded, persuasive, academic, creative |
| **Flexible Input**       | Stdin, file, clipboard, or direct argument                                               |
| **Flexible Output**      | Stdout, clipboard, or file                                                               |
| **Streaming Responses**  | Real-time output with Rich-powered TUI                                                   |
| **Configurable**         | YAML config for models, prompts, and defaults                                            |
| **Hotkeys**              | AutoHotkey integration for instant clipboard workflows                                   |
| **No API Keys**          | Runs entirely on your machine via Ollama                                                 |
| **Debug Mode**           | Opt-in logging via environment variable                                                  |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **[Ollama](https://ollama.com)** installed and running
- A supported model pulled locally (e.g. `llama3.2:3b-instruct-q4_K_M`)

```bash
ollama pull llama3.2:3b-instruct-q4_K_M
ollama serve
```

### Installation

```bash
# Clone the repository
git clone https://github.com/harysri/Scribe-CLI.git
cd Scribe-CLI

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS/Linux

# Install in editable mode
pip install -e .
```

> **Tip:** You can also install via `pipx` for an isolated global install:
>
> ```bash
> pipx install .
> ```

### Verify Installation

```bash
write --help
wa --help
write config --path
```

---

## 🎯 Usage

The CLI exposes three main commands via the `write` entry point:

### Correct Grammar

```bash
write correct "I has an apple"

# From clipboard
write correct --from-clipboard --to-clipboard

# From file
write correct --input essay.txt --output essay_v2.txt
```

### Improve Text

```bash
write improve "The meeting was good"

# Pipe from another command
cat draft.md | write improve --tone concise
```

### Rewrite in Different Tones

```bash
write rewrite --tone professional "Hey, can you send me that file?"

write rewrite --tone academic --input paper.txt --output paper_formal.txt
```

### Interactive / Stdin

```bash
# Type text, then Ctrl+D (Unix) or Ctrl+Z (Windows)
write correct --stdin
```

---

## 📋 Commands Reference

| Command                | Description                            |
| ---------------------- | -------------------------------------- |
| `write correct [TEXT]` | Fix grammar, spelling, and punctuation |
| `write improve [TEXT]` | Suggest better phrasing and structure  |
| `write rewrite [TEXT]` | Rewrite in a chosen style              |
| `write config`         | Show current configuration             |
| `write config --path`  | Show config file location              |
| `write config --edit`  | Open config in default editor          |
| `write --version`      | Show version                           |

---

## 🎨 Rewrite Tones

| Tone           | Description                        |
| -------------- | ---------------------------------- |
| `formal`       | Business-appropriate, polite       |
| `casual`       | Friendly, conversational           |
| `professional` | Polished workplace communication   |
| `concise`      | Short and to the point             |
| `expanded`     | More detailed and elaborate        |
| `persuasive`   | Compelling and convincing          |
| `academic`     | Scholarly and objective            |
| `creative`     | Vivid and imaginative              |
| `simple`       | Easy to understand (plain English) |

---

## ⚙️ Configuration

Edit `config.yaml` in the project root or your platform-specific config directory:

- **Windows:** `%APPDATA%\local-writing-assistant\config.yaml`
- **macOS:** `~/Library/Application Support/local-writing-assistant/config.yaml`
- **Linux:** `~/.config/local-writing-assistant/config.yaml`

```yaml
ollama:
  host: "http://localhost:11434"
  model: "llama3.2:3b-instruct-q4_K_M"
```

> **Pro Tip:** choose any small model that supports instruction-following. For example, `llama3.2:3b-instruct-q4_K_M` or `mistral-7b-instruct-v0.1`.

## 🖥️ Windows Hotkeys (AutoHotkey)

An `writing-assistant-hotkeys.ahk` script is included. Install [AutoHotkey v2](https://www.autohotkey.com/), then run or compile the script.

| Hotkey             | Action                                            |
| ------------------ | ------------------------------------------------- |
| `Ctrl + Shift + G` | Correct grammar of selected text and paste result |
| `Ctrl + Shift + C` | Correct grammar and copy result (no paste)        |
| `Ctrl + Alt + R`   | Rewrite in professional style                     |
| `Ctrl + Alt + I`   | Improve selected text                             |
| `Ctrl + Alt + F`   | Rewrite in formal style                           |
| `Ctrl + Alt + S`   | Make text concise                                 |
| `Ctrl + Alt + A`   | Rewrite in academic style                         |

The script:

1. Copies selected text to clipboard
2. Calls the CLI tool
3. Pastes (or copies) the improved text back

### Configuring the Hotkey Script

The script requires configuration to match your local setup. Edit the **Configuration** section at the top of `writing-assistant-hotkeys.ahk`:

```autohotkey
; --- Configuration ---
global WaDir := "project-root"  ; <-- Change this to your project root
global WriteExe := WaDir . "\.venv\Scripts\write.exe"
```

| Variable   | Description                                 | Example                                 |
| ---------- | ------------------------------------------- | --------------------------------------- |
| `WaDir`    | Absolute path to the project root           | `C:\CLI-writer`                         |
| `WriteExe` | Path to the `write.exe` entry point in venv | `C:\CLI-writer\.venv\Scripts\write.exe` |

> **Important:** The script uses the `write.exe` entry point from the virtual environment. Ensure the path is correct.

#### Auto-start on Login

To run the hotkey script automatically on Windows startup:

1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `writing-assistant-hotkeys.ahk` in the Startup folder

### Core Script Logic

The following shows the key functions that power the hotkey workflow:

**Argument quoting for Windows command line:**

```autohotkey
QuoteArg(arg) {
    return '"' StrReplace(arg, '"', '\"') '"'
}
```

**Main workflow — copy, process, paste:**

```autohotkey
RunAndPaste(args*) {
    oldClip := A_Clipboard
    A_Clipboard := ""

    Send "^c"
    Sleep 300

    if (A_Clipboard = "") {
        ToolTip "No text selected!"
        Sleep 1500
        ToolTip
        A_Clipboard := oldClip
        return
    }

    ; Build command: write.exe [subcommand] [options] --from-clipboard --to-clipboard --no-stats
    cmd := QuoteArg(WriteExe)
    for a in args
        cmd .= " " . QuoteArg(a)
    cmd .= " --from-clipboard --to-clipboard --no-stats"

    try {
        RunWait(cmd, WaDir, "Hide")
    } catch Error as e {
        ToolTip "Error: " e.Message
        Sleep 2000
        ToolTip
        A_Clipboard := oldClip
        return
    }

    if (A_Clipboard = "") {
        ToolTip "No response from assistant."
        Sleep 2000
        ToolTip
        A_Clipboard := oldClip
        return
    }

    Send "^v"
    Sleep 100

    ; Restore original clipboard after 5 seconds
    SetTimer(() => A_Clipboard := oldClip, -5000)
}
```

**Hotkey definitions:**

```autohotkey
^+g:: RunAndPaste("correct")                    ; Ctrl+Shift+G
^+c:: RunAndPaste("correct")                    ; Ctrl+Shift+C (copy only)
^!i:: RunAndPaste("improve")                    ; Ctrl+Alt+I
^!r:: RunAndPaste("rewrite", "--tone", "professional")  ; Ctrl+Alt+R
^!f:: RunAndPaste("rewrite", "--tone", "formal")        ; Ctrl+Alt+F
^!s:: RunAndPaste("rewrite", "--tone", "concise")       ; Ctrl+Alt+S
^!a:: RunAndPaste("rewrite", "--tone", "academic")      ; Ctrl+Alt+A
```

**System tray menu:**

```autohotkey
A_TrayMenu.Delete()
A_TrayMenu.Add("&Correct Grammar", (*) => RunAndPaste("correct"))
A_TrayMenu.Add("&Improve Text", (*) => RunAndPaste("improve"))
A_TrayMenu.Add("Rewrite &Professional", (*) => RunAndPaste("rewrite", "--tone", "professional"))
A_TrayMenu.Add("Rewrite &Formal", (*) => RunAndPaste("rewrite", "--tone", "formal"))
A_TrayMenu.Add("Make &Concise", (*) => RunAndPaste("rewrite", "--tone", "concise"))
A_TrayMenu.Add()
A_TrayMenu.Add("E&xit", (*) => ExitApp())
```

---

## 📁 Project Structure

```
.
├── src/
│   └── writing_assistant/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py           # Typer CLI entry points
│       ├── config.py       # YAML config + environment overrides
│       ├── ollama_client.py # HTTP streaming client for Ollama
│       └── utils.py        # I/O, clipboard, response cleaning
├── config.yaml             # User configuration (optional)
├── pyproject.toml          # Build + dependency metadata
└── writing-assistant-hotkeys.ahk
```

---

## 🔧 Troubleshooting

**Connection refused**

- Ensure Ollama is running: `ollama serve`
- Verify the host in `config.yaml` matches your Ollama instance

**Model not found**

- Pull the model first: `ollama pull llama3.2:3b-instruct-q4_K_M`

**Clipboard not working on Linux**

- Install `xclip` or `xsel`: `sudo apt install xclip`

**Empty response from model**

- The model may have echoed your input back. Try a larger model or different prompt.
- Enable debug logging: `set WRITE_ASSISTANT_DEBUG=1`

---

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check src/

# Run tests
pytest
```

### Debug Mode

Enable diagnostic logging:

```bash
# Windows PowerShell
$env:WRITE_ASSISTANT_DEBUG = "1"

# Unix/macOS
export WRITE_ASSISTANT_DEBUG=1
```

## 🙏 Acknowledgments

- **[Ollama](https://ollama.com)** — Local LLM runtime
- **[Typer](https://typer.tiangolo.com/)** — CLI framework
- **[Rich](https://rich.readthedocs.io/)** — Terminal formatting
- **[Pyperclip](https://pyperclip.readthedocs.io/)** — Cross-platform clipboard
