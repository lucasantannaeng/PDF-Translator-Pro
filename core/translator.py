"""
Translation Engine Wrapper for PDF-Translator-Pro
Orchestrates PDFMathTranslate (pdf2zh), manages progress callbacks, thread pools, and output files.
"""

from __future__ import annotations
import os
import re
import sys
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from core.config import config, BASE_DIR
from core.glossary import glossary_manager
from core.pdf_analyzer import analyze_pdf

VENV_PYTHON = BASE_DIR / ".venv" / "Scripts" / "python.exe"
PDF2ZH_EXE = BASE_DIR / ".venv" / "Scripts" / "pdf2zh.exe"


class TranslationJob:
    def __init__(
        self,
        input_pdf: Path | str,
        provider: str = "openrouter",
        model_id: str = "deepseek/deepseek-chat",
        source_lang: str = "en",
        target_lang: str = "pt",
        pages: Optional[str] = None,
        concurrency: int = 4,
        output_format: str = "both",
        domain: str = "aviation",
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
    ):
        self.input_pdf = Path(input_pdf)
        self.provider = provider
        self.model_id = model_id
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.pages = pages
        self.concurrency = concurrency
        self.output_format = output_format
        self.domain = domain
        self.on_progress = on_progress
        self.on_log = on_log

        self.analysis = analyze_pdf(self.input_pdf)
        self.job_id = f"{self.input_pdf.stem}_{int(time.time())}"
        self.status = "idle"  # idle, running, completed, failed, stopped
        self.progress_pct = 0.0
        self.current_page = 0
        self.total_pages = self.analysis.total_pages
        self.mono_pdf: Optional[Path] = None
        self.dual_pdf: Optional[Path] = None
        self.error_message: Optional[str] = None
        self.log_file = config.logs_dir / f"{self.job_id}.log"
        self._process: Optional[subprocess.Popen] = None
        self._stop_requested = False

    def log(self, message: str) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception:
            pass

        if self.on_log:
            self.on_log(formatted)

    def _prepare_prompt_file(self) -> Path:
        """Combines base system prompt with domain glossary rules."""
        base_prompt_file = BASE_DIR / "config" / "prompts" / "system_pt_br.txt"
        base_text = ""
        if base_prompt_file.exists():
            with open(base_prompt_file, "r", encoding="utf-8") as f:
                base_text = f.read()

        glossary_text = glossary_manager.format_prompt_injection(self.domain)
        if glossary_text and "$text" in base_text:
            combined = base_text.replace("Texto de Origem:\n$text", f"{glossary_text}\n\nTexto de Origem:\n$text")
        elif glossary_text:
            combined = f"{base_text}\n\n{glossary_text}\n\n$text"
        else:
            combined = base_text

        temp_prompt_path = config.temp_dir / f"prompt_{self.job_id}.txt"
        with open(temp_prompt_path, "w", encoding="utf-8") as f:
            f.write(combined)

        return temp_prompt_path

    def _build_env(self) -> Dict[str, str]:
        config.load()
        env = os.environ.copy()
        p_config = config.get_provider(self.provider)

        if self.provider == "freellm":
            env["OPENAI_BASE_URL"] = p_config.base_url if p_config else "http://127.0.0.1:31415/v1"
            env["OPENAI_API_KEY"] = p_config.api_key or os.getenv("FREELLM_API_KEY", "")
            env["OPENAI_MODEL"] = self.model_id
        elif self.provider == "openrouter":
            env["OPENAI_BASE_URL"] = p_config.base_url if p_config else "https://openrouter.ai/api/v1"
            env["OPENAI_API_KEY"] = p_config.api_key or os.getenv("OPENROUTER_API_KEY", "")
            env["OPENAI_MODEL"] = self.model_id
        elif self.provider == "deepseek":
            env["DEEPSEEK_API_KEY"] = p_config.api_key or os.getenv("DEEPSEEK_API_KEY", "")
            env["OPENAI_BASE_URL"] = "https://api.deepseek.com/v1"
            env["OPENAI_API_KEY"] = env["DEEPSEEK_API_KEY"]
            env["OPENAI_MODEL"] = self.model_id
        elif self.provider == "gemini":
            env["GEMINI_API_KEY"] = p_config.api_key or os.getenv("GEMINI_API_KEY", "")
            env["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
            env["OPENAI_API_KEY"] = env["GEMINI_API_KEY"]
            env["OPENAI_MODEL"] = self.model_id
        elif self.provider == "groq":
            env["GROQ_API_KEY"] = p_config.api_key or os.getenv("GROQ_API_KEY", "")
            env["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"
            env["OPENAI_API_KEY"] = env["GROQ_API_KEY"]
            env["OPENAI_MODEL"] = self.model_id

        return env

    def run(self) -> bool:
        """Executes the translation pipeline synchronously."""
        self.status = "running"
        self.log(f"Starting translation for: {self.input_pdf.name}")
        self.log(f"Provider: {self.provider} | Model: {self.model_id} | Threads: {self.concurrency}")
        self.log(f"Total Pages: {self.total_pages} | Words: {self.analysis.total_words}")

        prompt_file = self._prepare_prompt_file()
        env = self._build_env()

        # Determine pdf2zh executable
        pdf2zh_cmd = [
            str(PDF2ZH_EXE),
            str(self.input_pdf.resolve()),
            "-li", self.source_lang,
            "-lo", self.target_lang,
            "-t", str(self.concurrency),
            "-o", str(config.output_dir.resolve()),
            "-s", f"openai:{self.model_id}",
            "--skip-subset-fonts",
            "--ignore-cache",
        ]

        if prompt_file.exists():
            pdf2zh_cmd.extend(["--prompt", str(prompt_file.resolve())])

        if self.pages:
            # If pages has hyphens like '1-2', pass it directly
            pdf2zh_cmd.extend(["-p", str(self.pages)])

        self.log(f"Command: {' '.join(pdf2zh_cmd)}")

        try:
            self._process = subprocess.Popen(
                pdf2zh_cmd,
                env=env,
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )

            # Pattern match page logs e.g., "Page 15/621" or "[15/621]" or tqdm progress
            page_pattern = re.compile(r"(?:Page|page|\[|\b)(\d+)\s*/\s*(\d+)")

            for line in self._process.stdout:
                line_str = line.strip()
                if not line_str:
                    continue
                self.log(line_str)

                # Parse progress
                match = page_pattern.search(line_str)
                if match:
                    curr, total = int(match.group(1)), int(match.group(2))
                    self.current_page = curr
                    self.total_pages = total
                    self.progress_pct = round((curr / total) * 100.0, 1)
                    if self.on_progress:
                        self.on_progress({
                            "current_page": curr,
                            "total_pages": total,
                            "progress_pct": self.progress_pct,
                            "status": "running"
                        })

            self._process.wait()
            returncode = self._process.returncode

            if returncode == 0:
                self.status = "completed"
                self.progress_pct = 100.0
                self.log("Translation completed successfully!")

                # Locate output files
                expected_mono = config.output_dir / f"{self.input_pdf.stem}.mono.pdf"
                expected_dual = config.output_dir / f"{self.input_pdf.stem}.dual.pdf"
                alt_mono = config.output_dir / f"{self.input_pdf.stem}-mono.pdf"
                alt_dual = config.output_dir / f"{self.input_pdf.stem}-dual.pdf"

                if expected_mono.exists():
                    self.mono_pdf = expected_mono
                elif alt_mono.exists():
                    self.mono_pdf = alt_mono

                if expected_dual.exists():
                    self.dual_pdf = expected_dual
                elif alt_dual.exists():
                    self.dual_pdf = alt_dual

                if self.on_progress:
                    self.on_progress({
                        "current_page": self.total_pages,
                        "total_pages": self.total_pages,
                        "progress_pct": 100.0,
                        "status": "completed",
                        "mono_pdf": str(self.mono_pdf) if self.mono_pdf else None,
                        "dual_pdf": str(self.dual_pdf) if self.dual_pdf else None
                    })
                return True
            else:
                self.status = "failed"
                self.error_message = f"Process exited with code {returncode}"
                self.log(f"Error: {self.error_message}")
                if self.on_progress:
                    self.on_progress({"status": "failed", "error": self.error_message})
                return False

        except Exception as e:
            self.status = "failed"
            self.error_message = str(e)
            self.log(f"Exception during execution: {str(e)}")
            if self.on_progress:
                self.on_progress({"status": "failed", "error": self.error_message})
            return False

    def stop(self) -> None:
        self._stop_requested = True
        if self._process and self._process.poll() is None:
            self.log("Terminating translation process upon user request...")
            self._process.terminate()
            self.status = "stopped"
