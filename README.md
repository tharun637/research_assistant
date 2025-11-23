Project Title: Company Research Assistant – Account Plan Generator (Google ADK Agent)

Overview:

This project implements a conversational AI agent using Google ADK (Agent Developer Kit).
The agent can:

   1.Research companies using multiple sources (Wikipedia & DuckDuckGo)

   2.Detect conflicting information and ask the user whether to dig deeper

   3.Generate a structured Account Plan

   4.Allow users to update selected sections of the plan

   5.Provide natural, interactive conversation flow

This project satisfies all the required features of the assignment:

Conversational AI agent

Multi-source information gathering

Agentic reasoning steps ("conflicting information found…")

Account plan generation

Editing specific sections

Clear architecture and design decisions

Features
1. Company Research Tool (research_company)

Fetches information from:

Wikipedia REST API

DuckDuckGo Instant Answer API

Detects:

Conflicting years

Missing data

Ambiguities in source information

2. Conflict Detection Behavior

If conflicting founding years/dates are found, the agent says:

“I’m finding conflicting information about key dates: 1975, 1980.
Should I dig deeper before finalizing the plan?”

This simulates human-like uncertainty handling and user-directed research.

3. Account Plan Generator

Produces a 7-section structured plan:

## Company Overview
## Key Products and Services
## Industry and Market Position
## Recent News and Strategic Moves
## Key Challenges and Risks
## Opportunities for Our Company
## Recommended Next Steps

4. Section Updater Tool (update_account_plan)

Allows users to update only one section of a generated account plan, without rewriting the entire document.

5. Natural Conversational Flow

The agent responds in a consultant-style tone, explains its reasoning, and interacts clearly with the user.

Architecture
1. Google ADK (Agent Developer Kit)

This agent is built using Google’s ADK, which allows:

Tool-based agent architecture

Function calling

Model-driven reasoning

Easy extensibility

Architecture Diagram
           ┌────────────────────────────┐
           │         User Input         │
           └─────────────┬──────────────┘
                         ▼
              ┌─────────────────────┐
              │      ADK Agent      │
              │ (gemini-2.5-flash)  │
              └──────────┬──────────┘
          ┌──────────────┴──────────────┐
          ▼                               ▼
┌──────────────────┐           ┌──────────────────────────┐
│ research_company │           │  update_account_plan     │
└──────────────────┘           └──────────────────────────┘
          │                               │
          ▼                               ▼
┌──────────────────────┐     ┌───────────────────────────┐
│ Wikipedia API        │     │ Markdown Account Plan     │
│ DuckDuckGo API       │     │ Section Update Logic      │
└──────────────────────┘     └───────────────────────────┘
                         ▼
               ┌──────────────────┐
               │  Final Response  │
               └──────────────────┘
    
#------------------------------------------------------------------#

Setup Instructions
1. Clone / Create Project Folder
company_research_agent/

2. Create Virtual Environment
python -m venv .venv

Activate:

Windows CMD:
.venv\Scripts\activate.bat

3. Install Dependencies

google-adk requests

4. Add API Key via .env

Create .env file in project root:

GOOGLE_API_KEY=YOUR_GEMINI_KEY
GOOGLE_GENAI_USE_VERTEXAI=FALSE

 generated a key from:
 https://aistudio.google.com/app/api-keys

5. Ensure agent.py Exists

Placed the full ADK code inside agent.py.

6. Run the Agent

ADK may not be in PATH, so run it using absolute venv path:

.venv\Scripts\adk.exe run .

 adk web --port 8000 for UI


If ADK is globally recognized:

adk run .

How to Test the Agent
1. Generate an Account Plan

Input:

Create an account plan for Microsoft

Agent will:

Fetch data

Detect conflicts

Ask if it should dig deeper

Generate structured plan

2. Update a Section

Input:

Update the Opportunities for Our Company section to focus on cloud migration and AI services.


Agent updates only that section and returns the modified entire plan.

And it also works fine by Test with multiple people such as:

o The Confused User (unsure what they want)

o The Efficient User (wants quick results)

o The Chatty User (frequently goes off topic)

o The Edge Case Users (goes off topic/provides invalid inputs/submits requests beyond

bot's capabilities)

#----------------------------------------------------------------------------------#

Design Decisions:

1. Used ADK Instead of Direct SDK

ADK provides structured tool-calling

Separates agent reasoning from tool execution

Perfect for assignments requiring “agentic behavior”

2. Wikipedia + DuckDuckGo

Chosen because:

Public APIs

No authentication required

Provide reliable factual summaries

3. Markdown Section Updating

Markdown makes sections easy to parse, update, and regenerate.

4. Conflict Detection Logic

Extracting years using regex allows the agent to identify contradictions naturally:

Improves “intelligence”

Mimics real research ambiguity

5. Gemini Flash Model

Fast

Supports tool-calling

Good for multi-step agentic workflows