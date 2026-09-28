"""Main CLI application using Typer."""
#src/writing_assistant/cli.py
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from .config import get_prompt, load_config
from .ollama_client import OllamaClient
from .utils import clean_response, read_input, write_output

app = typer.Typer(
    name="write",
    help="Local AI Writing Assistant — correct, improve, and rewrite text with Ollama.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()

TONE_CHOICES = [
    "formal",
    "casual",
    "professional",
    "concise",
    "expanded",
    "persuasive",
    "academic",
    "creative",
    "simple",
]

# Debug logging is opt-in and never allowed to crash the app.
# Enable it with:  WRITE_ASSISTANT_DEBUG=1
_DEBUG_ENABLED = os.getenv("WRITE_ASSISTANT_DEBUG", "") not in ("", "0", "false", "False")
_LOG_PATH = Path(tempfile.gettempdir()) / "local-writing-assistant" / "debug.log"


def _debug_log(message: str) -> None:
    """Best-effort debug logging. Never raises — logging must not break the CLI."""
    if not _DEBUG_ENABLED:
        return
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(message)
    except Exception:
        # Logging is diagnostic only — silently ignore any failure.
        pass


def _get_ollama_client(config: dict) -> OllamaClient:
    """Create Ollama client from config."""
    ollama_cfg = config["ollama"]
    return OllamaClient(
        host=ollama_cfg["host"],
        model=ollama_cfg["model"],
        temperature=ollama_cfg.get("temperature", 0.3),
        timeout=ollama_cfg.get("timeout", 60),
    )


def _check_model(client: OllamaClient) -> None:
    """Warn if model is not available."""
    if not client.check_model():
        console.print(
            f"[yellow]⚠ Warning: Model '{client.model}' not found in Ollama.[/yellow]\n"
            f"Run: [bold]ollama pull {client.model}[/bold]"
        )


def _run_mode(
    mode: str,
    text: Optional[str],
    tone: Optional[str],
    input_file: Optional[Path],
    from_clipboard: bool,
    from_stdin: bool,
    output_file: Optional[Path],
    to_clipboard: bool,
    no_stream: bool,
    no_stats: bool,
) -> None:
    """Shared logic for correct, improve, and rewrite commands."""
    _debug_log(f"\n=== {mode} started ===\n")

    try:
        config = load_config()
        client = _get_ollama_client(config)

        _debug_log("Config loaded, client created\n")

        _check_model(client)

        user_text = read_input(
            text=text,
            input_file=input_file,
            from_clipboard=from_clipboard,
            from_stdin=from_stdin,
        )

        _debug_log(f"Input read: {len(user_text)} chars\n")

        if not user_text.strip():
            console.print("[red]Error:[/red] No input text provided. Use --help for usage.")
            raise typer.Exit(1)

        system_prompt = get_prompt(config, mode, tone)
        max_tokens = config["ollama"].get("max_tokens", 2048)
        stream = not no_stream and config["output"].get("streaming", True)
        show_stats = not no_stats and config["output"].get("show_stats", True)

        mode_display = mode.capitalize()
        if tone:
            mode_display += f" ({tone})"

        console.print(Panel(
            f"[dim]Input:[/dim] {user_text[:200]}{'...' if len(user_text) > 200 else ''}",
            title=f"[bold blue]{mode_display}[/bold blue]",
            border_style="blue",
        ))

        full_response = ""

        try:
            if stream:
                with Live(console=console, refresh_per_second=15, vertical_overflow="visible") as live:
                    live.update(Spinner("dots", text="Thinking..."))
                    for chunk in client.generate(
                        system=system_prompt,
                        prompt=user_text,
                        stream=True,
                        max_tokens=max_tokens,
                    ):
                        if "[Stats:" in chunk:
                            if show_stats:
                                full_response += chunk
                            continue
                        full_response += chunk
                        live.update(Text(full_response))
            else:
                with console.status("[bold green]Thinking..."):
                    for chunk in client.generate(
                        system=system_prompt,
                        prompt=user_text,
                        stream=False,
                        max_tokens=max_tokens,
                    ):
                        if "[Stats:" in chunk:
                            if show_stats:
                                full_response += chunk
                            continue
                        full_response += chunk
        except Exception as e:
            console.print(f"[red]Error contacting Ollama:[/red] {e}")
            console.print(
                "[dim]Is Ollama running? Try: [/dim][bold]ollama serve[/bold]"
            )
            client.close()
            raise typer.Exit(1)

        cleaned = clean_response(full_response)

        _debug_log(f"Response received: {len(cleaned)} chars\n")

        # If the model returned nothing at all, say so loudly instead of
        # silently falling through — otherwise the Input panel above looks
        # like "the output", which is confusing.
        if not cleaned.strip():
            console.print(
                "[red]⚠ The model returned an empty response.[/red] "
                "Most likely Ollama isn't running, or the model in your "
                "config hasn't been pulled yet.\n"
                f"[dim]Try:[/dim] [bold]ollama pull {config['ollama']['model']}[/bold]"
                " [dim]then[/dim] [bold]ollama run " + config["ollama"]["model"] + " \"hello\"[/bold]"
            )
            client.close()
            raise typer.Exit(1)

        if not stream:
            display_text = cleaned
            if "[Stats:" in display_text:
                display_text = display_text.split("\n\n[Stats:")[0]
            console.print("[bold green]Result:[/bold green]")
            console.print(Markdown(display_text))
            if show_stats and "[Stats:" in full_response:
                stats_part = full_response[full_response.find("[Stats:"):]
                console.print(Text(stats_part, style="dim"))
        elif show_stats and "[Stats:" in full_response:
            stats_part = full_response[full_response.find("[Stats:"):]
            console.print(Text(stats_part, style="dim"))

        # Flag (without blocking) when the model made no changes — helpful
        # when a small quantized model just echoes short/simple input back.
        stripped_display = cleaned.split("\n\n[Stats:")[0].strip()
        if stripped_display.strip().lower() == user_text.strip().lower():
            console.print(
                "[yellow]Note:[/yellow] the result is identical to your input — "
                "the model may not have made any changes, or struggled to "
                "follow the instruction. This is more common with very small "
                "quantized models on short input."
            )

        if to_clipboard:
            write_output(cleaned, output_file=output_file, to_clipboard=True, show_stats=False)
            _debug_log("Clipboard output done\n")
        elif output_file:
            write_output(cleaned, output_file=output_file, to_clipboard=False, show_stats=False)

        client.close()

    except typer.Exit:
        raise
    except Exception as e:
        _debug_log(f"ERROR: {e}\n{traceback.format_exc()}")
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def correct(
    text: Optional[str] = typer.Argument(None, help="Text to correct."),
    input_file: Optional[Path] = typer.Option(None, "--input", "-i", help="Read text from file."),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Write result to file."),
    from_clipboard: bool = typer.Option(False, "--from-clipboard", "-c", help="Read from clipboard."),
    from_stdin: bool = typer.Option(False, "--stdin", "-s", help="Read from stdin."),
    to_clipboard: bool = typer.Option(False, "--to-clipboard", "-C", help="Copy result to clipboard."),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming output."),
    no_stats: bool = typer.Option(False, "--no-stats", help="Hide token stats."),
) -> None:
    """Correct grammar, spelling, and punctuation with minimal changes."""
    _run_mode(
        "correct", text, None, input_file, from_clipboard,
        from_stdin, output_file, to_clipboard, no_stream, no_stats,
    )


@app.command()
def improve(
    text: Optional[str] = typer.Argument(None, help="Text to improve."),
    input_file: Optional[Path] = typer.Option(None, "--input", "-i", help="Read text from file."),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Write result to file."),
    from_clipboard: bool = typer.Option(False, "--from-clipboard", "-c", help="Read from clipboard."),
    from_stdin: bool = typer.Option(False, "--stdin", "-s", help="Read from stdin."),
    to_clipboard: bool = typer.Option(False, "--to-clipboard", "-C", help="Copy result to clipboard."),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming output."),
    no_stats: bool = typer.Option(False, "--no-stats", help="Hide token stats."),
) -> None:
    """Suggest better phrasing and sentence structure."""
    _run_mode(
        "improve", text, None, input_file, from_clipboard,
        from_stdin, output_file, to_clipboard, no_stream, no_stats,
    )


@app.command()
def rewrite(
    text: Optional[str] = typer.Argument(None, help="Text to rewrite."),
    tone: str = typer.Option("professional", "--tone", "-t", help="Rewrite tone/style.",
                               case_sensitive=False, shell_complete=TONE_CHOICES),
    input_file: Optional[Path] = typer.Option(None, "--input", "-i", help="Read text from file."),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Write result to file."),
    from_clipboard: bool = typer.Option(False, "--from-clipboard", "-c", help="Read from clipboard."),
    from_stdin: bool = typer.Option(False, "--stdin", "-s", help="Read from stdin."),
    to_clipboard: bool = typer.Option(False, "--to-clipboard", "-C", help="Copy result to clipboard."),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming output."),
    no_stats: bool = typer.Option(False, "--no-stats", help="Hide token stats."),
) -> None:
    """Rewrite text in a different style or tone."""
    tone = tone.lower()
    if tone not in TONE_CHOICES:
        console.print(f"[red]Error:[/red] Unknown tone '{tone}'. Choose from: {', '.join(TONE_CHOICES)}")
        raise typer.Exit(1)

    _run_mode(
        "rewrite", text, tone, input_file, from_clipboard,
        from_stdin, output_file, to_clipboard, no_stream, no_stats,
    )


@app.command()
def config(
    edit: bool = typer.Option(False, "--edit", "-e", help="Open config in default editor."),
    show_path: bool = typer.Option(False, "--path", help="Show config file path."),
) -> None:
    """Show or edit configuration."""
    from .config import _find_config_file, _get_config_dir

    cfg_path = _find_config_file()
    config_dir = _get_config_dir()

    if show_path:
        if cfg_path:
            console.print(f"[green]Config file:[/green] {cfg_path}")
        else:
            console.print(
                f"[yellow]No config file found.[/yellow] Searched in:\n"
                f"  - {Path.cwd() / 'config.yaml'}\n"
                f"  - {config_dir / 'config.yaml'}"
            )
        return

    if edit:
        if cfg_path:
            # Open in default editor
            if sys.platform == "win32":
                subprocess.run(["notepad", str(cfg_path)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(cfg_path)])
            else:
                editor = os.environ.get("EDITOR", "nano")
                subprocess.run([editor, str(cfg_path)])
        else:
            console.print(
                f"[yellow]No config file found.[/yellow] Create one at:\n"
                f"  {config_dir / 'config.yaml'}"
            )
        return

    # Show current effective config
    cfg = load_config()
    console.print(Panel(
        (
            f"[bold]Ollama:[/bold]\n"
            f"  Host: {cfg['ollama']['host']}\n"
            f"  Model: {cfg['ollama']['model']}\n"
            f"  Temperature: {cfg['ollama']['temperature']}\n"
            f"  Max Tokens: {cfg['ollama']['max_tokens']}\n\n"
            f"[bold]Output:[/bold]\n"
            f"  Streaming: {cfg['output']['streaming']}\n"
            f"  Show Stats: {cfg['output']['show_stats']}\n"
            f"  Default Clipboard: {cfg['output']['copy_to_clipboard']}"
        ),
        title="[bold green] Configuration[/bold green]",
        border_style="green",
    ))


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Show version and exit.", is_eager=True
    ),
) -> None:
    """Local AI Writing Assistant — powered by Ollama."""
    if version:
        from . import __version__
        console.print(f"[bold]local-writing-assistant[/bold] v{__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()