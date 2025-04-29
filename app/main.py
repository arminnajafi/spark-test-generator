import logging

from langchain_core.globals import set_debug

from app import set_up_logging
from app.agents.test_generator import generate_test
from app.config import ensure_env
from app.doc_scraper import collect_reference_pages

ensure_env()
set_up_logging()
logger = logging.getLogger(__name__)
set_debug(True)


def main():
    base_url = "https://spark.apache.org/docs/latest/api/python/reference/"
    reference_pages = collect_reference_pages(root=base_url)

    for reference_page in reference_pages[:2]:
        generate_test(reference_page=reference_page)


if __name__ == "__main__":
    main()
