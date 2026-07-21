"""
Standalone crawler untuk halaman komunitas Alodokter.

Fokus crawler:
- kunjungi halaman listing kategori penyakit;
- ambil daftar link diskusi pada tiap halaman listing;
- kunjungi halaman detail diskusi yang ditemukan;
- ekstrak tanggal, pertanyaan, jawaban, nama dokter, role dokter, dan metadata;
- simpan hasil ke file JSON.

Crawler ini sengaja hanya memakai standard library Python.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import random
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


# =========================
# KONSTANTA KONFIGURASI
# =========================

SCRIPT_DIR = Path(__file__).resolve().parent
URL = "https://www.alodokter.com/komunitas/diskusi/penyakit"
START_PAGE = 4500
JUMLAH_HALAMAN = 10
RANDOM_HALAMAN = True
RANDOM_PAGE_SPAN = 200
RANDOM_SEED: int | None = 42

OUTPUT_JSON = str(SCRIPT_DIR / "hasil_crawl_alodokter.json")
OUTPUT_DATASET_JSON = str(SCRIPT_DIR / "hasil_crawl_alodokter_dataset.json")
OUTPUT_QA_JSON = str(SCRIPT_DIR / "hasil_crawl_alodokter_qa_pairs.json")
TIMEOUT_SECONDS = 30
MIN_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 5.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36; research-crawler"
)

# Gunakan "path" untuk /page/2 sesuai contoh user.
# Gunakan "query" untuk ?paged=2 jika diperlukan.
PAGINATION_STYLE = "path"

# Batasi jumlah link detail per listing. Umumnya listing berisi sekitar 15 diskusi.
MAX_DETAIL_PER_LISTING: int | None = 15


INDONESIAN_MONTHS = {
    "januari": "01",
    "februari": "02",
    "maret": "03",
    "april": "04",
    "mei": "05",
    "juni": "06",
    "juli": "07",
    "agustus": "08",
    "september": "09",
    "oktober": "10",
    "november": "11",
    "desember": "12",
}


@dataclass
class LinkItem:
    url: str
    text: str


@dataclass
class CrawlError:
    url: str
    context: str
    error: str


@dataclass
class ConsultationRecord:
    source: str
    source_type: str
    url: str
    listing_url: str
    page_number: int
    title: str | None = None
    category: str = "penyakit"
    question: dict = field(default_factory=dict)
    answer: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class LinkExtractor(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[LinkItem] = []
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if not href:
            return

        if tag_name == "a":
            self._current_href = urljoin(self.base_url, href)
            self._current_text = []
            return

        # Alodokter listing uses custom elements such as:
        # <card-topic title="..." href="/komunitas/topic/...">
        title = attrs_dict.get("title") or attrs_dict.get("value") or attrs_dict.get("aria-label") or ""
        self.links.append(LinkItem(url=urljoin(self.base_url, href), text=clean_inline_text(title)))

    def handle_data(self, data: str) -> None:
        if self._current_href:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._current_href:
            text = clean_inline_text(" ".join(self._current_text))
            self.links.append(LinkItem(url=self._current_href, text=text))
            self._current_href = None
            self._current_text = []


class TextExtractor(HTMLParser):
    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title: str | None = None
        self.meta_description: str | None = None
        self._skip_depth = 0
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {key.lower(): value for key, value in attrs if key}
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
            self._title_parts = []
        if tag == "meta":
            name = (attrs_dict.get("name") or attrs_dict.get("property") or "").lower()
            if name in {"description", "og:description"} and attrs_dict.get("content"):
                self.meta_description = clean_inline_text(attrs_dict["content"] or "")
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False
            self.title = clean_inline_text(" ".join(self._title_parts))
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self._title_parts.append(data)
        self.parts.append(data)

    def get_text(self) -> str:
        text = html.unescape(" ".join(self.parts))
        lines = [clean_inline_text(line) for line in re.split(r"[\r\n]+", text)]
        lines = [line for line in lines if line]
        return "\n".join(lines)


class DetailAttributeExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.member: dict[str, str] = {}
        self.doctor: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag.lower() == "detail-topic":
            self.member = attrs_dict
        elif tag.lower() == "doctor-topic" and not self.doctor:
            self.doctor = attrs_dict


def clean_inline_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def decode_component_attr(value: str | None) -> str:
    if not value:
        return ""
    current = html.unescape(value)
    for _ in range(3):
        stripped = current.strip()
        if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
            try:
                current = json.loads(stripped)
                continue
            except json.JSONDecodeError:
                current = stripped[1:-1]
                continue
        break
    current = current.replace("\\u003c", "<").replace("\\u003e", ">").replace("\\u0026", "&")
    current = current.replace('\\"', '"').replace("\\n", "\n")
    return html.unescape(current)


def html_fragment_to_text(fragment: str) -> str:
    parser = TextExtractor()
    parser.feed(fragment)
    return clean_multiline_text(parser.get_text())


def is_masked_name(value: str | None) -> bool:
    if not value:
        return True
    clean_value = clean_inline_text(value)
    if not clean_value:
        return True
    return "*" in clean_value


def choose_doctor_name(doctor_attrs: dict[str, str]) -> str | None:
    candidates = [
        doctor_attrs.get("by-doctor"),
        doctor_attrs.get("doctor-name-title"),
    ]
    for candidate in candidates:
        if candidate and not is_masked_name(candidate):
            return clean_inline_text(candidate)
    for candidate in candidates:
        if candidate:
            return clean_inline_text(candidate)
    return None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_listing_url(base_url: str, page_number: int) -> str:
    base_url = base_url.rstrip("/")
    if page_number <= 1:
        return base_url
    if PAGINATION_STYLE == "query":
        return f"{base_url}/?paged={page_number}"
    return f"{base_url}/page/{page_number}"


def build_page_numbers(start_page: int, count: int, randomize: bool) -> list[int]:
    if count <= 0:
        return []
    if not randomize:
        return list(range(start_page, start_page + count))
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)
    end_page = start_page + max(count, RANDOM_PAGE_SPAN)
    pages = list(range(start_page, end_page))
    random.shuffle(pages)
    return pages[:count]


def fetch_html(url: str) -> tuple[str, int, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        text = raw.decode(charset, errors="replace")
        status = getattr(response, "status", 200)
        return text, status, hashlib.sha256(raw).hexdigest()


def extract_links(html_text: str, page_url: str) -> list[LinkItem]:
    parser = LinkExtractor(page_url)
    parser.feed(html_text)
    return parser.links


def is_discussion_detail_url(url: str, listing_base: str) -> bool:
    parsed = urlparse(url)
    listing = urlparse(listing_base)
    if parsed.netloc and parsed.netloc != listing.netloc:
        return False
    path = parsed.path.rstrip("/")
    if not path.startswith("/komunitas/topic/"):
        return False
    blocked_fragments = [
        "/komunitas/diskusi",
        "/komunitas$",
        "/komunitas/topik",
        "/login",
        "/register",
        "/tag/",
        "/search",
    ]
    if path in {"/komunitas", "/komunitas/"}:
        return False
    if path.startswith("/komunitas/diskusi"):
        return False
    if any(fragment in path for fragment in blocked_fragments if fragment not in {"/komunitas/", "/komunitas$"}):
        return False
    if parsed.fragment:
        return False
    return True


def unique_detail_links(links: Iterable[LinkItem], listing_base: str) -> list[LinkItem]:
    seen: set[str] = set()
    details: list[LinkItem] = []
    for link in links:
        clean_url = link.url.split("#", 1)[0]
        if not is_discussion_detail_url(clean_url, listing_base):
            continue
        if clean_url in seen:
            continue
        seen.add(clean_url)
        details.append(LinkItem(url=clean_url, text=link.text))
    if MAX_DETAIL_PER_LISTING is not None:
        return details[:MAX_DETAIL_PER_LISTING]
    return details


def extract_title(text_title: str | None, fallback_link_text: str) -> str | None:
    if text_title:
        title = re.sub(r"\s*-\s*Alodokter\s*$", "", text_title, flags=re.IGNORECASE)
        title = clean_inline_text(title)
        if title:
            return title
    fallback = clean_inline_text(fallback_link_text)
    return fallback or None


def parse_indonesian_date(line: str) -> str | None:
    match = re.search(
        r"\b(\d{1,2})\s+"
        r"(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)"
        r"\s+(\d{4})\b",
        line,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    day, month_name, year = match.groups()
    month = INDONESIAN_MONTHS[month_name.casefold()]
    return f"{year}-{month}-{int(day):02d}"


def parse_time(line: str) -> str | None:
    match = re.search(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b", line)
    if not match:
        return None
    hour, minute = match.groups()
    return f"{int(hour):02d}:{minute}"


def trim_boilerplate_lines(lines: list[str]) -> list[str]:
    blocked_exact = {
        "tanya dokter",
        "buat pertanyaan",
        "diskusi kesehatan terbaru",
        "dijawab oleh:",
        "dijawab oleh",
        "oleh:",
        "oleh",
    }
    blocked_contains = [
        "download aplikasi",
        "alodokter",
        "konsultasi lebih cepat",
        "semoga jawaban ini membantu",
    ]
    output: list[str] = []
    for line in lines:
        normalized = line.casefold().strip()
        if normalized in blocked_exact:
            continue
        if any(fragment in normalized for fragment in blocked_contains):
            continue
        output.append(line)
    return output


def parse_detail_page(
    html_text: str,
    detail_url: str,
    listing_url: str,
    page_number: int,
    link_text: str,
    raw_hash: str,
    http_status: int,
) -> ConsultationRecord:
    parser = TextExtractor()
    parser.feed(html_text)
    text = parser.get_text()
    lines = [line for line in text.splitlines() if line.strip()]

    attr_parser = DetailAttributeExtractor()
    attr_parser.feed(html_text)
    member_attrs = attr_parser.member
    doctor_attrs = attr_parser.doctor

    marker_index = find_first_index(lines, lambda item: "dijawab oleh" in item.casefold())
    date_index = find_first_index(lines, lambda item: parse_indonesian_date(item) is not None)
    time_index = find_first_index(lines, lambda item: parse_time(item) is not None)

    doctor_name = choose_doctor_name(doctor_attrs)
    doctor_role = doctor_attrs.get("doctor-title-small") or None
    if doctor_name and doctor_name.casefold().startswith("dr.") and (not doctor_role or doctor_role == "Anggota"):
        doctor_role = "Dokter"
    answered_at_date = None
    answered_at_time = None
    member_post_date = member_attrs.get("member-post-date")
    if member_post_date:
        answered_at_date = parse_indonesian_date(member_post_date)
        answered_at_time = parse_time(member_post_date)

    if marker_index is not None:
        after_marker = lines[marker_index + 1 :]
        for line in after_marker[:8]:
            lower = line.casefold()
            if lower in {"dokter", "doctor"}:
                doctor_role = line
                continue
            if parse_indonesian_date(line) or parse_time(line):
                continue
            if not doctor_name and ("dr." in lower or "dokter" not in lower):
                doctor_name = line
                continue
            if doctor_name and not doctor_role and lower in {"dokter", "dokter umum", "dokter spesialis"}:
                doctor_role = line

    if not answered_at_date and date_index is not None:
        answered_at_date = parse_indonesian_date(lines[date_index])
    if not answered_at_time and time_index is not None:
        answered_at_time = parse_time(lines[time_index])

    member_content = html_fragment_to_text(decode_component_attr(member_attrs.get("member-topic-content")))
    doctor_content = html_fragment_to_text(decode_component_attr(doctor_attrs.get("doctor-topic-content")))

    if member_content:
        question_text = member_content
    else:
        question_end = marker_index if marker_index is not None else date_index
        question_lines = lines[:question_end] if question_end is not None else []
        question_lines = trim_boilerplate_lines(question_lines)
        question_text = "\n".join(question_lines).strip()

    if doctor_content:
        answer_text = doctor_content
    else:
        answer_start_candidates = [idx for idx in [time_index, date_index, marker_index] if idx is not None]
        answer_start = max(answer_start_candidates) + 1 if answer_start_candidates else 0
        answer_lines = lines[answer_start:]
        answer_lines = remove_trailing_doctor_signature(answer_lines, doctor_name)
        answer_lines = trim_boilerplate_lines(answer_lines)
        answer_text = "\n".join(answer_lines).strip()

    title = member_attrs.get("member-topic-title") or extract_title(parser.title, link_text)

    return ConsultationRecord(
        source="alodokter",
        source_type="public_health_consultation",
        url=detail_url,
        listing_url=listing_url,
        page_number=page_number,
        title=title,
        category="penyakit",
        question={
            "raw_text": question_text,
            "clean_text": clean_multiline_text(question_text),
            "asked_at": None,
        },
        answer={
            "raw_text": answer_text,
            "clean_text": clean_multiline_text(answer_text),
            "answered_at_date": answered_at_date,
            "answered_at_time": answered_at_time,
            "doctor_name": doctor_name,
            "doctor_role": doctor_role,
        },
        metadata={
            "related_links": [],
            "scraped_at": now_iso(),
            "language": "id",
            "raw_html_hash": raw_hash,
            "http_status": http_status,
            "parser_version": "alodokter_v1",
            "meta_description": parser.meta_description,
        },
    )


def find_first_index(lines: list[str], predicate) -> int | None:
    for index, line in enumerate(lines):
        if predicate(line):
            return index
    return None


def remove_trailing_doctor_signature(lines: list[str], doctor_name: str | None) -> list[str]:
    if not lines:
        return lines
    output = list(lines)
    for index, line in enumerate(output):
        if line.casefold().strip() == "oleh:":
            return output[:index]
        if doctor_name and line.strip() == doctor_name and index > 0:
            previous = output[index - 1].casefold().strip()
            if previous in {"oleh:", "oleh"}:
                return output[: index - 1]
    return output


def clean_multiline_text(text: str) -> str:
    lines = [clean_inline_text(line) for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def polite_sleep() -> None:
    delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
    time.sleep(delay)


def crawl() -> dict:
    page_numbers = build_page_numbers(START_PAGE, JUMLAH_HALAMAN, RANDOM_HALAMAN)
    records: list[ConsultationRecord] = []
    errors: list[CrawlError] = []
    visited_detail_urls: set[str] = set()
    listing_summaries: list[dict] = []

    for page_number in page_numbers:
        listing_url = build_listing_url(URL, page_number)
        print(f"[listing] page={page_number} url={listing_url}")
        try:
            listing_html, listing_status, listing_hash = fetch_html(listing_url)
            links = extract_links(listing_html, listing_url)
            detail_links = unique_detail_links(links, URL)
            listing_summaries.append(
                {
                    "page_number": page_number,
                    "url": listing_url,
                    "http_status": listing_status,
                    "raw_html_hash": listing_hash,
                    "detail_link_count": len(detail_links),
                    "detail_urls": [item.url for item in detail_links],
                }
            )
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(CrawlError(url=listing_url, context="listing", error=repr(exc)))
            continue

        polite_sleep()

        for link in detail_links:
            if link.url in visited_detail_urls:
                continue
            visited_detail_urls.add(link.url)
            print(f"  [detail] {link.url}")
            try:
                detail_html, detail_status, detail_hash = fetch_html(link.url)
                record = parse_detail_page(
                    html_text=detail_html,
                    detail_url=link.url,
                    listing_url=listing_url,
                    page_number=page_number,
                    link_text=link.text,
                    raw_hash=detail_hash,
                    http_status=detail_status,
                )
                records.append(record)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                errors.append(CrawlError(url=link.url, context="detail", error=repr(exc)))
            polite_sleep()

    return {
        "crawl_metadata": {
            "source": "alodokter",
            "base_url": URL,
            "start_page": START_PAGE,
            "jumlah_halaman": JUMLAH_HALAMAN,
            "random_halaman": RANDOM_HALAMAN,
            "random_page_span": RANDOM_PAGE_SPAN,
            "pagination_style": PAGINATION_STYLE,
            "max_detail_per_listing": MAX_DETAIL_PER_LISTING,
            "created_at": now_iso(),
            "record_count": len(records),
            "error_count": len(errors),
        },
        "listings": listing_summaries,
        "records": [asdict(record) for record in records],
        "errors": [asdict(error) for error in errors],
    }


def build_research_dataset(records: list[dict]) -> list[dict]:
    dataset: list[dict] = []
    for index, record in enumerate(records, start=1):
        question = record.get("question") or {}
        answer = record.get("answer") or {}
        dataset.append(
            {
                "document_id": f"alodokter_{index:06d}",
                "input_text": question.get("clean_text") or question.get("raw_text") or "",
                "source_type": "public_consultation",
                "category": record.get("category") or "penyakit",
                "date": answer.get("answered_at_date"),
                "doctor_present": bool(answer.get("doctor_name")),
                "doctor_name_removed": True,
                "annotation_status": "raw",
                "provenance": {
                    "source": record.get("source"),
                    "url": record.get("url"),
                    "listing_url": record.get("listing_url"),
                    "page_number": record.get("page_number"),
                    "title": record.get("title"),
                },
            }
        )
    return dataset


def build_qa_pairs(records: list[dict]) -> list[dict]:
    qa_pairs: list[dict] = []
    for record in records:
        qa_pairs.append(
            {
                "source": record.get("source"),
                "source_type": record.get("source_type"),
                "url": record.get("url"),
                "listing_url": record.get("listing_url"),
                "title": record.get("title"),
                "category": record.get("category"),
                "question": record.get("question") or {
                    "raw_text": "",
                    "clean_text": "",
                    "asked_at": None,
                },
                "answer": record.get("answer") or {
                    "raw_text": "",
                    "clean_text": "",
                    "answered_at_date": None,
                    "answered_at_time": None,
                    "doctor_name": None,
                    "doctor_role": None,
                },
                "metadata": record.get("metadata") or {
                    "related_links": [],
                    "scraped_at": None,
                    "language": "id",
                    "raw_html_hash": None,
                    "parser_version": "alodokter_v1",
                },
            }
        )
    return qa_pairs


def save_json(payload: object, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawler standalone Alodokter komunitas/diskusi/penyakit.")
    parser.add_argument("--output", default=OUTPUT_JSON, help="Path output JSON.")
    parser.add_argument("--dataset-output", default=OUTPUT_DATASET_JSON, help="Path output JSON dataset riset.")
    parser.add_argument("--qa-output", default=OUTPUT_QA_JSON, help="Path output JSON pasangan pertanyaan-jawaban.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = crawl()
    save_json(payload, args.output)
    qa_pairs = build_qa_pairs(payload["records"])
    save_json(qa_pairs, args.qa_output)
    dataset = build_research_dataset(payload["records"])
    save_json(dataset, args.dataset_output)
    print(
        f"[done] records={payload['crawl_metadata']['record_count']} "
        f"errors={payload['crawl_metadata']['error_count']}"
    )
    print(f"[saved] raw={args.output}")
    print(f"[saved] qa_pairs={args.qa_output}")
    print(f"[saved] dataset={args.dataset_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
