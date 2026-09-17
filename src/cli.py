"""CLI chat interface — clean answers with optional source excerpts."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.assistant import Assistant


console = Console()

SUGGESTIONS = [
    "Summarize this candidate's experience.",
    "What are the strongest projects on this resume?",
    "Generate interview questions based on this resume.",
    "What skills does this resume highlight?",
]


def render_response(resp) -> None:
    console.print()
    console.print(Panel(resp.answer, title="Assistant", border_style="green"))
    if resp.sources:
        console.print("[dim]From the resume:[/dim]")
        for s in resp.sources[:3]:
            label = s.get("label") or s.get("source_id") or "Resume"
            section = s.get("section") or ""
            excerpt = (s.get("excerpt") or "")[:200]
            console.print(f"  • {label} — {section}\n    {excerpt}")


def interactive(assistant: Assistant) -> None:
    console.print(
        Markdown(
            "# Resume AI Assistant\n"
            "Ask about the resume, or generate interview questions.\n"
            "Type `quit` to exit.\n\n"
            "**Suggested:**\n" + "\n".join(f"- {s}" for s in SUGGESTIONS)
        )
    )
    while True:
        try:
            question = console.input("\n[bold]you>[/bold] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nbye")
            break
        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            console.print("bye")
            break
        with console.status("Thinking…"):
            resp = assistant.ask(question)
        render_response(resp)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Grounded resume assistant")
    parser.add_argument("-q", "--question", help="Ask a single question and exit")
    args = parser.parse_args(argv)

    try:
        assistant = Assistant()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Failed to start:[/red] {exc}")
        return 1

    if args.question:
        resp = assistant.ask(args.question)
        render_response(resp)
        return 0

    interactive(assistant)
    return 0


if __name__ == "__main__":
    sys.exit(main())
