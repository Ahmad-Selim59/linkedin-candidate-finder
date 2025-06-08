import os
from dotenv import load_dotenv
from scrapers.linkedin_scraper import save_linkedin_session, scrape_linkedin_profiles
from scrapers.experience_extractor import extract_experience_data
from llm.analyzer import format_experience_for_llm, analyze_candidate_experience

load_dotenv()


def save_results(
    name: str,
    profile_url: str,
    experience_url: str,
    experience_text: str,
    analysis: str,
    is_shortlisted: bool,
):
    """Save candidate results to appropriate file"""
    filename = (
        "shortlisted_candidates.txt" if is_shortlisted else "rejected_candidates.txt"
    )

    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"Name: {name}\n")
        f.write(f"LinkedIn Profile: {profile_url}\n")
        f.write(f"Experience Page: {experience_url}\n")
        if is_shortlisted:
            f.write(f"Experience Summary:\n{experience_text}\n")
        f.write(f"Analysis: {analysis}\n")
        f.write("-" * 80 + "\n\n")


def scrape_and_shortlist_linkedin(
    search_query: str, location: str, max_profiles: int = 1
):
    """Main function to scrape LinkedIn and analyze candidates"""
    shortlisted_count = 0
    rejected_count = 0

    profiles_data = scrape_linkedin_profiles(search_query, location, max_profiles)

    for profile in profiles_data:
        name = profile["name"]
        print(f"\n👤 Analyzing {name}...")

        experience_text = format_experience_for_llm(profile["experience_entries"])

        print("📋 Extracted Experience Profile:")
        print(
            experience_text[:500] + "..."
            if len(experience_text) > 500
            else experience_text
        )
        print("\n" + "=" * 50)

        if profile["experience_entries"]:
            print("🧠 Calling LLM to analyze candidate...")

            try:
                analysis = analyze_candidate_experience(experience_text, search_query)
                print(f"📊 LLM Analysis: {analysis}")

                is_shortlisted = "SHORTLIST" in analysis.upper()
                save_results(
                    name=name,
                    profile_url=profile["profile_url"],
                    experience_url=profile["experience_url"],
                    experience_text=experience_text,
                    analysis=analysis,
                    is_shortlisted=is_shortlisted,
                )

                if is_shortlisted:
                    shortlisted_count += 1
                    print(f"✅ SHORTLISTED: {name}")
                else:
                    rejected_count += 1
                    print(f"❌ REJECTED: {name}")

            except Exception as e:
                print(f"⚠️ Error analyzing {name}: {e}")
                continue
        else:
            print(f"⚠️ No experience data found for {name}")
            rejected_count += 1

    print(f"\n📊 FINAL RESULTS:")
    print(f"✅ Shortlisted: {shortlisted_count}")
    print(f"❌ Rejected: {rejected_count}")
    print(f"📁 Results saved to shortlisted_candidates.txt")
    print(f"📁 Rejections saved to rejected_candidates.txt")


if __name__ == "__main__":
    # save_linkedin_session()  # Run this first to save login session
    scrape_and_shortlist_linkedin("Cyber Security Engineer", "Dublin, Ireland", 1)
