from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional

from scrapers.experience_extractor import extract_experience_data


def save_linkedin_session():
    """Save LinkedIn login session for future use"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.linkedin.com/login")
        print("Please log in to LinkedIn manually in the browser window...")

        page.wait_for_timeout(60000)  # Give you 60 seconds to log in

        context.storage_state(path="auth.json")
        print("✅ Login session saved to auth.json")
        browser.close()


def get_experience_url_from_profile(profile_url: str) -> str:
    """Convert profile URL to experience-specific URL"""
    if "/details/experience/" in profile_url:
        return profile_url

    # Remove query parameters and trailing slashes
    if "?" in profile_url:
        clean_url = profile_url.split("?")[0]
    else:
        clean_url = profile_url

    clean_url = clean_url.rstrip("/")

    if "/in/" in clean_url:
        return f"{clean_url}/details/experience/"

    return profile_url


def scrape_linkedin_profiles(
    search_query: str, location: str, max_profiles: int = 1
) -> List[Dict]:
    """Scrape LinkedIn profiles based on search criteria"""
    with sync_playwright() as p:
        print("🚀 Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        profiles_data = []
        page_num = 1
        profiles_found = 0

        while profiles_found < max_profiles:
            # Navigate to people search with pagination
            print(f"🌐 Navigating to LinkedIn People Search (Page {page_num})...")
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query.replace(' ', '%20')}%20{location.replace(' ', '%20')}"
            if page_num > 1:
                search_url += f"&page={page_num}"

            page.goto(search_url)
            print(f"🌍 On People Search: {page.url}")

            page.wait_for_timeout(6000)

            # Find the search results container using the correct class
            search_results = page.query_selector("ul.eXOGCNtWZCUfVkYFgXYYeCjJSoAhEDHk")
            if not search_results:
                print("⚠️ Could not find search results container")
                break

            # Extract all list items (individual profile results)
            profile_items = search_results.query_selector_all(
                "li.nrxCTNBwEvLjnjUMRDlltdOsOQfMBkCNfDFxZfpE"
            )
            print(f"🔗 Found {len(profile_items)} profile items on page {page_num}")

            # Extract profile links from each list item
            profile_links = []
            for item in profile_items:
                # Look for the anchor tag with the profile link inside each list item
                link_element = item.query_selector(
                    'a[href*="/in/"][data-test-app-aware-link]'
                )
                if link_element:
                    href = link_element.get_attribute("href")
                    if href:
                        # Clean the URL by removing query parameters to get the base profile URL
                        base_url = href.split("?")[0]
                        if base_url not in [
                            link[0] for link in profile_links
                        ]:  # Avoid duplicates
                            profile_links.append(
                                (base_url, href)
                            )  # Store both clean and original

            print(f"📋 Extracted {len(profile_links)} unique profile links")

            for i, (clean_url, original_url) in enumerate(profile_links):
                if profiles_found >= max_profiles:
                    break

                print(f"\n➡️ Visiting profile #{profiles_found + 1}: {clean_url}")

                # Navigate to the experience-specific page
                experience_url = get_experience_url_from_profile(clean_url)
                print(f"🎯 Going to experience page: {experience_url}")

                try:
                    page.goto(experience_url)
                    page.wait_for_timeout(6000)

                    soup = BeautifulSoup(page.content(), "html.parser")

                    name = extract_name(soup)
                    print(f"👤 Found profile for: {name}")

                    experience_entries = extract_experience_data(soup)
                    print(
                        f"📊 Found {len(experience_entries)} experience entries on dedicated experience page"
                    )

                    profiles_data.append(
                        {
                            "name": name,
                            "profile_url": clean_url,
                            "experience_url": experience_url,
                            "experience_entries": experience_entries,
                        }
                    )
                    profiles_found += 1

                except Exception as e:
                    print(f"❌ Error processing profile {clean_url}: {str(e)}")
                    continue

            # Check if we need to go to next page
            if profiles_found < max_profiles and len(profile_links) > 0:
                # Check if there's a next page button
                next_button = page.query_selector(
                    'button[aria-label="Next"]:not([disabled])'
                )
                if next_button:
                    page_num += 1
                    print(f"➡️ Moving to page {page_num}")
                else:
                    print("⚠️ No more pages available or Next button is disabled")
                    break
            else:
                break

        browser.close()
        return profiles_data


def extract_name(soup: BeautifulSoup) -> str:
    """Extract name from LinkedIn profile page"""
    name_selectors = ["h1", ".text-heading-xlarge", ".break-words"]
    for selector in name_selectors:
        name_elem = soup.select_one(selector)
        if name_elem:
            potential_name = name_elem.get_text(strip=True)
            if len(potential_name) < 100 and potential_name:  # Reasonable name length
                return potential_name
    return "Unknown"
