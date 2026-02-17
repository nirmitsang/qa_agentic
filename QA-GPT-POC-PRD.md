# QA-GPT LOCAL POC — COMPREHENSIVE PRD
## Complete Specification for Claude-Assisted Implementation

**Document Version:** POC-1.0  
**Based On:** Production PRD v4.1, Design Conversation, Code Structure Planner Appendix  
**Purpose:** Self-contained specification for building the Walking Skeleton POC from scratch  
**Approach:** Give this document to a fresh Claude session. Ask it to break the work into tasks first, then build each task sequentially. Do NOT ask it to generate all code at once.

---

# TABLE OF CONTENTS

1. [Vision & Goals](#1-vision--goals)
2. [What This POC Is and Is Not](#2-what-this-poc-is-and-is-not)
3. [The Full Product Vision (Northstar)](#3-the-full-product-vision-northstar)
4. [POC Architecture Decisions](#4-poc-architecture-decisions)
5. [Complete 12-Stage Pipeline](#5-complete-12-stage-pipeline)
6. [Dual LLM Provider System](#6-dual-llm-provider-system)
7. [Context File System](#7-context-file-system)
8. [Technical Constraints & Versions](#8-technical-constraints--versions)
9. [Complete File Structure](#9-complete-file-structure)
10. [AgentState Specification](#10-agentstate-specification)
11. [Node Specifications](#11-node-specifications)
12. [Agent Prompt Specifications](#12-agent-prompt-specifications)
13. [LangGraph Graph Topology](#13-langgraph-graph-topology)
14. [Streamlit UI Specification](#14-streamlit-ui-specification)
15. [Mock vs Real Substitution Table](#15-mock-vs-real-substitution-table)
16. [Implementation Task Breakdown](#16-implementation-task-breakdown)
17. [V2/V3 Migration Notes](#17-v2v3-migration-notes)

---

# 1. VISION & GOALS

## 1.1 What We Are Building

A local Streamlit application that demonstrates an AI-powered QA workflow:
**Natural language requirement → Requirements Spec → Test Strategy → Gherkin Test Cases → Code Structure Plan → Runnable Test Script**

Every artifact is reviewed by an AI judge before a human sees it. Humans have a mandatory approval gate at each stage. The entire pipeline runs on LangGraph with real conditional routing and real interrupt-based human review.

## 1.2 The Two Use Cases

**Office laptop (AWS Bedrock):** Full production-aligned setup. Uses `boto3` to call AWS Bedrock with Claude 3.5 Sonnet via the EU cross-region inference endpoint.

**Personal laptop (Google Gemini API):** Alternate LLM backend for testing without AWS credentials. Uses the Gemini API via `google-generativeai`. Same graph, same nodes, same prompts — only the LLM client differs.

## 1.3 POC Success Criteria

1. User types a feature description → system produces a runnable test script
2. LangGraph `interrupt()` correctly pauses at all 5 human review gates
3. Judge loops correctly retry failed documents (up to 3 times)
4. Switching between Bedrock and Gemini requires only one environment variable change
5. The codebase mirrors the production file structure so future engineers know exactly where to add production components

---

# 2. WHAT THIS POC IS AND IS NOT

## 2.1 IS

- A real LangGraph `StateGraph` with all 12 stages wired as actual nodes and conditional edges
- Real LLM calls (Bedrock or Gemini — no mocked responses)
- Real judge evaluation loops (not simulated)
- Real LangGraph `interrupt()` for all 5 human review gates
- Framework-agnostic (UI/E2E, API, or unit tests — detected automatically)
- Production-shaped code: every file lives at its final production path, every interface is production-shaped

## 2.2 IS NOT

- Connected to any database (PostgreSQL, Neo4j, Redis, Pinecone)
- Connected to S3, SQS, SNS, Jira, GitHub, or CI systems
- Containerised (no Docker)
- Multi-user or multi-tenant
- Capable of actually executing the generated test scripts (execution node is a stub)

## 2.3 The Core Trade-off

Infrastructure is mocked at the **boundary** (file I/O instead of DB/cloud), never inside the graph. The graph itself is production-accurate. When V2 arrives, only the boundary implementations change — not the graph topology, not the node logic, not the state schema.

---

# 3. THE FULL PRODUCT VISION (NORTHSTAR)

This section describes what the production system eventually becomes. The POC is the skeleton of this system.

## 3.1 Production Architecture

```
AWS Bedrock (Claude 3.5 Sonnet) + LangGraph + Neo4j + PostgreSQL + Pinecone + Redis
FastAPI backend + Streamlit/React frontend
SQS/SNS for async workflows
Docker + ECS + Terraform
Estimated build: 24 weeks, 6-person team
```

## 3.2 The Production Workflow (12 stages, 5 gates)

```
Stage 1:  QA Interaction           — Confidence-based Q&A before any generation
Stage 2:  Requirements Spec Gen    — Markdown requirements specification
Stage 3:  Judge Requirements       — AI evaluates spec (0-100 score)
Gate #1:  Human Review Spec        — MANDATORY human approval
Stage 4:  Strategy Generation      — High-level test strategy with test case table
Stage 5:  Judge Strategy           — AI evaluates strategy
Gate #2:  Human Review Strategy    — MANDATORY human approval
Stage 6:  Test Case Generation     — Gherkin .feature files
Stage 7:  Judge Test Cases         — AI evaluates Gherkin quality
Gate #3:  Human Review Test Cases  — MANDATORY human approval
Stage 8:  Code Structure Planning  — Blueprint for file structure, classes, imports ⭐ NEW
Stage 9:  Judge Code Plan          — AI evaluates structure plan
Gate #4:  Human Review Code Plan   — MANDATORY human approval ⭐ NEW
Stage 10: Test Script Generation   — Runnable test code (follows approved plan STRICTLY)
Stage 11: Judge Code               — AI evaluates script + plan adherence
Gate #5:  Human Review Code        — MANDATORY human approval
Stage 12: Execution & Healing      — Run tests, auto-heal failures (V2+)
```

## 3.3 Key Design Principles from the Northstar

**Document versioning:** Every artifact (spec, strategy, Gherkin, code plan, script) is a versioned document with an approval status. Not just data in state — a traceable artifact.

**Judge loops:** Each judge node evaluates output quality (0–100). FAIL → regenerate with feedback. NEEDS_HUMAN → interrupt immediately. Max 3 retries before forcing human review.

**Human gates are mandatory and use LangGraph interrupt():** Not simulated. The graph actually pauses. The UI reads the interrupt payload and presents a decision interface. The graph resumes only after `graph.update_state()` is called with the human's decision.

**The Code Structure Planner (Stage 8)** is a blueprint agent. It defines WHAT files to create, WHAT classes and methods, WHICH existing utilities to reuse, and HOW to organise everything — before a single line of test code is written. The Scripting Agent (Stage 10) then acts as a "compiler" that follows this blueprint STRICTLY. Deviation from the approved plan is a judge failure.

---

# 4. POC ARCHITECTURE DECISIONS

These are **final decisions made during design**. Do not revisit them.

## 4.1 LangGraph vs Simple Chain

**Decision:** Use real LangGraph `StateGraph`. No simple function chains.

**Reason:** The goal of the POC is to produce northstar-aligned code. The LangGraph graph, AgentState TypedDict, conditional edges, and interrupt mechanism are the hardest things to retrofit later. Build them right once.

## 4.2 State Persistence

**Decision:** `MemorySaver` checkpointer (in-memory). No PostgreSQL in V1.

**Interface:** `get_checkpointer()` function in `src/graph/checkpointer.py` returns `MemorySaver`. In V2, change only this function to return `PostgresSaver`. Nothing else changes.

## 4.3 Team Context

**Decision:** Two local Markdown files loaded at session start. Not a vector database.

- `context_files/tech_context.md` — loaded once per session, injected into every agent call
- `context_files/codebase_map.md` — updated per feature, injected into Code Planner + Scripting nodes

**Interface:** `fetch_context(team_id, component) -> TeamContext` in `src/knowledge/retrieval/context_fetcher.py`. In V2, replace the body with ChromaDB queries. The `TeamContext` return type never changes.

**Critical rule:** `codebase_map.md` must contain actual code snippets, not just filenames. The Code Structure Planner uses this to identify existing utilities to reuse. A filename alone produces hallucinated code.

## 4.4 Document Storage

**Decision:** Document content stored directly in `AgentState`. `DocumentVersion` is a Python dataclass (not SQLAlchemy).

**Interface:** `DocumentVersion` dataclass has all production fields including `storage_url` (None in V1, S3 URL in V2). In V2, map it to SQLAlchemy. Same dataclass, different backend.

## 4.5 Framework Detection

**Decision:** Framework type (ui_e2e / api / unit) is detected by the QA Interaction node via LLM, with a keyword-based fallback from `tech_context.md`. Once set, it flows through all downstream nodes.

## 4.6 Test Scope

**Decision:** Framework-agnostic. The system generates:
- Playwright Python tests for UI/E2E
- pytest + httpx tests for API
- pytest tests for unit

The framework type tag set by QA Interaction drives which patterns the Scripting Agent uses.

---

# 5. COMPLETE 12-STAGE PIPELINE

## Stage 1 — QA Interaction

**Purpose:** Before generating anything, assess whether the raw input is detailed enough. Generate clarifying questions if not.

**Key behaviour:**
- LLM assesses confidence (0.0–1.0 float)
- If confidence >= threshold (default 0.85): proceed automatically
- If confidence < threshold: generate 1–5 targeted questions, pause for answers
- Max 3 question batches then force-proceed regardless of confidence
- Questions are categorised: scope | environment | auth | data | integration | error-handling
- Framework type is detected here and stored in `AgentState.team_context.framework_type`

**Output:** Structured JSON `{ai_confidence, can_proceed, questions: [{id, text, category, is_required}]}`

## Stage 2 — Requirements Spec Generation

**Purpose:** Produce a Markdown requirements specification from raw input + Q&A answers.

**Document sections (mandatory):**
1. Overview
2. Functional Requirements (FR-001, FR-002...)
3. Non-Functional Requirements (NFR-001...)
4. Acceptance Criteria (Given/When/Then per FR)
5. Edge Cases & Boundary Conditions
6. Out of Scope
7. Test Data Requirements
8. Dependencies & Assumptions
9. Risk Assessment (LOW/MEDIUM/HIGH)

## Stage 3 — Judge Requirements

**Evaluation rubric (100 pts):**
- Completeness: 30 pts (all 9 sections, all FRs covered, edge cases explicit)
- Testability: 30 pts (every FR has AC, Given/When/Then format, no vague language)
- Precision: 25 pts (specific error messages/codes, concrete test data, RFC 2119 language)
- Risk & Scope: 15 pts (justified risk level, clear out-of-scope, realistic assumptions)

**Routing:**
- Score >= 80 → Gate #1 (human review)
- Score 60-79 → FAIL → regenerate with feedback
- Score < 60 OR critical issue → NEEDS_HUMAN immediately
- Iteration 3 (final): FAIL → NEEDS_HUMAN (never loop forever)

## Gate #1 — Human Review Spec

**LangGraph interrupt().** User sees: spec document, judge score, judge feedback, specific question if NEEDS_HUMAN.

**User actions:** APPROVE → Strategy | REJECT (with feedback) → Regenerate | EDIT (provide corrected doc) → Strategy

## Stage 4 — Strategy Generation

**Input:** Approved requirements spec + tech context.

**Document sections:**
1. Strategy Overview
2. Test Scope
3. Test Types & Rationale (functional / negative / security / performance / integration / regression)
4. Test Case Summary Table: `| ID | Title | Type | Priority | Requirement | Risk |`
5. Priority Justification (P0=showstopper, P1=important, P2=edge case)
6. Coverage Matrix (FR-XXX → TC_XXX_YYY)
7. Test Environment Requirements
8. Estimated Effort (hours)

**Constraints:** Max 20 test cases. Every FR must have at least one test. Security tests mandatory if auth/sessions/data in scope.

## Stage 5 — Judge Strategy

**Evaluation rubric (100 pts):**
- Coverage Completeness: 35 pts
- Test Case Quality: 30 pts
- Risk & Completeness: 20 pts
- Effort & Environment: 15 pts

Same routing logic as Judge Requirements.

## Gate #2 — Human Review Strategy

Same mechanics as Gate #1.

## Stage 6 — Test Case Generation (Gherkin)

**Purpose:** Generate Gherkin `.feature` files from approved strategy.

**Critical rules:**
- Output must start with `Feature:` (no preamble, no markdown fences)
- Every scenario tagged with `@TC_XXX_001` plus type/priority tags
- Every scenario has Given + When + Then
- Scenario Outline must have Examples table
- Gherkin syntax validated BEFORE judge sees it (using `gherkin-official` parser)
- On syntax failure: immediate retry with error context injected into prompt (internal retry, not a judge loop)

## Stage 7 — Judge Test Cases

**Evaluation rubric (100 pts):**
- Strategy Traceability: 35 pts (every TC_XXX tag present, no missing/extra scenarios)
- Step Quality: 30 pts (correct Given/When/Then semantics, specific and observable)
- Coverage & Tags: 20 pts (all tags present, negative cases, security cases)
- Completeness: 15 pts (Background usage, meaningful test data, feature description)

## Gate #3 — Human Review Test Cases

Same mechanics as Gate #1.

## Stage 8 — Code Structure Planning ⭐ NEW

**Purpose:** Before writing any test code, produce a detailed architectural blueprint that the Scripting Agent will follow STRICTLY. This prevents the agent from making architectural decisions during code generation.

**Input:** Approved Gherkin + `codebase_map.md` (existing utilities, file structure, conventions).

**Output:** A Markdown document containing:
1. **File Structure** — Proposed file tree with `[NEW]` vs `[EXISTING - REUSE]` labels + estimated LOC per file
2. **Page Objects Design** — Full class definitions with method signatures for every new class
3. **Test File Structure** — Which Gherkin scenarios map to which test files
4. **Utility Reuse Strategy** — Table of existing utilities to reuse (from `codebase_map.md`) vs. new ones to create
5. **Import Strategy** — Complete import blocks for each file
6. **Test Data Organisation** — JSON structure of fixture files to create
7. **Naming Conventions** — File names, class names, method names, test case titles
8. **Complexity Estimation** — LOC per file, LOW/MEDIUM/HIGH complexity, implementation order
9. **Validation Checklist** — Self-check list

**In V1 (POC):** Neo4j and Redis are not available. The agent reads `codebase_map.md` as the source for existing utilities and conventions. The prompt must instruct the agent to treat `codebase_map.md` as its source of truth for what exists.

**Critical constraint for the Scripting Agent:** The approved Code Structure Plan is injected as the PRIMARY input to Stage 10. The system prompt for Stage 10 must explicitly state: "Follow this plan STRICTLY. Do not make architectural decisions. If the plan says use `CommonUtils.login()`, use it. Do not create a new login function."

## Stage 9 — Judge Code Plan

**Evaluation rubric (100 pts):**
- Team Convention Alignment: 30 pts (file structure, naming, patterns)
- Utility Reuse: 25 pts (existing utilities used correctly, no duplication)
- File Organisation: 20 pts (logical grouping, no 300+ LOC files)
- Naming Convention Compliance: 15 pts (files, classes, methods)
- Feasibility: 10 pts (complexity estimates reasonable, dependencies available)

**Special routing rule:** Even if score < 70, route to human review (not FAIL loop). The human always sees the code plan. The judge score informs the human but does not block them.

Implementation: route BOTH PASS and FAIL to `human_review_code_plan`. Only route to FAIL loop if critical issues exist (duplicate utilities, violates conventions structurally).

## Gate #4 — Human Review Code Plan ⭐ NEW

**This gate is MANDATORY — there is no auto-proceed path.**

User sees:
- Code Structure Plan document (Markdown)
- Judge score and feedback
- File tree preview (parsed from the plan's file structure section)
- List of files to create vs. reuse

User actions: APPROVE → Scripting | REJECT (with feedback) → Regenerate plan | EDIT (provide corrected plan) → Scripting

## Stage 10 — Test Script Generation (Scripting)

**Input:** Approved Gherkin + Approved Code Structure Plan + `codebase_map.md` + `tech_context.md`

**The plan is PRIMARY.** The scripting agent must:
- Create exactly the files listed in the plan
- Use exactly the class names and method signatures from the plan
- Use exactly the imports specified in the plan
- Reuse exactly the utilities listed in the plan's reuse strategy
- Generate code that passes the plan's own validation checklist

**Output:** A single Python file (or, in V1, the content of the primary test file). In V2 this becomes multi-file output.

## Stage 11 — Judge Code

**Same as before, with one additional check:**
- Plan adherence: Did the generated script follow the approved Code Structure Plan? (New criterion, 15 pts from the existing rubric redistributed)
- Check: Are the imports the same as planned?
- Check: Are the class/method names the same as planned?
- Check: Are existing utilities reused as planned?

## Gate #5 — Human Review Code

Same mechanics as previous code gates.

## Stage 12 — Execution & Healing (STUB in V1)

Stub node that logs "would run pytest here" and returns a mock result. Wired into the graph but not reachable from the main V1 flow (judge code PASS routes to END, not execution).

---

# 6. DUAL LLM PROVIDER SYSTEM

## 6.1 Overview

The system supports two LLM backends selected by an environment variable. The graph, nodes, and prompts are identical regardless of which backend is active.

```
LLM_PROVIDER=bedrock    → AWS Bedrock (office laptop)
LLM_PROVIDER=gemini     → Google Gemini API (personal laptop)
```

## 6.2 Provider Interface Contract

All nodes call a single function:

```python
def call_llm(
    system_prompt: str,
    user_prompt: str,
    trace_name: str,
    trace_id: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> LLMResponse:
    ...
```

```python
@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    trace_name: str
    model_id: str
    latency_ms: int
```

The function internally dispatches to `_call_bedrock()` or `_call_gemini()` based on `settings.llm_provider`. Nodes import only `call_llm` — they are completely unaware of which backend runs.

## 6.3 Bedrock Implementation

**Proven working pattern (do not deviate):**

```python
import boto3, json
from botocore.exceptions import ClientError

client = boto3.client("bedrock-runtime", region_name="eu-west-1")
model_id = "eu.anthropic.claude-3-5-sonnet-20240620-v1:0"

native_request = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 4096,
    "temperature": 0.3,
    "system": system_prompt,
    "messages": [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
}

response = client.invoke_model(modelId=model_id, body=json.dumps(native_request))
model_response = json.loads(response["body"].read())
content_text = model_response["content"][0]["text"]
```

**Key Bedrock details:**
- Region: `eu-west-1`
- Model ID: `eu.anthropic.claude-3-5-sonnet-20240620-v1:0` (EU cross-region inference prefix mandatory)
- `anthropic_version`: `bedrock-2023-05-31`
- Auth: `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` in `.env`
- IAM permission required: `bedrock:InvokeModel`

## 6.4 Gemini Implementation

**Use `google-generativeai` SDK:**

```python
import google.generativeai as genai

genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction=system_prompt,
)
response = model.generate_content(user_prompt)
content_text = response.text
```

**Key Gemini details:**
- Model: `gemini-1.5-pro` (or `gemini-1.5-flash` for lower cost)
- Auth: `GEMINI_API_KEY` in `.env`
- SDK: `google-generativeai` — must be added to `requirements.txt`
- Token counting: use `model.count_tokens()` for usage tracking
- Cost estimate: ~$0.00125/1K input tokens, ~$0.005/1K output tokens for 1.5 Pro

## 6.5 Per-Node Token Budgets

These apply to both backends:

```
qa_interaction:          2048 tokens
requirements_spec_gen:   8192 tokens
judge_requirements:      2048 tokens
strategy:                4096 tokens
judge_strategy:          2048 tokens
test_case_generation:   16384 tokens  (Gherkin can be verbose)
judge_test_cases:        2048 tokens
code_structure_planning: 16384 tokens (detailed blueprint)
judge_code_plan:         2048 tokens
scripting:               8192 tokens
judge_code:              2048 tokens
default:                 4096 tokens
```

## 6.6 Startup Health Check

`verify_llm_connection() -> bool` — makes a minimal test call to whichever backend is active. Called once in the Streamlit sidebar on app load.

---

# 7. CONTEXT FILE SYSTEM

## 7.1 Two-File Model

The user provides two Markdown files that replace the production knowledge layer (Neo4j + Pinecone + Redis):

### `context_files/tech_context.md` (loaded once per session)

Contains:
- Language and framework versions
- Test runner and assertion library
- Project folder structure (relevant parts)
- Coding conventions (naming, import style, async patterns)
- Shared infrastructure (base URLs, auth patterns, fixture patterns)
- What NOT to do (e.g., "don't use `requests`, we use `httpx`")

Injected into: QA Interaction, Requirements Spec, Strategy, Code Structure Planning, Scripting

### `context_files/codebase_map.md` (updated per feature)

Contains:
- The specific source files being tested (with actual code or meaningful summaries)
- Existing related test files (for style matching)
- Shared fixtures and helpers relevant to this feature
- Known edge cases and constraints specific to this component
- Which existing utilities are available and their signatures

Injected into: Code Structure Planning (PRIMARY), Scripting

**Critical rule:** `codebase_map.md` must contain actual code content, not just filenames. The Code Structure Planner uses this to identify what already exists and must not be duplicated.

## 7.2 Context Fetcher Interface

```python
# src/knowledge/retrieval/context_fetcher.py

def fetch_context(
    team_id: str,
    component: str = "",
    tech_context_path: str | None = None,
    codebase_map_path: str | None = None,
) -> TeamContext:
    """
    V1: Reads local .md files.
    V2: Queries ChromaDB.
    V3: Queries Pinecone + Neo4j.
    Return type (TeamContext) never changes.
    """
```

```python
@dataclass
class TeamContext:
    tech_context_md: str        # Full content of tech_context.md
    codebase_map_md: str        # Full content of codebase_map.md
    framework_type: FrameworkType
    conventions_summary: str    # Extracted conventions section
```

## 7.3 Framework Detection

`context_fetcher.py` does a keyword scan of `tech_context.md` to pre-populate `framework_type`. The QA Interaction node's LLM call then confirms or overrides this. Keywords:

- `ui_e2e`: playwright, selenium, cypress, browser, e2e
- `api`: httpx, requests, fastapi, endpoint, rest, openapi
- `unit`: pytest, unittest, mock, patch, fixture

---

# 8. TECHNICAL CONSTRAINTS & VERSIONS

## 8.1 Fixed Package Versions (Office Laptop — Do Not Change)

```
Python:              3.12.7
langgraph:           1.0.7
langgraph-checkpoint: 4.0.0
langgraph-prebuilt:  1.0.7
langgraph-sdk:       0.3.3
langchain-core:      1.2.8
boto3:               1.42.41
pydantic:            2.12.5
pydantic-settings:   2.12.0
pydantic-core:       2.41.5
python-dotenv:       1.0.0
streamlit:           1.54.0
gherkin-official:    36.0.0
```

## 8.2 Additional Packages to Install

```
google-generativeai  # For Gemini backend (personal laptop)
```

No specific version constraint given — use latest stable.

## 8.3 Pydantic v2 Syntax

All Pydantic usage must use v2 syntax:
- `model_config = SettingsConfigDict(...)` not `class Config`
- `BaseSettings` from `pydantic_settings` not `pydantic`
- `@field_validator` not `@validator`

## 8.4 LangGraph 1.0.7 API Notes

- `StateGraph(AgentState)` — TypedDict state
- `graph.add_node(name, function)` — node function signature: `(state: AgentState) -> dict`
- `graph.add_conditional_edges(source, routing_fn, {target_value: node_name})`
- `graph.compile(checkpointer=checkpointer)` — compiled graph
- `graph.stream(input, config={"configurable": {"thread_id": "..."}}, stream_mode="values")`
- `interrupt(payload)` — pauses graph, returns human response when resumed
- `graph.update_state(config, values)` — inject state update (used to feed Q&A answers back)
- `MemorySaver` from `langgraph.checkpoint.memory`

## 8.5 Gherkin Parser API (gherkin-official 36.0.0)

```python
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner
from gherkin.token_matcher import TokenMatcher
from gherkin.errors import ParserError

parser  = Parser()
matcher = TokenMatcher()
scanner = TokenScanner(content)
try:
    doc = parser.parse(scanner, matcher)
    # doc["feature"]["children"] → list of scenarios
except ParserError as e:
    # Syntax error
```

## 8.6 Windows Compatibility

The office laptop runs Windows. Ensure:
- No Unix-only path separators hardcoded — use `pathlib.Path`
- No Unix-only shell commands
- `streamlit run app.py` is run from the project root directory
- `sys.path.insert(0, str(PROJECT_ROOT))` at the top of `app.py` ensures `src/` is importable

---

# 9. COMPLETE FILE STRUCTURE

Every file listed here must exist in V1. Files marked `[STUB]` contain the correct function signature and a `# TODO V2` comment but no real logic. Files marked `[EMPTY]` are `__init__.py` only.

```
qa-gpt/
├── app.py                                      # Streamlit entry point
├── .env.example                                # Environment variable template
├── .env                                        # Not committed — user creates from example
├── requirements.txt                            # Pinned versions
├── README.md                                   # Setup and usage guide
├── context_files/
│   ├── tech_context.md                         # Template — user fills in
│   └── codebase_map.md                         # Template — user fills in per feature
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                         # Pydantic Settings v2 — reads .env
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                            # AgentState TypedDict + all dataclasses/enums
│   │   ├── builder.py                          # StateGraph construction + compile
│   │   ├── checkpointer.py                     # get_checkpointer() → MemorySaver (V1)
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── _judge_base.py                  # Shared judge logic (private)
│   │   │   ├── qa_interaction.py               # Stage 1
│   │   │   ├── requirements_spec_gen.py        # Stage 2
│   │   │   ├── judge_requirements.py           # Stage 3
│   │   │   ├── human_review_spec.py            # Gate 1
│   │   │   ├── strategy.py                     # Stage 4
│   │   │   ├── judge_strategy.py               # Stage 5
│   │   │   ├── human_review_strategy.py        # Gate 2
│   │   │   ├── test_case_generation.py         # Stage 6
│   │   │   ├── judge_test_cases.py             # Stage 7
│   │   │   ├── human_review_test_cases.py      # Gate 3
│   │   │   ├── code_structure_planning.py      # Stage 8 ⭐ NEW
│   │   │   ├── judge_code_plan.py              # Stage 9 ⭐ NEW
│   │   │   ├── human_review_code_plan.py       # Gate 4 ⭐ NEW
│   │   │   ├── scripting.py                    # Stage 10
│   │   │   ├── judge_code.py                   # Stage 11
│   │   │   ├── human_review_code.py            # Gate 5
│   │   │   ├── execution.py                    # Stage 12 [STUB]
│   │   │   ├── healing.py                      # Stage 12 [STUB]
│   │   │   └── reporting.py                    # Stage 12 [STUB]
│   │   └── edges/
│   │       ├── __init__.py
│   │       └── conditional.py                  # All routing functions
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── llm_client.py                       # Unified call_llm() dispatcher (Bedrock + Gemini)
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── qa_interaction_prompt.py
│   │       ├── requirements_spec_prompt.py
│   │       ├── judge_requirements_prompt.py
│   │       ├── strategy_prompt.py
│   │       ├── judge_strategy_prompt.py
│   │       ├── test_case_generation_prompt.py
│   │       ├── judge_test_cases_prompt.py
│   │       ├── code_structure_planner_prompt.py  # ⭐ NEW
│   │       ├── judge_code_plan_prompt.py          # ⭐ NEW
│   │       ├── scripting_prompt.py
│   │       └── judge_code_prompt.py
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── ingestion/
│   │   │   └── __init__.py                     # [EMPTY — V2]
│   │   └── retrieval/
│   │       ├── __init__.py
│   │       └── context_fetcher.py              # fetch_context() — file-based V1
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document_version.py                 # DocumentVersion dataclass (all production fields)
│   │   ├── qa_session.py                       # QASession dataclass
│   │   ├── approval_gate.py                    # ApprovalGate dataclass
│   │   └── audit_log.py                        # [EMPTY — V2]
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py                 # [STUB — V2: DB persistence]
│   │   └── lock_service.py                     # [STUB — V2: Redis locking]
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── neo4j_tools.py                      # [STUB — V2]
│   │   ├── pinecone_tools.py                   # [STUB — V2]
│   │   ├── redis_tools.py                      # [STUB — V2]
│   │   ├── s3_tools.py                         # [STUB — V2]
│   │   ├── github_tools.py                     # [STUB — V2]
│   │   └── linter_tools.py                     # [STUB — V2]
│   ├── db/
│   │   ├── __init__.py
│   │   ├── postgres.py                         # [STUB — V2]
│   │   ├── neo4j.py                            # [STUB — V2]
│   │   └── redis.py                            # [STUB — V2]
│   └── utils/
│       ├── __init__.py
│       └── gherkin_validator.py                # validate_gherkin() + format_errors_for_prompt()
```

---

# 10. AGENTSTATE SPECIFICATION

`AgentState` is a `TypedDict` with `total=False` (all fields optional — nodes use `.get()` with defaults). It is defined in `src/graph/state.py` and is the only object passed between nodes.

## 10.1 Enums

```python
class WorkflowStage(str, Enum):
    QA_INTERACTION            = "qa_interaction"
    REQUIREMENTS_SPEC_GEN     = "requirements_spec_gen"
    JUDGE_REQUIREMENTS        = "judge_requirements"
    HUMAN_REVIEW_SPEC         = "human_review_spec"
    STRATEGY                  = "strategy"
    JUDGE_STRATEGY            = "judge_strategy"
    HUMAN_REVIEW_STRATEGY     = "human_review_strategy"
    TEST_CASE_GENERATION      = "test_case_generation"
    JUDGE_TEST_CASES          = "judge_test_cases"
    HUMAN_REVIEW_TEST_CASES   = "human_review_test_cases"
    CODE_STRUCTURE_PLANNING   = "code_structure_planning"   # NEW
    JUDGE_CODE_PLAN           = "judge_code_plan"           # NEW
    HUMAN_REVIEW_CODE_PLAN    = "human_review_code_plan"    # NEW
    SCRIPTING                 = "scripting"
    JUDGE_CODE                = "judge_code"
    HUMAN_REVIEW_CODE         = "human_review_code"
    EXECUTION                 = "execution"
    HEALING                   = "healing"
    REPORTING                 = "reporting"
    COMPLETED                 = "completed"
    FAILED                    = "failed"

class JudgeResult(str, Enum):
    PASS         = "PASS"
    FAIL         = "FAIL"
    NEEDS_HUMAN  = "NEEDS_HUMAN"

class WorkflowStatus(str, Enum):
    RUNNING          = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED        = "COMPLETED"
    FAILED           = "FAILED"

class FrameworkType(str, Enum):
    UI_E2E  = "ui_e2e"
    API     = "api"
    UNIT    = "unit"
    UNKNOWN = "unknown"
```

## 10.2 Supporting Dataclasses

All defined in `src/graph/state.py`:
- `Question` — id, text, category, is_required
- `QASession` — session_id, batch_number, questions, answers (dict), ai_confidence, status, created_at
- `DocumentVersion` — document_id, workflow_id, document_type, version, content, format, created_by, is_approved, storage_url (None in V1), judge_score, judge_feedback, created_at
- `ApprovalGate` — gate_name, status, reviewer, feedback, document_version, reviewed_at
- `JudgeEvaluation` — score, result (JudgeResult), feedback, issues (list of dicts), recommendations, timestamp
- `TeamContext` — tech_context_md, codebase_map_md, framework_type (FrameworkType), conventions_summary

## 10.3 AgentState Fields

```python
class AgentState(TypedDict, total=False):
    # Identity
    workflow_id: str
    thread_id: str
    team_id: str
    trace_id: str
    workflow_status: WorkflowStatus
    current_stage: WorkflowStage
    error_message: Optional[str]

    # Context
    team_context: TeamContext

    # Input
    raw_input: str

    # Stage 1 — QA Interaction
    qa_sessions: list[QASession]
    qa_confidence: float
    qa_confidence_threshold: float
    qa_completed: bool
    qa_iteration_count: int

    # Stage 2-4 — Requirements
    requirements_spec_content: str
    current_requirements_spec_version: int
    requirements_spec_history: list[DocumentVersion]
    judge_requirements_evaluation: JudgeEvaluation
    requirements_iteration_count: int

    # Stage 4-7 — Strategy
    strategy_content: str
    current_strategy_version: int
    strategy_history: list[DocumentVersion]
    judge_strategy_evaluation: JudgeEvaluation
    strategy_iteration_count: int

    # Stage 6-10 — Gherkin
    gherkin_content: str
    current_test_cases_version: int
    test_cases_history: list[DocumentVersion]
    judge_test_cases_evaluation: JudgeEvaluation
    test_cases_iteration_count: int
    gherkin_validation_passed: bool

    # Stage 8-10 — Code Structure Plan (NEW)
    code_plan_content: str
    current_code_plan_version: int
    code_plan_history: list[DocumentVersion]
    judge_code_plan_evaluation: JudgeEvaluation
    code_plan_iteration_count: int

    # Stage 10-12 — Script
    script_content: str
    script_filename: str
    current_script_version: int
    script_history: list[DocumentVersion]
    judge_code_evaluation: JudgeEvaluation
    script_iteration_count: int

    # Gates
    approval_gates: dict[str, ApprovalGate]   # keys: "spec","strategy","test_cases","code_plan","code"
    human_feedback: Optional[str]

    # V2 stubs
    execution_result: Optional[dict]
    healing_attempts: int
    final_report_content: Optional[str]

    # Cost tracking
    accumulated_cost_usd: float
```

## 10.4 Factory Function

`create_initial_state(raw_input, team_context, team_id, qa_confidence_threshold) -> AgentState`

Initialises all list/dict fields to empty (never None), creates workflow_id/thread_id/trace_id as UUIDs, pre-populates all 5 ApprovalGate entries in `approval_gates`.

---

# 11. NODE SPECIFICATIONS

## 11.1 Node Function Signature

Every node follows this exact pattern:
```python
def <node_name>_node(state: AgentState) -> dict:
    """Reads specific AgentState fields. Returns partial dict."""
```

Nodes never return the full `AgentState`. They return only the keys they modified. LangGraph merges automatically.

## 11.2 Error Handling Pattern (All Nodes)

```python
try:
    response = call_llm(...)
except RuntimeError as e:
    return {
        "workflow_status": WorkflowStatus.FAILED,
        "error_message": str(e),
        "current_stage": WorkflowStage.FAILED,
    }
```

## 11.3 Judge Node Pattern

All judge nodes use a shared `run_judge()` base function in `src/graph/nodes/_judge_base.py`:

```python
def run_judge(
    state, system_prompt, user_prompt, trace_name,
    failure_stage, human_review_stage, pass_stage,
    iteration_count_key, evaluation_key
) -> dict
```

This eliminates duplication across all 5 judge nodes (requirements, strategy, test_cases, code_plan, code).

**Special case for code_plan judge:** The routing is different — even on FAIL, if score < critical threshold, route to human review (not failure loop). The judge score informs the human but doesn't block them.

## 11.4 Human Review Node Pattern

All human review nodes use a shared `_human_review_base()` function in `src/graph/nodes/human_review_spec.py`:

```python
def _human_review_base(
    state, gate_name, document_content_key, document_version_key,
    approve_stage, reject_stage
) -> dict
```

Calls `interrupt(payload)` where payload includes: gate_name, document content, judge score, judge feedback, specific judge question.

After `interrupt()` returns the human response dict `{decision, feedback, edited_content}`:
- APPROVE → approve_stage
- EDIT + content → approve_stage (with edited content stored)
- REJECT → reject_stage (with feedback stored as human_feedback)

## 11.5 Code Structure Planning Node (NEW)

**Reads:** `gherkin_content`, `team_context` (both `tech_context_md` and `codebase_map_md`), `judge_code_plan_evaluation` (on retry), `code_plan_iteration_count`

**Process:**
1. Build prompt using `codebase_map.md` as the source for existing utilities/structure (replaces Neo4j/Redis in V1)
2. Inject judge feedback if this is a retry
3. Call `call_llm()` with `code_structure_planning` trace name (16K token budget, temperature 0.2)
4. Store result as `DocumentVersion` (in-memory)

**Writes:** `code_plan_content`, `current_code_plan_version`, `code_plan_history`, `current_stage → JUDGE_CODE_PLAN`

---

# 12. AGENT PROMPT SPECIFICATIONS

## 12.1 Prompt File Naming Convention

All prompts in `src/agents/prompts/`:
- `{node_name}_prompt.py`
- Each file exports: `{NODE_NAME}_SYSTEM_PROMPT` and `{NODE_NAME}_USER_PROMPT_TEMPLATE`

## 12.2 Universal Prompt Rules

- System prompts define role, task, output format, and quality rules
- User prompt templates use `.format()` string substitution
- All judge prompts request JSON-only output (no markdown fences, no preamble)
- All generative prompts request raw document output (no preamble, no closing remarks)
- All judge prompts include: iteration count, max iterations, is_final_iteration flag
- When `is_final_iteration=True`: judges must return NEEDS_HUMAN instead of FAIL

## 12.3 Code Structure Planner Prompt

**System prompt persona:** Senior Software Architect specialising in test automation architecture. Convention-obsessed, reuse-focused, architectural mindset.

**Key instructions:**
- Treat `codebase_map.md` as ground truth for what already exists in the repo
- Mark every file as `[NEW]` or `[EXISTING - REUSE]`
- For `[EXISTING - REUSE]` files, include the actual file path from `codebase_map.md`
- Include class definitions with method signatures for every new class
- Include complete import blocks for each file
- Include LOC estimates and complexity (LOW/MEDIUM/HIGH) per file
- Include a validation checklist at the end
- The output must be detailed enough that the Scripting Agent can follow it WITHOUT making any architectural decisions

**User prompt template variables:**
- `{gherkin_content}` — approved Gherkin scenarios
- `{tech_context_md}` — full tech_context.md content
- `{codebase_map_md}` — full codebase_map.md content (PRIMARY source for existing utilities)
- `{conventions_summary}` — extracted conventions section
- `{framework_type}` — detected framework
- `{judge_feedback}` — from previous iteration (empty on first attempt)

## 12.4 Judge Code Plan Prompt

**Special scoring rule:** Score >= 70 AND Score < 70 both route to human review. Only critical issues (creates duplicate utilities, violates team conventions fundamentally) trigger a FAIL loop. Document this explicitly in the system prompt.

**Output JSON:**
```json
{
  "score": 0,
  "result": "PASS | FAIL | NEEDS_HUMAN",
  "feedback": "...",
  "validation_checks": {
    "utility_reuse_correct": true,
    "no_duplicate_utilities": true,
    "follows_conventions": true,
    "reasonable_file_sizes": true
  },
  "issues": [{"type":"...", "description":"...", "severity":"...", "affected_file":"..."}],
  "recommendations": [],
  "human_question": null
}
```

## 12.5 Scripting Prompt (Modified for Plan Adherence)

**Added to system prompt:**
```
CRITICAL: You have been given an approved Code Structure Plan.
Follow it STRICTLY. You are a compiler executing a blueprint, not an architect making decisions.
- Create exactly the files listed in the plan
- Use exactly the class names and method signatures from the plan
- Use exactly the imports specified in the plan
- Reuse exactly the utilities listed in the plan's Utility Reuse Strategy
- Do not create any utility, class, or function not in the plan
- If the plan says "Use CommonUtils.login()", use it — do not create a new login function
```

**User prompt template additional variable:** `{code_plan_content}` — the full approved Code Structure Plan

## 12.6 Judge Code Prompt (Modified for Plan Adherence)

**Additional evaluation criterion (15 pts, redistributed from existing rubric):**
Plan adherence:
- Imports match the plan's Import Strategy (5 pts)
- Class/method names match the plan's class definitions (5 pts)
- Existing utilities are reused as specified in the plan (5 pts)

---

# 13. LANGGRAPH GRAPH TOPOLOGY

## 13.1 Node Registration

Register all nodes using `WorkflowStage.value` as the node name (string). This ensures node names and stage values are always in sync.

## 13.2 Edge Map

```
START → qa_interaction

qa_interaction  →[conditional]→
    qa_completed=True  → requirements_spec_gen
    qa_completed=False → qa_interaction  (loop — Streamlit feeds answers back)

requirements_spec_gen → judge_requirements  [direct]

judge_requirements  →[conditional]→
    PASS         → human_review_spec  (NOTE: always goes to human — PASS goes to human)
    FAIL         → requirements_spec_gen
    NEEDS_HUMAN  → human_review_spec

human_review_spec  →[conditional]→
    APPROVE/EDIT → strategy
    REJECT       → requirements_spec_gen

strategy → judge_strategy  [direct]

judge_strategy  →[conditional]→
    PASS         → human_review_strategy
    FAIL         → strategy
    NEEDS_HUMAN  → human_review_strategy

human_review_strategy  →[conditional]→
    APPROVE/EDIT → test_case_generation
    REJECT       → strategy

test_case_generation → judge_test_cases  [direct]

judge_test_cases  →[conditional]→
    PASS         → human_review_test_cases
    FAIL         → test_case_generation
    NEEDS_HUMAN  → human_review_test_cases

human_review_test_cases  →[conditional]→
    APPROVE/EDIT → code_structure_planning
    REJECT       → test_case_generation

code_structure_planning → judge_code_plan  [direct]

judge_code_plan  →[conditional]→
    PASS         → human_review_code_plan   (always goes to human)
    FAIL (minor) → human_review_code_plan   (always goes to human)
    FAIL (critical) → code_structure_planning  (only on critical issues)
    NEEDS_HUMAN  → human_review_code_plan

human_review_code_plan  →[conditional]→
    APPROVE/EDIT → scripting
    REJECT       → code_structure_planning

scripting → judge_code  [direct]

judge_code  →[conditional]→
    PASS         → human_review_code
    FAIL         → scripting
    NEEDS_HUMAN  → human_review_code

human_review_code  →[conditional]→
    APPROVE/EDIT → END
    REJECT       → scripting

# V2 stub chain (wired but not reachable in V1)
execution → reporting  [direct]
healing   → reporting  [direct]
reporting → END
```

## 13.3 Routing Function Pattern

All routing functions in `src/graph/edges/conditional.py` follow this pattern:

```python
def route_after_<node_name>(state: AgentState) -> str:
    stage = state.get("current_stage", WorkflowStage.FAILED)
    return stage.value if isinstance(stage, WorkflowStage) else str(stage)
```

The routing function reads `current_stage` from state (set by the preceding node) and returns its string value. LangGraph uses this to select the next node.

## 13.4 Special Case: judge_code PASS → END

```python
graph.add_conditional_edges(
    "judge_code",
    route_after_judge_code,
    {
        "human_review_code":           "human_review_code",
        "scripting":                   "scripting",
        WorkflowStage.COMPLETED.value: END,
    }
)
```

## 13.5 QA Interaction Loop

The QA Interaction loop is unique: when `qa_completed=False`, the graph routes back to `qa_interaction`. The Streamlit app then calls `graph.update_state(config, {"qa_sessions": updated_sessions})` to inject the user's answers, then calls `graph.stream(None, config=config)` to resume. The node detects the updated answers and re-evaluates confidence.

---

# 14. STREAMLIT UI SPECIFICATION

## 14.1 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ SIDEBAR                                                          │
│  • App title: QA-GPT 🧪                                         │
│  • Bedrock/Gemini connection verify button + status             │
│  • Context file uploaders (tech_context.md, codebase_map.md)   │
│  • Session info: workflow_id, current stage, estimated cost     │
│  • New Session button                                           │
├─────────────────────────────────────────────────────────────────┤
│ PIPELINE PROGRESS BAR (full width)                              │
│  Q&A → Spec → Strategy → Test Cases → Code Plan → Script → Done│
├───────────────────────────┬─────────────────────────────────────┤
│ LEFT COLUMN (2/5 width)   │ RIGHT COLUMN (3/5 width)            │
│                           │                                      │
│ Chat Interface            │ Artifact Tabs                        │
│ • Chat history            │ [📋 Spec] [🗺️ Strategy]             │
│   (scrollable container)  │ [🧩 Test Cases] [📐 Code Plan]      │
│                           │ [💻 Script]                          │
│ Active interaction:       │                                      │
│  (one at a time)          │ Each tab shows:                      │
│  • Q&A form               │ • Document content (markdown/code)   │
│  • Human review gate      │ • Version number                     │
│  • Normal chat input      │ • Judge badge (score + PASS/FAIL)    │
│                           │ • Download button (Script tab)       │
└───────────────────────────┴─────────────────────────────────────┘
```

## 14.2 Artifact Tabs

Five tabs in the right column:
1. **📋 Spec** — `requirements_spec_content` rendered as Markdown
2. **🗺️ Strategy** — `strategy_content` rendered as Markdown
3. **🧩 Test Cases** — `gherkin_content` rendered as `st.code(..., language="gherkin")`
4. **📐 Code Plan** — `code_plan_content` rendered as Markdown ⭐ NEW
5. **💻 Script** — `script_content` rendered as `st.code(..., language="python")` with download button

Each tab shows:
- Version number (caption)
- Judge badge: green success for PASS, orange warning for NEEDS_HUMAN, red error for FAIL
- Judge score

## 14.3 Pipeline Progress Bar

Milestones shown (not every stage):
`Q&A → Spec → Strategy → Test Cases → Code Plan → Script → Done`

Current milestone highlighted in blue. Completed milestones in green. Pending in grey.

## 14.4 Human Review Gate UI

When `st.session_state.awaiting_review` is set, the chat column shows:

```
### 👤 Human Review Required: [Gate Name]
[Judge warning if NEEDS_HUMAN with specific question]
[Info text directing user to check artifact panel]

Decision: ○ APPROVE  ○ REJECT  ○ EDIT
Feedback: [text area]
[If EDIT: large text area pre-populated with current document]

[Submit APPROVE / Submit REJECT / Submit EDIT] (primary button)
```

## 14.5 Q&A Interface

When `st.session_state.awaiting_qa` is set:

```
### 🔍 Clarifying Questions
[Confidence bar: X% (threshold: 85%)]

[st.form with one st.text_area per question]
[Required questions marked with *]

[Submit Answers] (primary button)
```

## 14.6 Session State Keys

```python
st.session_state = {
    "messages":         list[dict],  # [{role, content}]
    "graph_state":      AgentState | None,
    "thread_id":        str | None,
    "workflow_running": bool,
    "awaiting_qa":      bool,
    "awaiting_review":  str | None,  # gate name e.g. "code_plan"
    "bedrock_ok":       bool | None,
    "tech_context_path": str | None,
    "codebase_map_path": str | None,
    "llm_provider":     str,  # "bedrock" or "gemini"
}
```

## 14.7 LLM Provider Toggle

Sidebar shows the active provider (read from `settings.llm_provider`). No in-session switching — changing provider requires `.env` edit and app restart. Display current provider clearly: "🔷 Using: AWS Bedrock" or "🔶 Using: Google Gemini".

---

# 15. MOCK VS REAL SUBSTITUTION TABLE

| Component | V1 (POC) | Production | Change Location |
|---|---|---|---|
| LLM (office) | AWS Bedrock via boto3 | AWS Bedrock via boto3 | No change |
| LLM (personal) | Google Gemini API | Not used in prod | N/A |
| State persistence | MemorySaver (RAM) | PostgresSaver | `checkpointer.py` — one line |
| Team context | Local .md files | Pinecone + Neo4j | `context_fetcher.py` — swap body |
| Document storage | AgentState in RAM | PostgreSQL + S3 | `document_service.py` — implement |
| Document versioning | Int counter in state | DB rows | `document_version.py` → SQLAlchemy |
| Approval gates | State dict | DB rows + API | `approval_gate.py` → SQLAlchemy |
| Gherkin validation | `gherkin-official` local | Same | No change |
| Human review | `interrupt()` in Streamlit | `interrupt()` + FastAPI webhook | `human_review_*.py` — same pattern |
| Execution | Stub | pytest subprocess | `execution.py` — implement TODO |
| Healing | Stub | LLM patch + retry | `healing.py` — implement TODO |
| Observability | Python `logging` | Langfuse tracing | `llm_client.py` — add trace calls |
| Auth | None | JWT | `api/middleware/auth.py` |
| Multi-tenancy | `team_id="local_team"` | Full team model | Multiple files |

---

# 16. IMPLEMENTATION TASK BREAKDOWN

This is the recommended task order for a fresh Claude session. **Ask Claude to complete tasks one at a time, verify each, then proceed.**

## Task 1: Project Scaffold
Create the complete directory structure and all `__init__.py` files. Create `.env.example` and `requirements.txt` with exact versions.

## Task 2: Settings & Config
`src/config/settings.py` — Pydantic Settings v2. Fields: `llm_provider`, `aws_access_key_id`, `aws_secret_access_key`, `aws_default_region`, `bedrock_model_id`, `gemini_api_key`, `gemini_model_id`, `team_id`, `qa_confidence_threshold`, `max_judge_iterations`, `tech_context_path`, `codebase_map_path`, `log_level`.

## Task 3: State Definition
`src/graph/state.py` — All enums, all dataclasses, `AgentState` TypedDict, `create_initial_state()` factory. This is the most important file — everything else depends on it. Include all 5 approval gate keys.

## Task 4: LLM Client
`src/agents/llm_client.py` — `LLMResponse` dataclass, `call_llm()` dispatcher, `_call_bedrock()` implementation (using proven pattern), `_call_gemini()` implementation, `extract_json_from_response()` helper, `verify_llm_connection()`. Per-node token budgets and temperatures as dicts.

## Task 5: Context Fetcher & Gherkin Validator
`src/knowledge/retrieval/context_fetcher.py` — `fetch_context()`, framework keyword detection, conventions extraction, file loading with graceful fallback.
`src/utils/gherkin_validator.py` — `validate_gherkin()`, `GherkinValidationResult`, `format_validation_errors_for_prompt()`.

## Task 6: All Agent Prompts
All 11 prompt files in `src/agents/prompts/`. Build in pipeline order: qa_interaction → requirements_spec → judge_requirements → strategy → judge_strategy → test_case_generation → judge_test_cases → code_structure_planner → judge_code_plan → scripting → judge_code.

## Task 7: Generative Nodes (Stages 1, 2, 4, 6, 8, 10)
`qa_interaction.py`, `requirements_spec_gen.py`, `strategy.py`, `test_case_generation.py`, `code_structure_planning.py`, `scripting.py`. Each node: reads state, builds prompt, calls `call_llm()`, creates `DocumentVersion`, returns partial state dict.

## Task 8: Judge Base + All Judge Nodes
`_judge_base.py` shared function first. Then: `judge_requirements.py`, `judge_strategy.py`, `judge_test_cases.py`, `judge_code_plan.py` (with special routing), `judge_code.py`.

## Task 9: Human Review Base + All Human Review Nodes
`human_review_spec.py` with `_human_review_base()`. Then: `human_review_strategy.py`, `human_review_test_cases.py`, `human_review_code_plan.py`, `human_review_code.py`. All call `interrupt()`.

## Task 10: Stub Nodes
`execution.py`, `healing.py`, `reporting.py` — correct function signatures, log message, `# TODO V2` comment, return minimal state update.

## Task 11: Conditional Edges + Checkpointer
`src/graph/edges/conditional.py` — all routing functions.
`src/graph/checkpointer.py` — `get_checkpointer()` returning `MemorySaver`.

## Task 12: Graph Builder
`src/graph/builder.py` — import all nodes and routing functions, register all nodes, wire all edges (following the topology in Section 13.2), compile with checkpointer. Export `qa_graph` module-level singleton.

## Task 13: Context File Templates
`context_files/tech_context.md` and `context_files/codebase_map.md` — well-commented templates that show users exactly what information to provide.

## Task 14: Streamlit App
`app.py` — full two-column layout, sidebar with provider toggle + connection verify + file upload, pipeline progress bar, artifact tabs (5 tabs including Code Plan), chat interface, Q&A form, human review gate UI for all 5 gates, graph invocation and streaming, session state management.

## Task 15: README
Setup instructions, provider configuration (Bedrock vs Gemini), context file guidance, example prompts, troubleshooting, V2 migration notes.

---

# 17. V2/V3 MIGRATION NOTES

## V2 Changes (Infrastructure plugging)

All changes are boundary swaps — the graph topology does not change:

1. `checkpointer.py`: `MemorySaver` → `PostgresSaver`
2. `context_fetcher.py`: file loading → ChromaDB local → Pinecone + Neo4j
3. `document_service.py`: implement from stub — persist `DocumentVersion` to PostgreSQL + S3
4. `execution.py`: implement from stub — subprocess pytest runner + result parser
5. `healing.py`: implement from stub — LLM failure analysis + script patch + re-execution
6. `llm_client.py`: add Langfuse trace calls around `call_bedrock()` and `call_gemini()`
7. `linter_tools.py`: implement from stub — run pylint/flake8 on generated script before judge sees it

## V3 Changes (Full production)

1. Wrap graph in FastAPI (`src/api/`) with async endpoints
2. SQS/SNS for async workflow triggering
3. Redis for session caching and document locking
4. Neo4j repo ingestion pipeline
5. Docker + ECS + Terraform
6. Multi-tenant team model
7. GitHub/Jira integrations
8. Bedrock Guardrails

## What Never Changes (V1 through V3)

- `state.py` — AgentState schema (only fields added, never removed)
- `builder.py` — graph topology (only nodes added for V2/V3 features)
- Node function signatures — `(state: AgentState) -> dict`
- All system prompts — production-quality from day one
- `call_llm()` interface — nodes always call this single function

---

# APPENDIX A: ENVIRONMENT VARIABLES REFERENCE

```bash
# Provider Selection (REQUIRED)
LLM_PROVIDER=bedrock               # "bedrock" (office) or "gemini" (personal)

# AWS Bedrock (required if LLM_PROVIDER=bedrock)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=eu-west-1
BEDROCK_MODEL_ID=eu.anthropic.claude-3-5-sonnet-20240620-v1:0

# Google Gemini (required if LLM_PROVIDER=gemini)
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_ID=gemini-1.5-pro

# App Configuration
TEAM_ID=local_team
QA_CONFIDENCE_THRESHOLD=0.85       # 0.0-1.0
MAX_JUDGE_ITERATIONS=3

# Context Files (relative to project root)
TECH_CONTEXT_PATH=context_files/tech_context.md
CODEBASE_MAP_PATH=context_files/codebase_map.md

# Logging
LOG_LEVEL=INFO
```

---

# APPENDIX B: EXAMPLE PROMPTS FOR TESTING

Use these to test the full pipeline end-to-end:

**UI/E2E test:**
> "Create tests for a login page with email/password login, Google OAuth, and a Remember Me checkbox. After login, users land on /dashboard. Failed logins show an inline error message. Account lockout after 5 failed attempts."

**API test:**
> "I need API tests for our user registration endpoint POST /api/v1/users. It accepts email, password, first_name, last_name. Returns 201 with user object on success. Returns 409 if email already registered. Returns 422 for validation errors. Auth not required."

**Unit test:**
> "Generate unit tests for a PaymentService.process_payment(amount, currency, card_token) method. It calls a Stripe API client, handles StripeCardError and StripeNetworkError, logs all transactions, and returns a Transaction object."

---

# APPENDIX C: KEY DESIGN DECISIONS SUMMARY (DO NOT REVISIT)

1. **Real LangGraph graph, not function chains.** All nodes, edges, conditional routing, and `interrupt()` calls are real.
2. **Production file structure from day one.** Every file lives at its final production path.
3. **Dual LLM provider via single `call_llm()` function.** Bedrock and Gemini are backend details — nodes don't know which is active.
4. **All 5 human review gates use real `interrupt()`.** The graph actually pauses.
5. **Code Structure Planning (Stage 8) is mandatory.** The Scripting Agent receives the approved plan and follows it STRICTLY.
6. **`AgentState` includes all V2 fields from day one.** Adding fields later is fine. Removing or renaming them after nodes are built is catastrophic.
7. **Judge loops max 3 iterations.** On iteration 3 (is_final_iteration=True), FAIL becomes NEEDS_HUMAN.
8. **Context comes from two .md files, not a vector DB.** Files must contain actual code content, not filenames.
9. **`pydantic_settings` v2 syntax throughout.** `model_config = SettingsConfigDict(...)`, not `class Config`.
10. **LangGraph 1.0.7 API.** Node returns `dict`, not `AgentState`. `stream_mode="values"`.
