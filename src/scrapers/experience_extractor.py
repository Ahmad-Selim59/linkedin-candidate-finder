from bs4 import BeautifulSoup
from typing import List, Dict


def extract_experience_data(soup: BeautifulSoup) -> List[Dict]:
    """Extract complete experience data from the dedicated experience page"""
    experience_entries = []

    # Look for experience entries in the dedicated experience page
    job_entries = soup.find_all(
        "li",
        class_="pvs-list__paged-list-item artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column",
    )

    # Also try to find by ID pattern as backup
    if not job_entries:
        job_entries = soup.find_all(
            "li",
            id=lambda x: x and "EXPERIENCE-VIEW-DETAILS-profile" in x if x else False,
        )

    print(
        f"📊 Found {len(job_entries)} experience entries on dedicated experience page"
    )

    for i, job_entry in enumerate(job_entries):
        try:
            job_data = _extract_job_entry(job_entry, i)
            if job_data:
                experience_entries.append(job_data)
        except Exception as e:
            print(f"⚠️ Error extracting experience entry {i+1}: {e}")
            continue

    return experience_entries


def _extract_job_entry(job_entry, index: int) -> Dict:
    """Extract data from a single job entry"""
    job_data = {}
    print(f"\n🔍 Processing experience entry {index+1}")

    job_data["title"] = _extract_job_title(job_entry)

    company_info = _extract_company_info(job_entry)
    job_data.update(company_info)

    job_data["duration"] = _extract_duration(job_entry)

    job_data["location"] = _extract_location(job_entry)

    job_data["description"] = _extract_description(job_entry)

    if job_data.get("title") or job_data.get("company"):
        print(
            f"✅ Successfully extracted experience {index+1}: {job_data.get('title', 'Unknown Title')} at {job_data.get('company', 'Unknown Company')}"
        )
        return job_data
    else:
        print(f"⚠️ Skipped entry {index+1} - missing essential info")
        return None


def _extract_job_title(job_entry) -> str:
    """Extract job title from job entry"""
    title_selectors = [
        "div[data-field='experience-company-name'] span[aria-hidden='true']",
        ".display-flex.align-items-center span[aria-hidden='true']",
        ".mr1.hoverable-link-text span[aria-hidden='true']",
        ".break-words span[aria-hidden='true']",
    ]

    for selector in title_selectors:
        title_elem = job_entry.select_one(selector)
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            if title_text and len(title_text) > 2:
                print(f"✅ Found title: {title_text}")
                return title_text

    # Fallback search
    title_spans = job_entry.find_all("span", {"aria-hidden": "true"})
    for span in title_spans[:3]:
        text = span.get_text(strip=True)
        if (
            text
            and len(text) > 5
            and len(text) < 100
            and not any(
                keyword in text.lower()
                for keyword in [
                    "·",
                    "full-time",
                    "part-time",
                    "jan",
                    "feb",
                    "mar",
                    "apr",
                    "may",
                    "jun",
                ]
            )
        ):
            print(f"✅ Found title (fallback): {text}")
            return text

    return ""


def _extract_company_info(job_entry) -> Dict:
    """Extract company name and employment type"""
    company_info = {}

    # Try to find company info in spans with specific patterns
    company_spans = job_entry.find_all("span", class_="t-14 t-normal")
    for span in company_spans:
        span_text = span.get_text(strip=True)
        if "·" in span_text:
            company_parts = span_text.split("·")
            if len(company_parts) >= 2:
                company_name = company_parts[0].strip()
                employment_type = company_parts[1].strip()
                if company_name and len(company_name) > 1:
                    company_info["company"] = company_name
                    company_info["employment_type"] = employment_type
                    print(f"✅ Found company: {company_name} ({employment_type})")
                    return company_info

    # Fallback search for company name
    all_spans = job_entry.find_all("span", {"aria-hidden": "true"})
    for span in all_spans:
        text = span.get_text(strip=True)
        if (
            text
            and 3 < len(text) < 80
            and not any(
                date_word in text.lower()
                for date_word in [
                    "jan",
                    "feb",
                    "mar",
                    "apr",
                    "may",
                    "jun",
                    "jul",
                    "aug",
                    "sep",
                    "oct",
                    "nov",
                    "dec",
                    "present",
                    "mos",
                    "yr",
                ]
            )
            and not any(
                emp_type in text.lower()
                for emp_type in ["full-time", "part-time", "contract", "internship"]
            )
        ):

            if (
                any(
                    suffix in text.lower()
                    for suffix in [
                        "inc",
                        "llc",
                        "ltd",
                        "corp",
                        "company",
                        "technologies",
                        "solutions",
                        "systems",
                        "software",
                    ]
                )
                or len(text.split()) <= 4
            ):
                company_info["company"] = text
                print(f"✅ Found company (fallback): {text}")
                return company_info

    return company_info


def _extract_duration(job_entry) -> str:
    """Extract duration from job entry"""
    date_spans = job_entry.find_all("span", class_="t-14 t-normal t-black--light")
    for span in date_spans:
        text = span.get_text(strip=True)
        if any(
            indicator in text.lower()
            for indicator in [
                "jan",
                "feb",
                "mar",
                "apr",
                "may",
                "jun",
                "jul",
                "aug",
                "sep",
                "oct",
                "nov",
                "dec",
                "present",
                "mos",
                "yr",
                "month",
                "year",
            ]
        ):
            print(f"✅ Found duration: {text}")
            return text
    return ""


def _extract_location(job_entry) -> str:
    """Extract location from job entry"""
    location_spans = job_entry.find_all("span", class_="t-14 t-normal t-black--light")
    for span in location_spans:
        text = span.get_text(strip=True)
        location_keywords = [
            "colombia",
            "bogota",
            "dublin",
            "ireland",
            "india",
            "mumbai",
            "pune",
            "remote",
            "hybrid",
            "on-site",
            "united states",
            "usa",
            "uk",
            "canada",
            "new york",
            "california",
            "texas",
            "florida",
            "london",
            "paris",
            "berlin",
        ]
        if any(keyword in text.lower() for keyword in location_keywords):
            print(f"✅ Found location: {text}")
            return text
    return ""


def _extract_description(job_entry) -> str:
    """Extract job description from job entry"""
    description_parts = []

    # Look for description containers
    desc_containers = job_entry.find_all(
        "div",
        class_=lambda x: x
        and any(
            cls in str(x)
            for cls in [
                "pvs-list__outer-container",
                "pvs-entity__sub-components",
                "display-flex",
            ]
        ),
    )

    for container in desc_containers:
        desc_spans = container.find_all("span", {"aria-hidden": "true"})
        for span in desc_spans:
            desc_text = span.get_text(strip=True)
            if len(desc_text) > 50 and not any(
                keyword in desc_text.lower()
                for keyword in ["full-time", "part-time", "contract"]
            ):
                if desc_text not in description_parts:
                    description_parts.append(desc_text)
                    print(f"✅ Found description part: {desc_text[:100]}...")

    # Look for bullet points
    ul_elements = job_entry.find_all("ul")
    for ul in ul_elements:
        li_elements = ul.find_all("li")
        for li in li_elements:
            text = li.get_text(strip=True)
            if text and len(text) > 10:
                bullet_text = f"• {text}"
                if bullet_text not in description_parts:
                    description_parts.append(bullet_text)

    return (
        "\n\n".join(description_parts)
        if description_parts
        else "No detailed description provided"
    )
