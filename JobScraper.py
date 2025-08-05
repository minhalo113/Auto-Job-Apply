"""Simple Indeed job scraping script.

This module provides a small command line tool for collecting job
postings from Indeed.com.  It is intentionally lightweight and only
depends on :mod:`requests` and :mod:`beautifulsoup4` which are widely
used third‑party libraries.

Example
-------
Run the script from the command line::

    python JobScraper.py --query "python developer" --location "New York"

The results are printed to stdout.
"""

from dataclasses import dataclass
from typing import List

import requests
from bs4 import BeautifulSoup


@dataclass
class JobPosting:
    """Representation of a single job posting returned by Indeed."""

    title: str
    company: str
    location: str
    summary: str
    url: str


BASE_URL = "https://www.indeed.com/jobs"


def _build_search_url(query: str, location: str, start: int = 0) -> str:
    """Return a search URL for the given parameters."""

    params = {
        "q": query,
        "l": location,
        "start": start,
    }
    # Manually build the query string to avoid introducing urllib dependency
    query_str = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
    return f"{BASE_URL}?{query_str}"


def scrape_jobs(query: str, location: str, pages: int = 1) -> List[JobPosting]:
    """Scrape job postings from Indeed.

    Parameters
    ----------
    query:
        Search query string, e.g. ``"python developer"``.
    location:
        Desired job location.
    pages:
        Number of result pages to retrieve.  Each page usually contains
        around ten results.  ``pages`` defaults to 1.
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"
    }
    results: List[JobPosting] = []

    for page in range(pages):
        url = _build_search_url(query, location, start=page * 10)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for card in soup.select("div.jobsearch-SerpJobCard, div.cardOutline"):
            # Title and link
            title_tag = card.select_one("h2.title a") or card.select_one("h2.jobTitle a")
            if not title_tag:
                continue
            title = title_tag.get("title") or title_tag.text.strip()
            link = title_tag.get("href", "")
            if link and link.startswith("/"):
                link = "https://www.indeed.com" + link

            # Company
            company_tag = card.select_one("span.company") or card.select_one("span.companyName")
            company = company_tag.text.strip() if company_tag else ""

            # Location
            loc_tag = card.select_one("div.recJobLoc") or card.select_one("div.companyLocation")
            location_text = (
                loc_tag.get("data-rc-loc")
                if loc_tag and loc_tag.get("data-rc-loc")
                else loc_tag.text.strip() if loc_tag else ""
            )

            # Summary
            summary_tag = card.select_one("div.summary") or card.select_one("div.job-snippet")
            summary = summary_tag.text.strip() if summary_tag else ""

            results.append(
                JobPosting(
                    title=title,
                    company=company,
                    location=location_text,
                    summary=summary,
                    url=link,
                )
            )

    return results


def main() -> None:
    """Entry point for the command line interface."""

    # import argparse

    # parser = argparse.ArgumentParser(description="Scrape job listings from Indeed.com")
    # parser.add_argument("--query", required=True, help="Job search query")
    # parser.add_argument("--location", required=True, help="Job location")
    # parser.add_argument(
    #     "--pages", type=int, default=1, help="Number of pages of results to retrieve"
    # )
    # args = parser.parse_args()

    postings = scrape_jobs("computer science", "Canada", 1)

    for job in postings:
        print(f"{job.title} at {job.company} ({job.location})")
        if job.summary:
            print(job.summary)
        print(job.url)
        print("-" * 60)


if __name__ == "__main__":
    main()
