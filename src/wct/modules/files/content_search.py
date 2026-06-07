from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from loguru import logger


@dataclass
class SearchResult:
    path: str
    line_number: int
    preview: str
    match_count: int


def _read_text_file(path: Path, encoding: str = "utf-8") -> str:
    try:
        return path.read_text(encoding=encoding, errors="ignore")
    except Exception:
        return ""


def _search_pdf(path: Path, query: str) -> list[SearchResult]:
    results: list[SearchResult] = []
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            total = 0
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if query.lower() in text.lower():
                    total += 1
                    if total == 1:
                        preview = text[:200].replace("\n", " ")
                        results.append(SearchResult(
                            path=str(path),
                            line_number=i + 1,
                            preview=preview,
                            match_count=1,
                        ))
                    else:
                        results[0].match_count += 1
        if results:
            results[0].match_count = total
    except Exception as exc:
        logger.debug("PDF search failed for {}: {}", path, exc)
    return results


def _search_docx(path: Path, query: str) -> list[SearchResult]:
    results: list[SearchResult] = []
    try:
        import docx
        doc = docx.Document(path)
        total = 0
        for i, para in enumerate(doc.paragraphs):
            if query.lower() in para.text.lower():
                total += 1
                if total == 1:
                    preview = para.text[:200]
                    results.append(SearchResult(
                        path=str(path),
                        line_number=i + 1,
                        preview=preview,
                        match_count=1,
                    ))
                else:
                    results[0].match_count += 1
        if results:
            results[0].match_count = total
    except Exception as exc:
        logger.debug("DOCX search failed for {}: {}", path, exc)
    return results


def _search_txt(path: Path, query: str) -> list[SearchResult]:
    results: list[SearchResult] = []
    try:
        text = _read_text_file(path)
        lines = text.splitlines()
        total = 0
        for i, line in enumerate(lines):
            if query.lower() in line.lower():
                total += 1
                if total <= 3:
                    results.append(SearchResult(
                        path=str(path),
                        line_number=i + 1,
                        preview=line[:200],
                        match_count=1,
                    ))
        if results:
            # Update first result with total count
            results[0].match_count = total
    except Exception as exc:
        logger.debug("TXT search failed for {}: {}", path, exc)
    return results


def _search_generic(path: Path, query: str) -> list[SearchResult]:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _search_pdf(path, query)
    if ext in (".docx", ".doc"):
        return _search_docx(path, query)
    if ext in (".txt", ".md", ".csv", ".json", ".xml", ".py", ".cpp", ".c", ".h", ".js", ".ts", ".html", ".css", ".log", ".ini", ".cfg"):
        return _search_txt(path, query)
    return []


def search_folder(folder: Path, query: str, *, recursive: bool = True, extensions: list[str] | None = None) -> list[SearchResult]:
    results: list[SearchResult] = []
    if not folder.exists():
        return results
    if extensions:
        targets = set(e.lower().lstrip(".") for e in extensions)
    else:
        targets = {"txt", "md", "csv", "json", "xml", "py", "cpp", "c", "h", "js", "ts", "html", "css", "log", "ini", "cfg", "pdf", "docx"}
    pattern = "**/*" if recursive else "*"
    for path in folder.glob(pattern):
        if not path.is_file():
            continue
        if path.suffix.lower().lstrip(".") not in targets:
            continue
        try:
            found = _search_generic(path, query)
            results.extend(found)
        except Exception as exc:
            logger.debug("Search failed for {}: {}", path, exc)
    return results
