"""
CLI Interface for PDF-Translator-Pro
Provides high-density, rich terminal management and batch translation execution.
"""

from __future__ import annotations
import sys
import os
import argparse
from pathlib import Path

# Force UTF-8 on Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from core.config import config, BASE_DIR
from core.pdf_analyzer import analyze_pdf
from core.llm_router import router
from core.translator import TranslationJob
from core.batch_runner import BatchRunner

console = Console(force_terminal=True, legacy_windows=False)


def show_banner():
    console.print(
        Panel.fit(
            "[bold cyan]PDF-Translator-Pro[/bold cyan] [dim]v1.0.0[/dim]\n"
            "[white]Enterprise AI-Powered PDF Layout-Preserving Translation Suite[/white]\n"
            "[dim]Engines: DeepSeek V3 | Gemini 3.7/2.5 Flash | OpenRouter | Claude 3.5[/dim]",
            border_style="cyan"
        )
    )


def cmd_list(args):
    show_banner()
    pdf_files = list(config.input_dir.glob("*.pdf"))
    if not pdf_files:
        console.print("[yellow]Nenhum arquivo PDF encontrado na pasta 'input_pdfs/'.[/yellow]")
        console.print(f"[dim]Coloque os PDFs em: {config.input_dir.resolve()}[/dim]")
        return

    table = Table(title="Arquivos na Fila de Entrada (input_pdfs/)", header_style="bold cyan")
    table.add_column("No.", style="dim", width=4)
    table.add_column("Nome do Arquivo", style="bold white")
    table.add_column("Tamanho", justify="right", style="green")
    table.add_column("Paginas", justify="right", style="yellow")
    table.add_column("Status Saida", style="magenta")

    for idx, pdf in enumerate(pdf_files, 1):
        analysis = analyze_pdf(pdf)
        mono_exists = (config.output_dir / f"{pdf.stem}.mono.pdf").exists() or (config.output_dir / f"{pdf.stem}-mono.pdf").exists()
        status_txt = "[bold green][PRONTO][/bold green]" if mono_exists else "[yellow][PENDENTE][/yellow]"
        table.add_row(
            str(idx),
            pdf.name,
            f"{analysis.file_size_mb} MB",
            str(analysis.total_pages),
            status_txt
        )

    console.print(table)


def cmd_analyze(args):
    show_banner()
    target = Path(args.file) if args.file else None
    if not target or not target.exists():
        pdf_files = list(config.input_dir.glob("*.pdf"))
        if not pdf_files:
            console.print("[red]Erro: Especifique um arquivo PDF valido ou coloque arquivos em 'input_pdfs/'.[/red]")
            return
        target = pdf_files[0]

    console.print(f"[bold green]Analisando:[/] {target.name} ({target.resolve()})")
    with console.status("[cyan]Extraindo metadados, camadas e contagem de palavras...[/cyan]"):
        analysis = analyze_pdf(target)

    if not analysis.is_valid:
        console.print(f"[red]Falha na analise do PDF: {analysis.error_message}[/red]")
        return

    table = Table(title=f"Diagnostico Estrutural: {analysis.file_name}", header_style="bold cyan")
    table.add_column("Metrica", style="bold white")
    table.add_column("Valor", style="yellow")

    table.add_row("Tamanho do Arquivo", f"{analysis.file_size_mb} MB")
    table.add_row("Total de Paginas", str(analysis.total_pages))
    table.add_row("Total de Palavras", f"{analysis.total_words:,}")
    table.add_row("Estimativa de Tokens", f"~{analysis.estimated_tokens:,} tokens")
    table.add_row("Camada de Texto Vetorial", "Sim (Pronto para traducao direta)" if analysis.has_text_layer else "Nao (Requer OCR)")
    table.add_row("Imagens/Diagramas", "Presentes" if analysis.has_images else "Apenas texto")
    table.add_row("Indice / Bookmarks (TOC)", f"{len(analysis.toc)} secoes identificadas")

    console.print(table)

    # Cost Estimation Table
    cost_table = Table(title="Estimativa de Custo por Modelo de IA", header_style="bold green")
    cost_table.add_column("Provedor / Modelo", style="bold white")
    cost_table.add_column("Custo Entrada/1k", style="dim", justify="right")
    cost_table.add_column("Custo Saida/1k", style="dim", justify="right")
    cost_table.add_column("Custo Total Estimado", style="bold green", justify="right")

    for model in router.get_available_models():
        costs = analysis.calculate_cost(model["cost_in"], model["cost_out"])
        cost_table.add_row(
            f"{model['name']} ({model['provider']})",
            f"${model['cost_in']:.6f}",
            f"${model['cost_out']:.6f}",
            f"${costs['total_cost_usd']:.4f} USD (~R$ {costs['total_cost_usd'] * 5.8:.2f})"
        )

    console.print(cost_table)


