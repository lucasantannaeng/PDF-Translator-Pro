"""
PDF Analyzer Module for PDF-Translator-Pro
Extracts structural metadata, word counts, token estimates, and cost calculations.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF


class PDFAnalysis:
    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.file_name = self.file_path.name
        self.file_size_mb = round(self.file_path.stat().st_size / (1024 * 1024), 2)
        self.total_pages = 0
        self.total_words = 0
        self.total_chars = 0
        self.estimated_tokens = 0
        self.has_text_layer = True
        self.has_images = False
        self.toc: List[Dict[str, Any]] = []
        self.page_stats: List[Dict[str, Any]] = []
        self.is_valid = False
        self.error_message: Optional[str] = None
        self._analyze()

    def _analyze(self) -> None:
        try:
            doc = fitz.open(str(self.file_path))
            self.total_pages = len(doc)
            
            # TOC / Bookmarks
            raw_toc = doc.get_toc()
            self.toc = [{"level": item[0], "title": item[1], "page": item[2]} for item in raw_toc]

            words_count = 0
            chars_count = 0
            empty_pages = 0
            images_found = False

            for i, page in enumerate(doc):
                text = page.get_text()
                p_words = len(text.split())
                p_chars = len(text)
                images = page.get_images()

                if images:
                    images_found = True

                if p_words == 0 and not images:
                    empty_pages += 1

                words_count += p_words
                chars_count += p_chars

                self.page_stats.append({
                    "page_num": i + 1,
                    "words": p_words,
                    "chars": p_chars,
                    "images_count": len(images)
                })

            self.total_words = words_count
            self.total_chars = chars_count
            # Rule of thumb for English technical text: ~1.3 tokens per word
            self.estimated_tokens = int(words_count * 1.3)
            self.has_images = images_found
            self.has_text_layer = words_count > (self.total_pages * 5)
            self.is_valid = True
            doc.close()
        except Exception as e:
            self.is_valid = False
            self.error_message = str(e)

    def calculate_cost(self, input_cost_per_1k: float, output_cost_per_1k: float) -> Dict[str, float]:
        """Calculates estimated API cost based on token estimates."""
        input_tokens = self.estimated_tokens
        # Translation output in Portuguese typically has 1.1x token density
        output_tokens = int(self.estimated_tokens * 1.1)
        
        in_cost = (input_tokens / 1000.0) * input_cost_per_1k
        out_cost = (output_tokens / 1000.0) * output_cost_per_1k
        total_cost = in_cost + out_cost
        
        return {
            "input_cost_usd": round(in_cost, 4),
            "output_cost_usd": round(out_cost, 4),
            "total_cost_usd": round(total_cost, 4)
        }

    def summary(self) -> Dict[str, Any]:
        return {
            "file_name": self.file_name,
            "size_mb": self.file_size_mb,
            "total_pages": self.total_pages,
            "total_words": self.total_words,
            "estimated_tokens": self.estimated_tokens,
            "has_text_layer": self.has_text_layer,
            "has_images": self.has_images,
            "toc_items_count": len(self.toc)
        }


def analyze_pdf(file_path: Path | str) -> PDFAnalysis:
    return PDFAnalysis(Path(file_path))
