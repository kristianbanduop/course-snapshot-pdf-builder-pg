from pathlib import Path
import json
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

DATA_DIR = Path("data")
OUTPUT_JSON = Path("extracted.json")

OVERVIEW_PLACEHOLDER = "Course overview details are being finalised and will be updated soon."
HIGHLIGHTS_PLACEHOLDER = ["Details are being finalised and will be updated soon."]
MODULE_PLACEHOLDER = "Details for this module are being finalised and will be updated soon."
CREDIT_PLACEHOLDER = "Credit value to be confirmed."


def clean_text(el):
    if not el:
        return ""
    return " ".join(el.stripped_strings)


def fetch_soup(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_overview(soup):
    h2 = soup.find("h2", id="overview")
    if not h2:
        return OVERVIEW_PLACEHOLDER

    container = h2.find_next("div", class_="text-highlighted__content")
    text = clean_text(container)
    return text if text else OVERVIEW_PLACEHOLDER


def extract_highlights(soup):
    for block in soup.select("div.text-highlighted__content"):
        h3 = block.find("h3")
        if h3 and "Course highlights" in h3.get_text(strip=True):
            lis = block.find_all("li")
            items = [clean_text(li) for li in lis if clean_text(li)]
            return items if items else HIGHLIGHTS_PLACEHOLDER
    return HIGHLIGHTS_PLACEHOLDER


def parse_credits(title):
    m = re.search(r"(\d+)\s*credits?", title, re.I)
    if not m:
        return CREDIT_PLACEHOLDER
    return "Not applicable" if m.group(1) == "0" else m.group(1)


def extract_modules(soup):
    modules = {}

    modules_h2 = soup.find("h2", id="modules")
    if not modules_h2:
        return modules

    study_heading = modules_h2.find_next("h3", class_="tabs__heading")
    if not study_heading:
        return modules

    tabs_container = study_heading.find_next("div", class_="tabs__content")
    if not tabs_container:
        return modules

    for tabpane in tabs_container.select("div[role='tabpanel']"):
        tab_id = tabpane.get("aria-labelledby", "")
        tab_button = soup.find(id=tab_id)
        year_label = clean_text(tab_button) if tab_button else "Year"

        year_modules = []

        for accordion in tabpane.select("div.accordion"):
            section_title_el = accordion.find("h3", class_="accordion__heading")
            section_title = clean_text(section_title_el).lower() if section_title_el else ""
            core_optional = "Optional" if "optional" in section_title else "Core"

            for item in accordion.select("div.accordion-item--module"):
                title_span = item.select_one("span.accordion-item__button-title")
                if not title_span:
                    continue

                title_text = clean_text(title_span)
                if not title_text or title_text.lower() == "close all":
                    continue

                module_name = re.sub(r"\s*-\s*\d+\s*credits?", "", title_text, flags=re.I).strip()
                credits = parse_credits(title_text)

                desc_container = item.select_one("div.accordion-item__content")
                description = clean_text(desc_container) if desc_container else MODULE_PLACEHOLDER
                if not description:
                    description = MODULE_PLACEHOLDER

                year_modules.append({
                    "module_name": module_name,
                    "credits": credits,
                    "core_optional": core_optional,
                    "description": description
                })

        if year_modules:
            modules[year_label] = year_modules

    return modules


def main():
    df = pd.read_excel(DATA_DIR / "courses.xlsx")

    results = []

    for _, row in df.iterrows():
        url = str(row["Course URL"]).strip()
        if not url:
            continue

        print(f"Extracting: {url}")

        soup = fetch_soup(url)

        course = {
            "faculty": row.get("Faculty", ""),
            "school": row.get("School", ""),
            "title": row.get("Course title", ""),
            "award": row.get("Award", ""),
            "url": url,
            "overview": extract_overview(soup),
            "highlights": extract_highlights(soup),
            "modules": extract_modules(soup),
        }

        results.append(course)

    OUTPUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Wrote {len(results)} courses to {OUTPUT_JSON.resolve()}")


if __name__ == "__main__":
    main()
