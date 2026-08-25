"""
Batch Translation Runner for PDF-Translator-Pro
Processes multiple PDF files in sequence, tracks overall status, and outputs reports.
"""

from __future__ import annotations
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from core.config import config, BASE_DIR
from core.translator import TranslationJob
from core.pdf_analyzer import analyze_pdf


class BatchRunner:
    def __init__(
        self,
        input_files: Optional[List[Path | str]] = None,
        provider: str = "openrouter",
        model_id: str = "deepseek/deepseek-chat",
        source_lang: str = "en",
        target_lang: str = "pt",
        pages: Optional[str] = None,
        concurrency: int = 4,
        domain: str = "aviation",
        on_job_start: Optional[Callable[[TranslationJob], None]] = None,
        on_job_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_job_complete: Optional[Callable[[TranslationJob], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
    ):
        self.input_files = [Path(f) for f in (input_files or self._discover_inputs())]
        self.provider = provider
        self.model_id = model_id
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.pages = pages
        self.concurrency = concurrency
        self.domain = domain
        self.on_job_start = on_job_start
        self.on_job_progress = on_job_progress
        self.on_job_complete = on_job_complete
        self.on_log = on_log

        self.jobs: List[TranslationJob] = []
        self.is_running = False
        self.current_job_index = 0
        self.results: List[Dict[str, Any]] = []

    def _discover_inputs(self) -> List[Path]:
        return sorted(list(config.input_dir.glob("*.pdf")))

    def run_all(self) -> List[Dict[str, Any]]:
        self.is_running = True
        self.results = []
        total_files = len(self.input_files)

        if total_files == 0:
            if self.on_log:
                self.on_log("Nenhum arquivo PDF encontrado para tradução em input_pdfs/.")
            self.is_running = False
            return []

        start_time = time.time()

        for idx, file_path in enumerate(self.input_files, 1):
            self.current_job_index = idx
            if self.on_log:
                self.on_log(f"\n=======================================================")
                self.on_log(f"Iniciando Arquivo [{idx}/{total_files}]: {file_path.name}")
                self.on_log(f"=======================================================\n")

            job = TranslationJob(
                input_pdf=file_path,
                provider=self.provider,
                model_id=self.model_id,
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                pages=self.pages,
                concurrency=self.concurrency,
                domain=self.domain,
                on_progress=self.on_job_progress,
                on_log=self.on_log,
            )
            self.jobs.append(job)

            if self.on_job_start:
                self.on_job_start(job)

            success = job.run()

            res = {
                "file_name": file_path.name,
                "pages": job.total_pages,
                "status": job.status,
                "mono_pdf": str(job.mono_pdf) if job.mono_pdf else None,
                "dual_pdf": str(job.dual_pdf) if job.dual_pdf else None,
                "error": job.error_message,
            }
            self.results.append(res)

            if self.on_job_complete:
                self.on_job_complete(job)

        total_elapsed = round(time.time() - start_time, 2)
        self.is_running = False
        self._generate_report(total_elapsed)
        return self.results

    def _generate_report(self, total_elapsed: float) -> Path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = config.output_dir / f"relatorio_traducao_{timestamp}.md"

        lines = [
            "# Relatório de Tradução - PDF-Translator-Pro",
            f"\n- **Data de Execução:** {time.strftime('%d/%m/%Y %H:%M:%S')}",
            f"- **Provedor:** `{self.provider}`",
            f"- **Modelo:** `{self.model_id}`",
            f"- **Tempo Total:** {total_elapsed} segundos",
            f"- **Arquivos Processados:** {len(self.results)}",
            "\n## Detalhamento por Arquivo\n",
            "| Arquivo | Páginas | Status | Mono PDF (Traduzido) | Dual PDF (Bilíngue) |",
            "| :--- | :---: | :---: | :--- | :--- |",
        ]

        for r in self.results:
            mono_link = f"`{Path(r['mono_pdf']).name}`" if r.get("mono_pdf") else "N/A"
            dual_link = f"`{Path(r['dual_pdf']).name}`" if r.get("dual_pdf") else "N/A"
            status_badge = "✅ Concluído" if r["status"] == "completed" else f"❌ Falha ({r.get('error')})"
            lines.append(f"| **{r['file_name']}** | {r['pages']} | {status_badge} | {mono_link} | {dual_link} |")

        report_content = "\n".join(lines)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        return report_file
