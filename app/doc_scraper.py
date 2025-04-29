from __future__ import annotations

import json
import logging
import re
import requests

from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from app import set_up_logging, ROOT_DIRECTORY

set_up_logging()

logger = logging.getLogger(__name__)


def fetch(url: str) -> BeautifulSoup:
    headers = {"User-Agent": "scraper"}
    html = requests.get(url, headers=headers, timeout=20).text
    return BeautifulSoup(html, "html.parser")


def locate_main_nav_ul(soup: BeautifulSoup):
    """
    Find the <ul> inside the main navigation sidebar.

    Handles Spark docs that look like:
      <nav class="bd-links" id="bd-docs-nav" aria-label="Main navigation">
        <div class="bd-toc-item active">
          <ul class="current nav bd-sidenav">
    """

    # First, find the main <nav> using ID or aria-label
    main_nav = soup.find("nav", {"id": "bd-docs-nav"})

    if not main_nav:
        main_nav = soup.find(
            "nav", attrs={"aria-label": re.compile(r"main navigation", re.I)}
        )

    if not main_nav:
        raise RuntimeError("Could not locate the main navigation <nav> element.")

    # Then, find the <ul> inside it
    nav_ul = main_nav.select_one("div.bd-toc-item > ul.bd-sidenav")

    if not nav_ul:
        raise RuntimeError("Could not locate the navigation <ul> inside the <nav>.")

    return nav_ul


def is_leaf(li_tag) -> bool:
    """Leaf = <li> that is *not* marked has-children."""
    return not any("has-children" in cls for cls in li_tag.get("class", []))


@dataclass
class ReferencePage:
    title: str
    url: str


def collect_reference_pages(root: str) -> List[ReferencePage]:
    soup = fetch(root)
    main_nav_ul = locate_main_nav_ul(soup)
    reference_pages = []
    li_list = main_nav_ul.find_all("li")

    for li in li_list:
        a = li.find("a", recursive=False)
        title = a.text.strip()
        href = a.get("href", "")
        url = urljoin(root, href)

        if is_leaf(li):
            reference_pages.append(ReferencePage(title=title, url=url))

    return reference_pages


def dump_to_json(reference_pages: List[ReferencePage]):
    with open(ROOT_DIRECTORY / "reference_pages.json", "w", encoding="utf-8") as f:
        json.dump(
            [reference_page.__dict__ for reference_page in reference_pages],
            f,
            indent=2,
            ensure_ascii=False,
        )
    logger.info(
        f"\nSaved {reference_pages.__len__()} reference pages to reference_pages.json."
    )


if __name__ == "__main__":
    base_url = "https://spark.apache.org/docs/latest/api/python/reference/"
    _reference_pages = collect_reference_pages(root=base_url)

    # pretty-print
    for _reference_page in _reference_pages:
        logger.info(f"{_reference_page.title}: {_reference_page.url}")

    # Dump to JSON
    dump_to_json(reference_pages=_reference_pages)
