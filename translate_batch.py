"""
Automated Batch Translation Runner for PDF-Translator-Pro
Processes all PDFs in input_pdfs/ with full progress reporting.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.config import config
from core.batch_runner import BatchRunner
from rich.console import Console

console = Console(force_terminal=True, legacy_windows=False)


def main():
    console.print("[bold cyan]==================================================[/bold cyan]")
    console.print("[bold cyan]  PDF-Translator-Pro - Execução em Lote          [/bold cyan]")
    console.print("[bold cyan]==================================================[/bold cyan]\n")

    provider = config.default_provider
    model = config.default_model
    concurrency = config.concurrency

    console.print(f"[white]Provedor:[/] [bold yellow]{provider}[/]")
    console.print(f"[white]Modelo:[/]   [bold yellow]{model}[/]")
    console.print(f"[white]Threads:[/]  [bold green]{concurrency}[/]\n")

    runner = BatchRunner(
        provider=provider,
        model_id=model,
        concurrency=concurrency,
        on_log=lambda msg: console.print(f"[dim]{msg}[/dim]"),
    )

    if not runner.input_files:
        console.print("[yellow]Nenhum arquivo PDF encontrado em input_pdfs/.[/yellow]")
        return

    console.print(f"[bold green]Encontrados {len(runner.input_files)} arquivos para traduzir.[/bold green]")
    results = runner.run_all()

    console.print("\n[bold green]Processamento em lote finalizado![/bold green]")
    for r in results:
        status_txt = "[green]OK[/green]" if r["status"] == "completed" else f"[red]ERRO ({r.get('error')})[/red]"
        console.print(f"- [bold white]{r['file_name']}[/]: {status_txt}")


if __name__ == "__main__":
    main()