def cmd_models(args):
    show_banner()
    table = Table(title="Modelos e Provedores Configurados", header_style="bold cyan")
    table.add_column("Provedor", style="bold magenta")
    table.add_column("Nome do Modelo", style="bold white")
    table.add_column("Model ID", style="cyan")
    table.add_column("Status Chave API", style="yellow")

    for m in router.get_available_models():
        status_key = "[green]Configurada[/green]" if m["is_ready"] else f"[red]Ausente ({m['env_key']})[/red]"
        table.add_row(m["provider"], m["name"], m["model_id"], status_key)

    console.print(table)


def cmd_test_api(args):
    show_banner()
    provider = args.provider or config.default_provider
    model = args.model or config.default_model

    console.print(f"[cyan]Testando conectividade com Provedor: [bold]{provider}[/bold] | Modelo: [bold]{model}[/bold]...[/cyan]")
    success, message, elapsed = router.test_connection(provider, model)

    if success:
        console.print(Panel(f"[bold green][SUCESSO] CONEXAO ESTABELECIDA COM SUCESSO![/bold green]\n\n{message}", border_style="green"))
    else:
        console.print(Panel(f"[bold red][ERRO] FALHA NO TESTE DE API[/bold red]\n\n{message}", border_style="red"))


def cmd_translate(args):
    show_banner()
    file_path = Path(args.file)
    if not file_path.exists():
        file_path = config.input_dir / args.file
        if not file_path.exists():
            console.print(f"[red]Erro: Arquivo '{args.file}' nao encontrado.[/red]")
            return

    provider = args.provider or config.default_provider
    model = args.model or config.default_model
    concurrency = int(args.concurrency or config.concurrency)
    pages = args.pages or None

    console.print(Panel.fit(
        f"[bold white]Arquivo:[/] [cyan]{file_path.name}[/]\n"
        f"[bold white]Provedor:[/] [yellow]{provider}[/] | [bold white]Modelo:[/] [yellow]{model}[/]\n"
        f"[bold white]Paginas:[/] [magenta]{pages or 'Todas'}[/] | [bold white]Threads Concorrentes:[/] [green]{concurrency}[/]\n"
        f"[bold white]Diretorio Saida:[/] [dim]{config.output_dir.resolve()}[/dim]",
        title="Parametros de Execucao",
        border_style="cyan"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(f"[cyan]Traduzindo {file_path.name}...", total=100)

        def on_prog(data):
            pct = data.get("progress_pct", 0)
            curr = data.get("current_page", 0)
            tot = data.get("total_pages", 0)
            progress.update(task_id, completed=pct, description=f"[cyan]Traduzindo {file_path.name} (Pag {curr}/{tot})...")

        job = TranslationJob(
            input_pdf=file_path,
            provider=provider,
            model_id=model,
            pages=pages,
            concurrency=concurrency,
            on_progress=on_prog,
            on_log=lambda msg: console.print(f"[dim]{msg}[/dim]"),
        )

        success = job.run()

    if success:
        console.print(Panel(
            f"[bold green]TRADUCAO CONCLUIDA COM SUCESSO![/bold green]\n\n"
            f"[bold]Mono PDF (Apenas Traducao):[/bold] {job.mono_pdf or 'Gerado na pasta'}\n"
            f"[bold]Dual PDF (Bilingue Lado a Lado):[/bold] {job.dual_pdf or 'Gerado na pasta'}\n"
            f"[bold]Pasta de Saida:[/] {config.output_dir.resolve()}",
            border_style="green"
        ))
    else:
        console.print(Panel(f"[bold red]FALHA NA TRADUCAO[/bold red]\n\n{job.error_message}", border_style="red"))


def cmd_batch(args):
    show_banner()
    provider = args.provider or config.default_provider
    model = args.model or config.default_model
    concurrency = int(args.concurrency or config.concurrency)
    pages = args.pages or None

    runner = BatchRunner(
        provider=provider,
        model_id=model,
        concurrency=concurrency,
        pages=pages,
        on_log=lambda msg: console.print(f"[dim]{msg}[/dim]"),
    )

    console.print(f"[bold cyan]Iniciando Traducao em Lote de {len(runner.input_files)} arquivos...[/bold cyan]")
    results = runner.run_all()

    table = Table(title="Resumo Final da Traducao em Lote", header_style="bold green")
    table.add_column("Arquivo", style="bold white")
    table.add_column("Paginas", justify="right", style="yellow")
    table.add_column("Status", style="magenta")

    for r in results:
        status_badge = "[green]Concluido[/green]" if r["status"] == "completed" else "[red]Falha[/red]"
        table.add_row(r["file_name"], str(r["pages"]), status_badge)

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="PDF-Translator-Pro CLI Suite")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponiveis")

    # list
    subparsers.add_parser("list", help="Lista PDFs na fila de entrada (input_pdfs/)")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Diagnostico estrutural e estimativa de custos de um PDF")
    p_analyze.add_argument("file", nargs="?", help="Caminho ou nome do arquivo PDF")

    # models
    subparsers.add_parser("models", help="Lista modelos e provedores de IA disponiveis")

    # test-api
    p_test = subparsers.add_parser("test-api", help="Testa conectividade com a API de traducao")
    p_test.add_argument("--provider", "-p", help="Provedor (openrouter, deepseek, gemini, groq)")
    p_test.add_argument("--model", "-m", help="ID do modelo")

    # translate
    p_trans = subparsers.add_parser("translate", help="Traduz um unico arquivo PDF")
    p_trans.add_argument("file", help="Caminho ou nome do arquivo PDF")
    p_trans.add_argument("--provider", "-P", help="Provedor (openrouter, deepseek, gemini, groq)")
    p_trans.add_argument("--model", "-m", help="ID do modelo")
    p_trans.add_argument("--pages", "-p", help="Intervalo de paginas (ex: 1-10)")
    p_trans.add_argument("--concurrency", "-t", type=int, help="Numero de threads simultaneas")

    # batch
    p_batch = subparsers.add_parser("batch", help="Traduz todos os arquivos em input_pdfs/")
    p_batch.add_argument("--provider", "-P", help="Provedor")
    p_batch.add_argument("--model", "-m", help="ID do modelo")
    p_batch.add_argument("--pages", "-p", help="Intervalo de paginas")
    p_batch.add_argument("--concurrency", "-t", type=int, help="Numero de threads simultaneas")

    args = parser.parse_args()

    if not args.command:
        show_banner()
        parser.print_help()
        return

    commands = {
        "list": cmd_list,
        "analyze": cmd_analyze,
        "models": cmd_models,
        "test-api": cmd_test_api,
        "translate": cmd_translate,
        "batch": cmd_batch,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        cmd_fn(args)


if __name__ == "__main__":
    main()
