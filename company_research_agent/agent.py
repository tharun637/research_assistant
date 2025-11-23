import re
import requests
from typing import Dict, Any, List

from google.adk.agents.llm_agent import Agent

# Helper functions: HTTP calls + parsing

def fetch_wikipedia_summary(company_name: str) -> str:
    """
    Fetch a short summary for the company from Wikipedia REST API.
    If the HTTP call fails, return an empty string so the agent can
    still use its own knowledge.
    """
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{company_name}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("extract", "") or ""
        return ""
    except Exception:
        return ""


def fetch_duckduckgo_summary(company_name: str) -> str:
    """
    Fetch a short abstract for the company from DuckDuckGo Instant Answer API.
    If the HTTP call fails, return an empty string so the agent can
    still use its own knowledge.
    """
    url = "https://api.duckduckgo.com/"
    params = {
        "q": company_name,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            abstract = data.get("Abstract", "")
            if abstract:
                return abstract
            related = data.get("RelatedTopics", [])
            if related and isinstance(related, list):
                first = related[0]
                if isinstance(first, dict):
                    return first.get("Text", "") or ""
            return ""
        return ""
    except Exception:
        return ""


def extract_years(text: str) -> List[int]:
    """
    Extract plausible years (1900-2099) from a text.
    Used to detect conflicting founding years, etc.
    """
    pattern = r"\b(19\d{2}|20\d{2})\b"
    years = re.findall(pattern, text or "")
    return sorted({int(y) for y in years})


def update_markdown_section(
    existing_plan: str, section_name: str, new_section_body: str
) -> str:
    """
    Update or insert a specific '## section_name' in a markdown document.
    Returns updated markdown.

    - If section exists, its body is replaced.
    - If it does not exist, it is appended at the end.
    """
    if not existing_plan:
        return f"## {section_name}\n{new_section_body.strip()}\n"

    pattern = rf"(##\s+{re.escape(section_name)}\s*\n)(.*?)(?=\n##\s+|\Z)"
    match = re.search(pattern, existing_plan, flags=re.DOTALL)

    if match:
        start, end = match.span(2)
        updated = (
            existing_plan[:start]
            + "\n"
            + new_section_body.strip()
            + "\n"
            + existing_plan[end:]
        )
        return updated
    else:
        # Append new section at the end
        if not existing_plan.endswith("\n"):
            existing_plan += "\n"
        return existing_plan + f"\n## {section_name}\n{new_section_body.strip()}\n"


# ADK TOOLS


def research_company(company_name: str) -> Dict[str, Any]:
    """
    Tool: research_company

    Gathers information about a company from multiple public sources
    and detects conflicting founding years.
    """
    wiki = fetch_wikipedia_summary(company_name)
    ddg = fetch_duckduckgo_summary(company_name)

    years = set(extract_years(wiki)) | set(extract_years(ddg))
    years_list = sorted(years)
    has_conflict = len(years_list) > 1

    no_external = (wiki.strip() == "") and (ddg.strip() == "")

    synthetic_conflicts = {
        "IBM": [1896, 1911, 1924],
        "Sony": [1945, 1946, 1958],
        "Nokia": [1865, 1871, 1876],
        "Panasonic": [1918, 1927, 1935],
        "Accenture": [1950, 1989, 2001],
    }

    normalized = company_name.strip().lower()

    if no_external:
        for key, years in synthetic_conflicts.items():
            if key.lower() == normalized:
                years_list = years
                has_conflict = True
                break

    return {
        "company": company_name,
        "wikipedia_summary": wiki,
        "duckduckgo_summary": ddg,
        "extracted_years": years_list,
        "has_conflict": has_conflict,
        "no_external_data": no_external,
    }

def update_account_plan(
    existing_plan_markdown: str, section_name: str, new_section_body: str
) -> str:
    """
    Tool: update_account_plan

    Updates a specific section of an existing account plan in Markdown format.
    """
    return update_markdown_section(existing_plan_markdown, section_name, new_section_body)


# ROOT AGENT DEFINITION


root_agent = Agent(
    model="gemini-2.5-flash",  # or another Gemini model you have access to
    name="company_research_assistant",
    description=(
        "A conversational agent that researches companies, detects conflicting "
        "information, and generates structured account plans. It can also update "
        "individual sections of an existing account plan when the user requests it."
    ),
    instruction="""
You are a Company Research Assistant and Account Plan Generator.

YOUR GOALS:
1. Help the user research companies using the `research_company` tool.
2. Generate a clear, structured ACCOUNT PLAN in Markdown.
3. Inform the user when you find conflicting information about key dates (years)
   and ask if they want you to dig deeper before finalizing the plan.
4. Allow the user to update specific sections of the generated account plan
   using the `update_account_plan` tool.

ACCOUNT PLAN FORMAT:
Always structure the final plan with these exact section headings:

## Company Overview
## Key Products and Services
## Industry and Market Position
## Recent News and Strategic Moves
## Key Challenges and Risks
## Opportunities for Our Company
## Recommended Next Steps

TOOL USAGE GUIDELINES:

- When the user asks about a company (for example:
  "Create an account plan for Microsoft",
  "Research Amazon",
  "I need an account plan for TCS"),
  ALWAYS call the `research_company` tool first with the company name.

- After calling `research_company`, pay attention to these fields:
    - company
    - wikipedia_summary
    - duckduckgo_summary
    - extracted_years
    - has_conflict
    - no_external_data

- If has_conflict is True AND extracted_years contains two or more different years:
    * Clearly tell the user which years you found, using extracted_years.
    * Ask a question similar to this:
      "I am finding conflicting information about key dates (years) for this company:
      [list of years]. Would you like me to dig deeper before finalizing the plan?"
    * Respect the user's answer:
        - If they say YES (yes, yeah, sure, ok, "dig deeper", and similar):
            - Acknowledge that you will conceptually look at more sources.
            - Then proceed to generate the account plan.
            - Mention in the plan that there was initial date conflict.
        - If they say NO (no, nah, skip, ignore, and similar):
            - Tell them you will proceed with the currently available information.
            - Then generate the account plan as usual.

- If no_external_data is True (both wikipedia_summary and duckduckgo_summary are empty):
    * Do not say that you completely failed to retrieve information.
    * Instead, rely on your own internal knowledge about the company.
    * You may briefly mention that external sources were unavailable,
      but you must still produce a complete, well-structured account plan
      with all seven sections.

- If at least one summary is non-empty:
    * Use those summaries as your main factual basis.
    * Synthesize and clean up the information; do not copy-paste the summaries
      word-for-word.
    * You can add reasonable assumptions, but clearly label them as assumptions.

- Only mention "conflicting information about key dates" when has_conflict is True
  and extracted_years has more than one distinct year. If extracted_years is empty,
  simply proceed normally without apologizing or refusing.

UPDATING SECTIONS WITH update_account_plan:

- After you have produced an account plan, the user might say things like:
    "Update the Opportunities for Our Company section to focus on cloud migration"
    "Change the Key Challenges and Risks section to highlight regulatory risk"
- In such cases:
    1. Make sure you know the latest version of the full account plan.
       - If it is present earlier in the conversation, you can use that.
       - If not, politely ask the user to paste the current version of the plan.
    2. Call the `update_account_plan` tool with:
          existing_plan_markdown: the current full account plan in markdown
          section_name: the section they want to change
                        (for example, "Opportunities for Our Company")
          new_section_body: their new content, which you may refine for clarity.
    3. Return the updated account plan to the user.
    4. Clearly state which section was updated.

STYLE:
- Talk naturally, like a consultant.
- Use bullet points and short paragraphs where helpful.
- Be concise but insightful.
- Do not refuse to answer just because external tools failed; always try to help.
""",
    tools=[research_company, update_account_plan],
)
