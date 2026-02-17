# TASKS.md — QA-GPT POC Implementation Plan

> **Methodology:** Strict Test-Driven Development (TDD). Every task is **small**, **atomic**, and has a **mandatory Verification Step** before the next task begins. Never proceed to the next task if the verification fails.
>
> **Golden Rules:**
> - No task writes code that another unverified task depends on.
> - Stub first, implement second, verify always.
> - Every import must work before it's used.
> - The file structure is sacred — every file lives at its final production path from Day 1.

---

## PHASE 1 — Scaffold & Configuration
> **Goal:** A runnable project skeleton where settings can be loaded from `.env`.

---

### Task 1.1 — Create the Complete Directory Structure

**What to do:**
Create the full production-aligned folder tree from Section 9 of the PRD. Every directory must have an `__init__.py`. Directories marked `[EMPTY]` get only `__init__.py`. No Python logic yet — just the skeleton.

**Directories to create:**
```
qa-gpt/
├── context_files/
├── src/
│   ├── config/
│   ├── graph/
│   │   ├── nodes/
│   │   └── edges/
│   ├── agents/
│   │   └── prompts/
│   ├── knowledge/
│   │   ├── ingestion/
│   │   └── retrieval/
│   ├── models/
│   ├── services/
│   ├── tools/
│   ├── db/
│   └── utils/
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

**Files to create (empty `__init__.py` only):**
Every `__init__.py` in the tree above. Add a one-line comment `# QA-GPT — <module name>` to each.

**Verification Step:**
Create `tests/test_phase1.py` and run it:
```python
# tests/test_phase1.py
import os, pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent

REQUIRED_DIRS = [
    "src/config", "src/graph", "src/graph/nodes", "src/graph/edges",
    "src/agents", "src/agents/prompts", "src/knowledge", "src/knowledge/ingestion",
    "src/knowledge/retrieval", "src/models", "src/services", "src/tools",
    "src/db", "src/utils", "context_files", "tests/unit",
    "tests/integration", "tests/fixtures",
]

REQUIRED_INITS = [
    "src/__init__.py", "src/config/__init__.py", "src/graph/__init__.py",
    "src/graph/nodes/__init__.py", "src/graph/edges/__init__.py",
    "src/agents/__init__.py", "src/agents/prompts/__init__.py",
    "src/knowledge/__init__.py", "src/knowledge/ingestion/__init__.py",
    "src/knowledge/retrieval/__init__.py", "src/models/__init__.py",
    "src/services/__init__.py", "src/tools/__init__.py",
    "src/db/__init__.py", "src/utils/__init__.py",
]

def test_directories_exist():
    for d in REQUIRED_DIRS:
        assert (ROOT / d).is_dir(), f"Missing directory: {d}"

def test_init_files_exist():
    for f in REQUIRED_INITS:
        assert (ROOT / f).is_file(), f"Missing __init__.py: {f}"
```
**Pass condition:** `pytest tests/test_phase1.py` → All tests GREEN.

---

### Task 1.2 — Create `requirements.txt` and `.env.example`

**What to do:**
Create `requirements.txt` with the exact pinned versions from PRD Section 8.1. Create `.env.example` with all variables from Appendix A.

**`requirements.txt` must include:**
```
langgraph==1.0.7
langgraph-checkpoint==4.0.0
langgraph-prebuilt==1.0.7
langgraph-sdk==0.3.3
langchain-core==1.2.8
boto3==1.42.41
pydantic==2.12.5
pydantic-settings==2.12.0
pydantic-core==2.41.5
python-dotenv==1.0.0
streamlit==1.54.0
gherkin-official==36.0.0
google-generativeai  # no pin — latest stable
pytest
pytest-cov
```

**`.env.example` must include** all variables from Appendix A with placeholder values and inline comments explaining each.

**Verification Step:**
```bash
# 1. Create a fresh virtual environment
python -m venv .venv

# 2. Activate and install
# (Windows) .venv\Scripts\activate
# (Unix)    source .venv/bin/activate
pip install -r requirements.txt

# 3. Verify key packages are importable
python -c "import langgraph; import pydantic; import streamlit; import boto3; print('All core packages OK')"

# 4. Verify .env.example exists and has the required keys
python -c "
from pathlib import Path
content = Path('.env.example').read_text()
required_keys = ['LLM_PROVIDER','AWS_ACCESS_KEY_ID','GEMINI_API_KEY','QA_CONFIDENCE_THRESHOLD','MAX_JUDGE_ITERATIONS','TECH_CONTEXT_PATH','CODEBASE_MAP_PATH']
for k in required_keys:
    assert k in content, f'Missing key in .env.example: {k}'
print('.env.example OK')
"
```
**Pass condition:** All packages install without error. All assertions pass.

---

### Task 1.3 — Implement `src/config/settings.py`

**What to do:**
Implement the Pydantic Settings v2 `Settings` class. Must use `SettingsConfigDict` (NOT `class Config`). Must read from `.env` file. All fields from PRD Section 16 Task 2.

**Required fields:**
- `llm_provider: str` — "bedrock" or "gemini"
- `aws_access_key_id: str = ""`
- `aws_secret_access_key: str = ""`
- `aws_default_region: str = "eu-west-1"`
- `bedrock_model_id: str = "eu.anthropic.claude-3-5-sonnet-20240620-v1:0"`
- `gemini_api_key: str = ""`
- `gemini_model_id: str = "gemini-1.5-pro"`
- `team_id: str = "local_team"`
- `qa_confidence_threshold: float = 0.85`
- `max_judge_iterations: int = 3`
- `tech_context_path: str = "context_files/tech_context.md"`
- `codebase_map_path: str = "context_files/codebase_map.md"`
- `log_level: str = "INFO"`

Add a `@field_validator("llm_provider")` that raises `ValueError` if value is not `"bedrock"` or `"gemini"`.

Export a module-level `settings = Settings()` singleton at the bottom.

**Verification Step:**
Create `tests/unit/test_settings.py`:
```python
# tests/unit/test_settings.py
import os, pytest
from unittest.mock import patch

def test_settings_loads_defaults():
    """Settings loads with environment variables."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"}):
        from importlib import reload
        import src.config.settings as settings_module
        reload(settings_module)
        s = settings_module.Settings()
        assert s.llm_provider == "gemini"
        assert s.qa_confidence_threshold == 0.85
        assert s.max_judge_iterations == 3
        assert s.team_id == "local_team"

def test_settings_rejects_invalid_provider():
    """Invalid LLM_PROVIDER raises a clear error."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "openai"}):
        with pytest.raises(Exception):  # pydantic ValidationError
            from src.config.settings import Settings
            Settings()

def test_settings_bedrock_defaults():
    """Bedrock model defaults are correct."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "bedrock"}):
        from src.config.settings import Settings
        s = Settings()
        assert s.bedrock_model_id == "eu.anthropic.claude-3-5-sonnet-20240620-v1:0"
        assert s.aws_default_region == "eu-west-1"
```
**Pass condition:** `pytest tests/unit/test_settings.py -v` → All tests GREEN.

---

## PHASE 2 — Core State & Types
> **Goal:** A complete, importable `state.py` with all enums, dataclasses, and the `AgentState` TypedDict. The graph, every node, and every test depends on this file.

---

### Task 2.1 — Implement All Enums in `src/graph/state.py`

**What to do:**
Create `src/graph/state.py` and implement the four enums from PRD Section 10.1. Start with enums only — no dataclasses yet.

**Enums to implement:**
- `WorkflowStage(str, Enum)` — 19 values (qa_interaction through failed)
- `JudgeResult(str, Enum)` — PASS, FAIL, NEEDS_HUMAN
- `WorkflowStatus(str, Enum)` — RUNNING, WAITING_APPROVAL, COMPLETED, FAILED
- `FrameworkType(str, Enum)` — UI_E2E, API, UNIT, UNKNOWN

**Verification Step:**
```python
# tests/unit/test_state_enums.py
from src.graph.state import WorkflowStage, JudgeResult, WorkflowStatus, FrameworkType

def test_workflow_stage_values():
    assert WorkflowStage.QA_INTERACTION.value == "qa_interaction"
    assert WorkflowStage.CODE_STRUCTURE_PLANNING.value == "code_structure_planning"
    assert WorkflowStage.COMPLETED.value == "completed"
    assert len(WorkflowStage) == 19

def test_judge_result_values():
    assert JudgeResult.PASS.value == "PASS"
    assert JudgeResult.NEEDS_HUMAN.value == "NEEDS_HUMAN"
    assert len(JudgeResult) == 3

def test_framework_type_values():
    assert FrameworkType.UI_E2E.value == "ui_e2e"
    assert FrameworkType.UNKNOWN.value == "unknown"

def test_enums_are_str_subclass():
    """Enums must be str subclasses for LangGraph state serialisation."""
    assert isinstance(WorkflowStage.QA_INTERACTION, str)
    assert isinstance(JudgeResult.PASS, str)
```
**Pass condition:** `pytest tests/unit/test_state_enums.py -v` → All tests GREEN.

---

### Task 2.2 — Implement All Supporting Dataclasses in `src/graph/state.py`

**What to do:**
Add all six dataclasses to `src/graph/state.py` (below the enums). Use `@dataclass` from `dataclasses`. Use `field(default_factory=...)` for mutable defaults. Use `Optional[str] = None` pattern for nullable fields. Import `datetime` for timestamp fields.

**Dataclasses to implement** (exact field names from PRD Section 10.2):
1. `Question` — `id: str`, `text: str`, `category: str`, `is_required: bool = True`
2. `QASession` — `session_id: str`, `batch_number: int`, `questions: list[Question]`, `answers: dict`, `ai_confidence: float`, `status: str`, `created_at: datetime`
3. `DocumentVersion` — `document_id: str`, `workflow_id: str`, `document_type: str`, `version: int`, `content: str`, `format: str`, `created_by: str`, `is_approved: bool = False`, `storage_url: Optional[str] = None`, `judge_score: Optional[float] = None`, `judge_feedback: Optional[str] = None`, `created_at: datetime = field(default_factory=datetime.utcnow)`
4. `ApprovalGate` — `gate_name: str`, `status: str = "pending"`, `reviewer: Optional[str] = None`, `feedback: Optional[str] = None`, `document_version: Optional[DocumentVersion] = None`, `reviewed_at: Optional[datetime] = None`
5. `JudgeEvaluation` — `score: float`, `result: JudgeResult`, `feedback: str`, `issues: list[dict] = field(default_factory=list)`, `recommendations: list[str] = field(default_factory=list)`, `timestamp: datetime = field(default_factory=datetime.utcnow)`
6. `TeamContext` — `tech_context_md: str`, `codebase_map_md: str`, `framework_type: FrameworkType`, `conventions_summary: str`

**Verification Step:**
```python
# tests/unit/test_state_dataclasses.py
from datetime import datetime
from src.graph.state import (
    Question, QASession, DocumentVersion, ApprovalGate,
    JudgeEvaluation, TeamContext, JudgeResult, FrameworkType
)

def test_question_instantiation():
    q = Question(id="Q1", text="What is the auth mechanism?", category="auth")
    assert q.is_required is True

def test_document_version_instantiation():
    dv = DocumentVersion(
        document_id="doc-001", workflow_id="wf-001",
        document_type="requirements_spec", version=1,
        content="# Spec", format="markdown", created_by="system"
    )
    assert dv.is_approved is False
    assert dv.storage_url is None  # V1: always None
    assert isinstance(dv.created_at, datetime)

def test_approval_gate_defaults():
    gate = ApprovalGate(gate_name="spec")
    assert gate.status == "pending"
    assert gate.reviewer is None

def test_judge_evaluation_instantiation():
    ev = JudgeEvaluation(
        score=85.0, result=JudgeResult.PASS, feedback="Good spec."
    )
    assert ev.issues == []
    assert ev.recommendations == []

def test_team_context_instantiation():
    ctx = TeamContext(
        tech_context_md="# Tech", codebase_map_md="# Codebase",
        framework_type=FrameworkType.API, conventions_summary="Use httpx."
    )
    assert ctx.framework_type == FrameworkType.API
```
**Pass condition:** `pytest tests/unit/test_state_dataclasses.py -v` → All tests GREEN.

---

### Task 2.3 — Implement `AgentState` TypedDict and `create_initial_state()` Factory

**What to do:**
Add the `AgentState` TypedDict and `create_initial_state()` factory function to `src/graph/state.py`. This completes the file.

**`AgentState`:** Must be `TypedDict` with `total=False`. Include ALL fields from PRD Section 10.3 exactly. Do not rename, omit, or add extra fields.

**`create_initial_state()`:** Must:
- Accept: `raw_input: str`, `team_context: TeamContext`, `team_id: str`, `qa_confidence_threshold: float`
- Generate UUIDs for `workflow_id`, `thread_id`, `trace_id`
- Set `workflow_status = WorkflowStatus.RUNNING`
- Set `current_stage = WorkflowStage.QA_INTERACTION`
- Initialise all list fields to `[]` (never `None`)
- Initialise all int counters to `0`
- Initialise all float fields to `0.0`
- Pre-populate `approval_gates` dict with 5 `ApprovalGate` entries keyed: `"spec"`, `"strategy"`, `"test_cases"`, `"code_plan"`, `"code"`

**Verification Step:**
```python
# tests/unit/test_state_factory.py
from src.graph.state import (
    create_initial_state, AgentState, WorkflowStatus, WorkflowStage,
    TeamContext, FrameworkType
)

DUMMY_CONTEXT = TeamContext(
    tech_context_md="# Tech Context", codebase_map_md="# Codebase Map",
    framework_type=FrameworkType.API, conventions_summary="Use httpx."
)

def test_create_initial_state_returns_agent_state():
    state = create_initial_state(
        raw_input="Test the login page",
        team_context=DUMMY_CONTEXT,
        team_id="local_team",
        qa_confidence_threshold=0.85
    )
    assert isinstance(state, dict)
    assert state["raw_input"] == "Test the login page"

def test_initial_state_has_uuids():
    state = create_initial_state("input", DUMMY_CONTEXT, "team", 0.85)
    assert len(state["workflow_id"]) > 0
    assert len(state["thread_id"]) > 0

def test_initial_state_list_fields_are_empty_lists():
    state = create_initial_state("input", DUMMY_CONTEXT, "team", 0.85)
    assert state["qa_sessions"] == []
    assert state["requirements_spec_history"] == []
    assert state["code_plan_history"] == []

def test_initial_state_has_all_five_approval_gates():
    state = create_initial_state("input", DUMMY_CONTEXT, "team", 0.85)
    gates = state["approval_gates"]
    assert set(gates.keys()) == {"spec", "strategy", "test_cases", "code_plan", "code"}
    for gate in gates.values():
        assert gate.status == "pending"

def test_initial_state_workflow_status():
    state = create_initial_state("input", DUMMY_CONTEXT, "team", 0.85)
    assert state["workflow_status"] == WorkflowStatus.RUNNING
    assert state["current_stage"] == WorkflowStage.QA_INTERACTION
```
**Pass condition:** `pytest tests/unit/test_state_factory.py -v` → All tests GREEN.

---

## PHASE 3 — Infrastructure Layer
> **Goal:** A working LLM client that can make real calls and a context fetcher that reads `.md` files. These are the two external dependencies the graph relies on.

---

### Task 3.1 — Implement `src/agents/llm_client.py`

**What to do:**
Implement the unified LLM client. This is the most critical infrastructure file.

**Must implement:**
1. `LLMResponse` dataclass — all fields from PRD Section 6.2
2. `TOKEN_BUDGETS` dict — per-node budgets from PRD Section 6.5
3. `_call_bedrock(system_prompt, user_prompt, max_tokens, temperature) -> LLMResponse` — use exact pattern from PRD Section 6.3. Use `eu-west-1` region. Time the call with `time.time()` for `latency_ms`.
4. `_call_gemini(system_prompt, user_prompt, max_tokens, temperature) -> LLMResponse` — use pattern from PRD Section 6.4. Estimate cost using the rates in PRD Section 6.4.
5. `call_llm(system_prompt, user_prompt, trace_name, trace_id, temperature, max_tokens) -> LLMResponse` — dispatches to Bedrock or Gemini based on `settings.llm_provider`. Uses `TOKEN_BUDGETS.get(trace_name, 4096)` for `max_tokens` default.
6. `extract_json_from_response(text: str) -> dict` — strips markdown code fences, parses JSON. Raises `ValueError` if not valid JSON.
7. `verify_llm_connection() -> bool` — sends a minimal "Reply with OK" prompt. Returns `True` if response received, `False` on any exception.

**Error handling:** All `ClientError` (Bedrock) and `Exception` (Gemini) must be caught and re-raised as `RuntimeError(f"LLM call failed: {e}")`.

**Verification Step:**
Create `tests/integration/test_llm_connection.py`:
```python
# tests/integration/test_llm_connection.py
# NOTE: This test makes REAL LLM calls. Requires valid credentials in .env
# Run with: pytest tests/integration/test_llm_connection.py -v -s
import os, pytest
from src.agents.llm_client import call_llm, verify_llm_connection, extract_json_from_response, LLMResponse

@pytest.mark.integration
def test_verify_connection():
    """Verify the active LLM backend responds."""
    result = verify_llm_connection()
    assert result is True, "LLM connection failed — check credentials in .env"

@pytest.mark.integration
def test_call_llm_returns_llm_response():
    """Real LLM call returns a valid LLMResponse."""
    response = call_llm(
        system_prompt="You are a helpful assistant.",
        user_prompt="Reply with exactly: HELLO",
        trace_name="test_ping",
    )
    assert isinstance(response, LLMResponse)
    assert len(response.content) > 0
    assert response.input_tokens > 0
    assert response.latency_ms > 0

def test_extract_json_strips_fences():
    """JSON extraction handles markdown code fences."""
    raw = '```json\n{"score": 85, "result": "PASS"}\n```'
    result = extract_json_from_response(raw)
    assert result["score"] == 85
    assert result["result"] == "PASS"

def test_extract_json_raises_on_invalid():
    """JSON extraction raises ValueError on non-JSON."""
    import pytest
    with pytest.raises(ValueError):
        extract_json_from_response("This is not JSON at all")
```
**Pass condition (unit):** `pytest tests/integration/test_llm_connection.py::test_extract_json_strips_fences tests/integration/test_llm_connection.py::test_extract_json_raises_on_invalid -v` → GREEN (no LLM call needed).
**Pass condition (integration, requires credentials):** `pytest tests/integration/test_llm_connection.py -m integration -v` → GREEN.

---

### Task 3.2 — Implement `src/knowledge/retrieval/context_fetcher.py`

**What to do:**
Implement the file-based context fetcher. This is the V1 replacement for the Neo4j + Pinecone knowledge layer.

**Must implement:**
1. `_detect_framework_type(tech_context_md: str) -> FrameworkType` — keyword scan from PRD Section 7.3. Keywords: ui_e2e (playwright, selenium, cypress, browser, e2e), api (httpx, requests, fastapi, endpoint, rest, openapi), unit (pytest, unittest, mock, patch, fixture). Returns `FrameworkType.UNKNOWN` if no match.
2. `_extract_conventions_summary(tech_context_md: str) -> str` — extract lines from a "conventions" or "coding standards" section. If no such section exists, return the first 500 characters.
3. `fetch_context(team_id, component, tech_context_path, codebase_map_path) -> TeamContext` — reads both `.md` files using `pathlib.Path`. Graceful fallback: if a file does not exist, return an empty string with a warning log (do NOT raise).

**Also create model stubs** at their final production paths (since `TeamContext` is already in `state.py`, these don't need separate model files — but create empty model files):
- `src/models/document_version.py` — `# see src/graph/state.py for V1 implementation`
- `src/models/qa_session.py` — `# see src/graph/state.py for V1 implementation`
- `src/models/approval_gate.py` — `# see src/graph/state.py for V1 implementation`
- `src/models/audit_log.py` — `# TODO V2: AuditLog model for database persistence`

**Verification Step:**
Create `tests/unit/test_context_fetcher.py`:
```python
# tests/unit/test_context_fetcher.py
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from src.knowledge.retrieval.context_fetcher import fetch_context, _detect_framework_type
from src.graph.state import FrameworkType, TeamContext

PLAYWRIGHT_CONTEXT = "We use Playwright for browser automation and e2e testing."
API_CONTEXT = "Our tests use httpx and pytest to call FastAPI REST endpoints."
UNIT_CONTEXT = "Unit tests use pytest with unittest.mock for mocking."

def test_detect_framework_ui_e2e():
    assert _detect_framework_type(PLAYWRIGHT_CONTEXT) == FrameworkType.UI_E2E

def test_detect_framework_api():
    assert _detect_framework_type(API_CONTEXT) == FrameworkType.API

def test_detect_framework_unit():
    assert _detect_framework_type(UNIT_CONTEXT) == FrameworkType.UNIT

def test_detect_framework_unknown():
    assert _detect_framework_type("No keywords here.") == FrameworkType.UNKNOWN

def test_fetch_context_returns_team_context(tmp_path):
    """fetch_context reads files and returns TeamContext."""
    tech = tmp_path / "tech_context.md"
    codebase = tmp_path / "codebase_map.md"
    tech.write_text("# Tech Context\nWe use playwright for e2e testing.")
    codebase.write_text("# Codebase Map\n## Existing Utils\n```python\ndef login(): pass\n```")
    
    result = fetch_context(
        team_id="local_team",
        tech_context_path=str(tech),
        codebase_map_path=str(codebase),
    )
    assert isinstance(result, TeamContext)
    assert "playwright" in result.tech_context_md.lower()
    assert result.framework_type == FrameworkType.UI_E2E
    assert "Codebase Map" in result.codebase_map_md

def test_fetch_context_graceful_fallback_on_missing_file(tmp_path):
    """fetch_context does NOT raise if a file is missing."""
    tech = tmp_path / "tech_context.md"
    tech.write_text("We use playwright.")
    
    result = fetch_context(
        team_id="local_team",
        tech_context_path=str(tech),
        codebase_map_path="/nonexistent/codebase_map.md",  # Missing file
    )
    assert result.codebase_map_md == ""  # Empty string, not an exception
```
**Pass condition:** `pytest tests/unit/test_context_fetcher.py -v` → All tests GREEN.

---

### Task 3.3 — Implement `src/utils/gherkin_validator.py`

**What to do:**
Implement the Gherkin syntax validator using `gherkin-official` 36.0.0. This is used by the test case generation node for an internal retry loop BEFORE the judge sees the output.

**Must implement:**
1. `GherkinValidationResult` dataclass — `is_valid: bool`, `errors: list[str]`, `scenario_count: int`, `feature_title: str`
2. `validate_gherkin(content: str) -> GherkinValidationResult` — uses the exact parser API from PRD Section 8.5. On `ParserError`, return `is_valid=False` with error messages.
3. `format_validation_errors_for_prompt(result: GherkinValidationResult) -> str` — formats errors into a prompt-injectable string: `"The following Gherkin syntax errors were found:\n1. <error>\n..."`

**Verification Step:**
```python
# tests/unit/test_gherkin_validator.py
from src.utils.gherkin_validator import validate_gherkin, format_validation_errors_for_prompt

VALID_GHERKIN = """Feature: User Login
  Scenario: Successful login
    Given the user is on the login page
    When they enter valid credentials
    Then they are redirected to the dashboard
"""

INVALID_GHERKIN = """This is not valid Gherkin at all."""

VALID_OUTLINE = """Feature: Data-driven tests
  Scenario Outline: Login with multiple users
    Given I am on the login page
    When I login as <username>
    Then I see the dashboard
    Examples:
      | username |
      | alice    |
      | bob      |
"""

def test_validate_valid_gherkin():
    result = validate_gherkin(VALID_GHERKIN)
    assert result.is_valid is True
    assert result.errors == []
    assert result.scenario_count >= 1
    assert "User Login" in result.feature_title

def test_validate_invalid_gherkin():
    result = validate_gherkin(INVALID_GHERKIN)
    assert result.is_valid is False
    assert len(result.errors) > 0

def test_format_errors_for_prompt():
    from dataclasses import dataclass
    result = validate_gherkin(INVALID_GHERKIN)
    prompt_text = format_validation_errors_for_prompt(result)
    assert "Gherkin syntax errors" in prompt_text
    assert len(prompt_text) > 0

def test_validate_scenario_outline():
    result = validate_gherkin(VALID_OUTLINE)
    assert result.is_valid is True
```
**Pass condition:** `pytest tests/unit/test_gherkin_validator.py -v` → All tests GREEN.

---

## PHASE 4 — Graph Topology (The Skeleton)
> **Goal:** A fully wired LangGraph `StateGraph` that can execute from START to END using stub nodes. Every node, edge, and routing function must exist at its final production path.

---

### Task 4.1 — Create All Stub Nodes

**What to do:**
Create all 19 node files in `src/graph/nodes/`. Every stub must:
- Have the exact final production function signature: `def <name>_node(state: AgentState) -> dict:`
- Import `AgentState` from `src.graph.state`
- Contain a `logger.info("STUB: <node_name> executing")` call
- Return a minimal valid partial state dict that sets `current_stage` to the NEXT expected stage
- Contain `# TODO: Implement in Phase 6/7/8` comment

**Node files and their stub return values:**

| File | Function | Stub returns `current_stage` |
|---|---|---|
| `qa_interaction.py` | `qa_interaction_node` | `WorkflowStage.REQUIREMENTS_SPEC_GEN`, `qa_completed=True` |
| `requirements_spec_gen.py` | `requirements_spec_gen_node` | `WorkflowStage.JUDGE_REQUIREMENTS`, `requirements_spec_content="STUB SPEC"` |
| `judge_requirements.py` | `judge_requirements_node` | `WorkflowStage.HUMAN_REVIEW_SPEC` |
| `human_review_spec.py` | `human_review_spec_node` | `WorkflowStage.STRATEGY` |
| `strategy.py` | `strategy_node` | `WorkflowStage.JUDGE_STRATEGY`, `strategy_content="STUB STRATEGY"` |
| `judge_strategy.py` | `judge_strategy_node` | `WorkflowStage.HUMAN_REVIEW_STRATEGY` |
| `human_review_strategy.py` | `human_review_strategy_node` | `WorkflowStage.TEST_CASE_GENERATION` |
| `test_case_generation.py` | `test_case_generation_node` | `WorkflowStage.JUDGE_TEST_CASES`, `gherkin_content="STUB GHERKIN"` |
| `judge_test_cases.py` | `judge_test_cases_node` | `WorkflowStage.HUMAN_REVIEW_TEST_CASES` |
| `human_review_test_cases.py` | `human_review_test_cases_node` | `WorkflowStage.CODE_STRUCTURE_PLANNING` |
| `code_structure_planning.py` | `code_structure_planning_node` | `WorkflowStage.JUDGE_CODE_PLAN`, `code_plan_content="STUB PLAN"` |
| `judge_code_plan.py` | `judge_code_plan_node` | `WorkflowStage.HUMAN_REVIEW_CODE_PLAN` |
| `human_review_code_plan.py` | `human_review_code_plan_node` | `WorkflowStage.SCRIPTING` |
| `scripting.py` | `scripting_node` | `WorkflowStage.JUDGE_CODE`, `script_content="STUB SCRIPT"` |
| `judge_code.py` | `judge_code_node` | `WorkflowStage.HUMAN_REVIEW_CODE` |
| `human_review_code.py` | `human_review_code_node` | `WorkflowStage.COMPLETED`, `workflow_status=WorkflowStatus.COMPLETED` |
| `execution.py` | `execution_node` | `WorkflowStage.REPORTING` |
| `healing.py` | `healing_node` | `WorkflowStage.REPORTING` |
| `reporting.py` | `reporting_node` | `WorkflowStage.COMPLETED` |

**Also create** `src/graph/nodes/_judge_base.py` as an empty stub with a `# TODO: implement run_judge() in Phase 7` comment.

**Verification Step:**
```python
# tests/unit/test_stub_nodes.py
import pytest

# Test that all node files are importable and have the correct function
NODE_IMPORTS = [
    ("src.graph.nodes.qa_interaction", "qa_interaction_node"),
    ("src.graph.nodes.requirements_spec_gen", "requirements_spec_gen_node"),
    ("src.graph.nodes.judge_requirements", "judge_requirements_node"),
    ("src.graph.nodes.human_review_spec", "human_review_spec_node"),
    ("src.graph.nodes.strategy", "strategy_node"),
    ("src.graph.nodes.judge_strategy", "judge_strategy_node"),
    ("src.graph.nodes.human_review_strategy", "human_review_strategy_node"),
    ("src.graph.nodes.test_case_generation", "test_case_generation_node"),
    ("src.graph.nodes.judge_test_cases", "judge_test_cases_node"),
    ("src.graph.nodes.human_review_test_cases", "human_review_test_cases_node"),
    ("src.graph.nodes.code_structure_planning", "code_structure_planning_node"),
    ("src.graph.nodes.judge_code_plan", "judge_code_plan_node"),
    ("src.graph.nodes.human_review_code_plan", "human_review_code_plan_node"),
    ("src.graph.nodes.scripting", "scripting_node"),
    ("src.graph.nodes.judge_code", "judge_code_node"),
    ("src.graph.nodes.human_review_code", "human_review_code_node"),
    ("src.graph.nodes.execution", "execution_node"),
    ("src.graph.nodes.healing", "healing_node"),
    ("src.graph.nodes.reporting", "reporting_node"),
]

@pytest.mark.parametrize("module_path,func_name", NODE_IMPORTS)
def test_node_is_importable_and_callable(module_path, func_name):
    import importlib
    module = importlib.import_module(module_path)
    func = getattr(module, func_name)
    assert callable(func), f"{func_name} must be callable"
```
**Pass condition:** `pytest tests/unit/test_stub_nodes.py -v` → All 19 tests GREEN.

---

### Task 4.2 — Implement `src/graph/edges/conditional.py`

**What to do:**
Implement all routing functions. Every routing function follows the exact pattern from PRD Section 13.3: read `current_stage` from state, return its `.value`.

**Routing functions to implement:**
- `route_after_qa_interaction(state) -> str`
- `route_after_judge_requirements(state) -> str`
- `route_after_human_review_spec(state) -> str`
- `route_after_judge_strategy(state) -> str`
- `route_after_human_review_strategy(state) -> str`
- `route_after_judge_test_cases(state) -> str`
- `route_after_human_review_test_cases(state) -> str`
- `route_after_judge_code_plan(state) -> str`
- `route_after_human_review_code_plan(state) -> str`
- `route_after_judge_code(state) -> str`
- `route_after_human_review_code(state) -> str`

All functions use the same body: `return state.get("current_stage", WorkflowStage.FAILED).value if isinstance(state.get("current_stage"), WorkflowStage) else str(state.get("current_stage", WorkflowStage.FAILED))`

**Verification Step:**
```python
# tests/unit/test_conditional_edges.py
from src.graph.edges.conditional import (
    route_after_qa_interaction, route_after_judge_requirements,
    route_after_human_review_code
)
from src.graph.state import WorkflowStage

def test_route_reads_current_stage():
    state = {"current_stage": WorkflowStage.REQUIREMENTS_SPEC_GEN}
    result = route_after_qa_interaction(state)
    assert result == "requirements_spec_gen"

def test_route_returns_failed_on_missing_stage():
    result = route_after_qa_interaction({})
    assert result == "failed"

def test_route_handles_completed():
    state = {"current_stage": WorkflowStage.COMPLETED}
    result = route_after_human_review_code(state)
    assert result == "completed"
```
**Pass condition:** `pytest tests/unit/test_conditional_edges.py -v` → All tests GREEN.

---

### Task 4.3 — Implement `src/graph/checkpointer.py`

**What to do:**
Implement the `get_checkpointer()` factory function. Returns `MemorySaver`. This is the entire file. It exists to make V2 migration a one-line change.
```python
# src/graph/checkpointer.py
from langgraph.checkpoint.memory import MemorySaver

def get_checkpointer():
    """
    V1: Returns in-memory checkpointer.
    V2: Replace body with PostgresSaver(conn_string=settings.db_url).
    """
    return MemorySaver()
```

**Verification Step:**
```python
# tests/unit/test_checkpointer.py
from src.graph.checkpointer import get_checkpointer
from langgraph.checkpoint.memory import MemorySaver

def test_get_checkpointer_returns_memory_saver():
    cp = get_checkpointer()
    assert isinstance(cp, MemorySaver)

def test_get_checkpointer_returns_new_instance():
    cp1 = get_checkpointer()
    cp2 = get_checkpointer()
    assert cp1 is not cp2  # Not a singleton — each call returns fresh
```
**Pass condition:** `pytest tests/unit/test_checkpointer.py -v` → All tests GREEN.

---

### Task 4.4 — Implement `src/graph/builder.py`

**What to do:**
Implement the complete graph topology. Wire every node and every edge from PRD Section 13.2. This is the file that assembles all previous work.

**Must implement:**
1. Import all 19 node functions
2. Import all routing functions from `conditional.py`
3. Build `StateGraph(AgentState)` and `add_node()` for all 19 nodes using `WorkflowStage.value` as the node name
4. Wire all direct edges with `add_edge()`
5. Wire all conditional edges with `add_conditional_edges()` — use exact target maps from PRD Section 13.2
6. Special case: `judge_code` → `{..., WorkflowStage.COMPLETED.value: END}` (PRD Section 13.4)
7. `graph.add_edge(START, WorkflowStage.QA_INTERACTION.value)` for the entry point
8. Compile with `get_checkpointer()`
9. Export `qa_graph` as a module-level compiled graph

**Verification Step:**
```python
# tests/unit/test_graph_builder.py
from src.graph.builder import qa_graph
from src.graph.state import create_initial_state, TeamContext, FrameworkType

DUMMY_CONTEXT = TeamContext(
    tech_context_md="playwright e2e", codebase_map_md="# map",
    framework_type=FrameworkType.UI_E2E, conventions_summary="PEP8"
)

def test_graph_compiles():
    """The graph can be imported and is compiled (not None)."""
    assert qa_graph is not None

def test_graph_has_correct_node_count():
    """Graph has all 19 nodes registered."""
    # Access the underlying graph nodes
    graph_nodes = qa_graph.nodes
    assert len(graph_nodes) >= 19, f"Expected 19+ nodes, got {len(graph_nodes)}"

def test_graph_runs_stub_pipeline_to_completion():
    """
    Critical integration test: run the stub graph from START to COMPLETED.
    Stub human_review nodes skip interrupt() — they just route forward.
    """
    initial_state = create_initial_state(
        raw_input="Test the login feature",
        team_context=DUMMY_CONTEXT,
        team_id="local_team",
        qa_confidence_threshold=0.85,
    )
    config = {"configurable": {"thread_id": initial_state["thread_id"]}}
    
    final_state = None
    for state_snapshot in qa_graph.stream(initial_state, config=config, stream_mode="values"):
        final_state = state_snapshot
    
    assert final_state is not None
    assert final_state.get("workflow_status").value == "COMPLETED"
```
**Pass condition:** `pytest tests/unit/test_graph_builder.py -v` → All tests GREEN. The stub pipeline runs from START to COMPLETED.

---

## PHASE 5 — Agent Prompts
> **Goal:** All 11 prompt files exist, are importable, and have the correct template variable placeholders. No LLM calls needed to verify this phase.

---

### Task 5.1 — `qa_interaction_prompt.py`

**Exports:** `QA_INTERACTION_SYSTEM_PROMPT` (str), `QA_INTERACTION_USER_PROMPT_TEMPLATE` (str).
**System prompt:** Expert QA analyst. Assess confidence (0.0–1.0). Generate questions. Detect framework type. Output JSON only.
**Template variables:** `{raw_input}`, `{tech_context_md}`, `{previous_qa_summary}`, `{batch_number}`, `{max_batches}`, `{confidence_threshold}`.
**JSON output format:** `{"ai_confidence": float, "can_proceed": bool, "framework_type": str, "questions": [{"id": str, "text": str, "category": str, "is_required": bool}]}`.

**Verification:** Import and check template variables are present in template strings.

---

### Task 5.2 — `requirements_spec_prompt.py`

**Exports:** `REQUIREMENTS_SPEC_SYSTEM_PROMPT`, `REQUIREMENTS_SPEC_USER_PROMPT_TEMPLATE`.
**System prompt:** Senior QA Engineer. Produce a Markdown requirements spec with all 9 mandatory sections from PRD Section 5 (Stage 2). Raw document output only — no preamble.
**Template variables:** `{raw_input}`, `{qa_summary}`, `{tech_context_md}`, `{framework_type}`, `{judge_feedback}`, `{iteration}`.

**Verification:** Import and check template variables.

---

### Task 5.3 — `judge_requirements_prompt.py`

**Exports:** `JUDGE_REQUIREMENTS_SYSTEM_PROMPT`, `JUDGE_REQUIREMENTS_USER_PROMPT_TEMPLATE`.
**System prompt:** Impartial QA document judge. Evaluate using rubric from PRD Section 5 (Stage 3): Completeness 30pts, Testability 30pts, Precision 25pts, Risk & Scope 15pts. JSON output only.
**Template variables:** `{requirements_spec_content}`, `{raw_input}`, `{iteration}`, `{max_iterations}`, `{is_final_iteration}`.
**JSON output format:** `{"score": int, "result": "PASS|FAIL|NEEDS_HUMAN", "feedback": str, "issues": [...], "recommendations": [...], "human_question": str|null}`.

**Verification:** Import and check template variables.

---

### Task 5.4 — `strategy_prompt.py`

**Exports:** `STRATEGY_SYSTEM_PROMPT`, `STRATEGY_USER_PROMPT_TEMPLATE`.
**System prompt:** QA Strategy Architect. Produce 8-section test strategy doc per PRD Section 5 (Stage 4). Max 20 test cases. Coverage matrix mandatory.
**Template variables:** `{requirements_spec_content}`, `{tech_context_md}`, `{framework_type}`, `{judge_feedback}`, `{iteration}`.

**Verification:** Import and check template variables.

---

### Task 5.5 — `judge_strategy_prompt.py`

**Exports:** `JUDGE_STRATEGY_SYSTEM_PROMPT`, `JUDGE_STRATEGY_USER_PROMPT_TEMPLATE`.
**System prompt:** Strategy reviewer. Rubric from PRD Section 5 (Stage 5): Coverage 35pts, TC Quality 30pts, Risk 20pts, Effort 15pts. Same JSON output format as judge_requirements.
**Template variables:** `{strategy_content}`, `{requirements_spec_content}`, `{iteration}`, `{max_iterations}`, `{is_final_iteration}`.

**Verification:** Import and check template variables.

---

### Task 5.6 — `test_case_generation_prompt.py`

**Exports:** `TEST_CASE_GENERATION_SYSTEM_PROMPT`, `TEST_CASE_GENERATION_USER_PROMPT_TEMPLATE`.
**System prompt:** Gherkin expert. Rules from PRD Section 5 (Stage 6): start with `Feature:`, every scenario tagged `@TC_XXX_001`, no markdown fences, raw Gherkin output.
**Template variables:** `{strategy_content}`, `{requirements_spec_content}`, `{tech_context_md}`, `{framework_type}`, `{judge_feedback}`, `{gherkin_errors}`, `{iteration}`.

**Verification:** Import and check template variables.

---

### Task 5.7 — `judge_test_cases_prompt.py`

**Exports:** `JUDGE_TEST_CASES_SYSTEM_PROMPT`, `JUDGE_TEST_CASES_USER_PROMPT_TEMPLATE`.
**System prompt:** Gherkin quality judge. Rubric from PRD Section 5 (Stage 7): Traceability 35pts, Step Quality 30pts, Coverage 20pts, Completeness 15pts. Same JSON output format.
**Template variables:** `{gherkin_content}`, `{strategy_content}`, `{iteration}`, `{max_iterations}`, `{is_final_iteration}`.

**Verification:** Import and check template variables.

---

### Task 5.8 — `code_structure_planner_prompt.py`

**Exports:** `CODE_STRUCTURE_PLANNER_SYSTEM_PROMPT`, `CODE_STRUCTURE_PLANNER_USER_PROMPT_TEMPLATE`.
**System prompt:** Senior Software Architect specialising in test automation. Persona from PRD Section 12.3. Key instructions: treat `codebase_map.md` as ground truth, mark every file `[NEW]` vs `[EXISTING - REUSE]`, include class definitions with method signatures, include import blocks, LOC estimates. Output must be detailed enough for the Scripting Agent to follow WITHOUT making architectural decisions.
**Output structure:** 9 sections from PRD Section 5 (Stage 8). Raw Markdown only.
**Template variables:** `{gherkin_content}`, `{tech_context_md}`, `{codebase_map_md}`, `{conventions_summary}`, `{framework_type}`, `{judge_feedback}`, `{iteration}`.

**Verification:** Import and check template variables.

---

### Task 5.9 — `judge_code_plan_prompt.py`

**Exports:** `JUDGE_CODE_PLAN_SYSTEM_PROMPT`, `JUDGE_CODE_PLAN_USER_PROMPT_TEMPLATE`.
**System prompt:** Architecture reviewer with special routing rules from PRD Section 12.4. Rubric: Convention Alignment 30pts, Utility Reuse 25pts, File Organisation 20pts, Naming 15pts, Feasibility 10pts. Explicitly document: "Score >= 70 AND < 70 both route to human — only critical issues (duplicate utilities, fundamental convention violations) trigger FAIL loop."
**JSON output includes** `validation_checks` object from PRD Section 12.4.
**Template variables:** `{code_plan_content}`, `{gherkin_content}`, `{tech_context_md}`, `{codebase_map_md}`, `{iteration}`, `{max_iterations}`, `{is_final_iteration}`.

**Verification:** Import and check template variables.

---

### Task 5.10 — `scripting_prompt.py`

**Exports:** `SCRIPTING_SYSTEM_PROMPT`, `SCRIPTING_USER_PROMPT_TEMPLATE`.
**System prompt:** Contains the critical plan-adherence instructions from PRD Section 12.5 verbatim: "You are a compiler executing a blueprint, not an architect making decisions." Lists all 5 STRICT rules.
**Template variables:** `{gherkin_content}`, `{code_plan_content}`, `{tech_context_md}`, `{codebase_map_md}`, `{framework_type}`, `{judge_feedback}`, `{iteration}`.

**Verification:** Import and check template variables. Specifically verify the word "STRICTLY" appears in `SCRIPTING_SYSTEM_PROMPT`.

---

### Task 5.11 — `judge_code_prompt.py`

**Exports:** `JUDGE_CODE_SYSTEM_PROMPT`, `JUDGE_CODE_USER_PROMPT_TEMPLATE`.
**System prompt:** Code reviewer. Rubric includes plan adherence criterion from PRD Section 12.6 (15pts redistributed from existing rubric). Total must sum to 100pts.
**Template variables:** `{script_content}`, `{code_plan_content}`, `{gherkin_content}`, `{framework_type}`, `{iteration}`, `{max_iterations}`, `{is_final_iteration}`.

**Verification:** Import and check template variables. Verify "plan adherence" or "plan" appears in `JUDGE_CODE_SYSTEM_PROMPT`.

---

### Task 5.12 — Prompt Suite Regression Test

**What to do:**
Create a single test that imports all 11 prompts and validates structural correctness.

**Verification Step:**
```python
# tests/unit/test_all_prompts.py
import pytest

PROMPT_SPECS = [
    ("src.agents.prompts.qa_interaction_prompt", "QA_INTERACTION_SYSTEM_PROMPT", "QA_INTERACTION_USER_PROMPT_TEMPLATE",
     ["{raw_input}", "{tech_context_md}", "{batch_number}"]),
    ("src.agents.prompts.requirements_spec_prompt", "REQUIREMENTS_SPEC_SYSTEM_PROMPT", "REQUIREMENTS_SPEC_USER_PROMPT_TEMPLATE",
     ["{raw_input}", "{judge_feedback}", "{iteration}"]),
    ("src.agents.prompts.judge_requirements_prompt", "JUDGE_REQUIREMENTS_SYSTEM_PROMPT", "JUDGE_REQUIREMENTS_USER_PROMPT_TEMPLATE",
     ["{requirements_spec_content}", "{is_final_iteration}"]),
    ("src.agents.prompts.strategy_prompt", "STRATEGY_SYSTEM_PROMPT", "STRATEGY_USER_PROMPT_TEMPLATE",
     ["{requirements_spec_content}", "{tech_context_md}"]),
    ("src.agents.prompts.judge_strategy_prompt", "JUDGE_STRATEGY_SYSTEM_PROMPT", "JUDGE_STRATEGY_USER_PROMPT_TEMPLATE",
     ["{strategy_content}", "{is_final_iteration}"]),
    ("src.agents.prompts.test_case_generation_prompt", "TEST_CASE_GENERATION_SYSTEM_PROMPT", "TEST_CASE_GENERATION_USER_PROMPT_TEMPLATE",
     ["{strategy_content}", "{gherkin_errors}"]),
    ("src.agents.prompts.judge_test_cases_prompt", "JUDGE_TEST_CASES_SYSTEM_PROMPT", "JUDGE_TEST_CASES_USER_PROMPT_TEMPLATE",
     ["{gherkin_content}", "{is_final_iteration}"]),
    ("src.agents.prompts.code_structure_planner_prompt", "CODE_STRUCTURE_PLANNER_SYSTEM_PROMPT", "CODE_STRUCTURE_PLANNER_USER_PROMPT_TEMPLATE",
     ["{gherkin_content}", "{codebase_map_md}", "{judge_feedback}"]),
    ("src.agents.prompts.judge_code_plan_prompt", "JUDGE_CODE_PLAN_SYSTEM_PROMPT", "JUDGE_CODE_PLAN_USER_PROMPT_TEMPLATE",
     ["{code_plan_content}", "{is_final_iteration}"]),
    ("src.agents.prompts.scripting_prompt", "SCRIPTING_SYSTEM_PROMPT", "SCRIPTING_USER_PROMPT_TEMPLATE",
     ["{code_plan_content}", "{gherkin_content}"]),
    ("src.agents.prompts.judge_code_prompt", "JUDGE_CODE_SYSTEM_PROMPT", "JUDGE_CODE_USER_PROMPT_TEMPLATE",
     ["{script_content}", "{code_plan_content}", "{is_final_iteration}"]),
]

@pytest.mark.parametrize("module_path,sys_name,usr_name,required_vars", PROMPT_SPECS)
def test_prompt_importable_and_has_required_vars(module_path, sys_name, usr_name, required_vars):
    import importlib
    module = importlib.import_module(module_path)
    system_prompt = getattr(module, sys_name)
    user_template = getattr(module, usr_name)
    assert isinstance(system_prompt, str) and len(system_prompt) > 100, f"{sys_name} too short"
    assert isinstance(user_template, str) and len(user_template) > 50, f"{usr_name} too short"
    for var in required_vars:
        assert var in user_template, f"Missing variable {var} in {usr_name}"

def test_scripting_prompt_contains_strict_instruction():
    from src.agents.prompts.scripting_prompt import SCRIPTING_SYSTEM_PROMPT
    assert "STRICTLY" in SCRIPTING_SYSTEM_PROMPT or "strictly" in SCRIPTING_SYSTEM_PROMPT.lower()

def test_judge_code_prompt_mentions_plan():
    from src.agents.prompts.judge_code_prompt import JUDGE_CODE_SYSTEM_PROMPT
    assert "plan" in JUDGE_CODE_SYSTEM_PROMPT.lower()
```
**Pass condition:** `pytest tests/unit/test_all_prompts.py -v` → All 13 tests GREEN.

---

## PHASE 6 — Implement Generative Nodes (One at a Time)
> **Goal:** Replace stub logic in each generative node with real LLM calls, state reads, and state writes. Verify each node in isolation before moving to the next.

---

### Task 6.1 — Implement `qa_interaction_node`

**What to do:**
Replace stub body with real implementation in `src/graph/nodes/qa_interaction.py`.

**Logic:**
1. Read: `raw_input`, `team_context`, `qa_sessions`, `qa_iteration_count`, `qa_confidence_threshold` from state
2. Build user prompt from `QA_INTERACTION_USER_PROMPT_TEMPLATE`
3. Call `call_llm(system_prompt, user_prompt, "qa_interaction")`
4. Parse JSON response with `extract_json_from_response()`
5. Create `QASession` dataclass and append to `qa_sessions`
6. If `can_proceed=True` OR `qa_iteration_count >= 2` (max 3 batches): set `qa_completed=True`, `current_stage=REQUIREMENTS_SPEC_GEN`
7. Else: set `qa_completed=False`, `current_stage=QA_INTERACTION` (loop back — Streamlit feeds answers in)
8. Return partial state dict

**Verification Step:**
```python
# tests/unit/test_qa_interaction_node.py
from unittest.mock import patch, MagicMock
from src.graph.nodes.qa_interaction import qa_interaction_node
from src.graph.state import (
    create_initial_state, TeamContext, FrameworkType,
    WorkflowStage, QASession
)
from src.agents.llm_client import LLMResponse
import json

DUMMY_CONTEXT = TeamContext(
    tech_context_md="playwright e2e", codebase_map_md="",
    framework_type=FrameworkType.UI_E2E, conventions_summary=""
)

MOCK_HIGH_CONFIDENCE = json.dumps({
    "ai_confidence": 0.92, "can_proceed": True,
    "framework_type": "ui_e2e", "questions": []
})

MOCK_LOW_CONFIDENCE = json.dumps({
    "ai_confidence": 0.60, "can_proceed": False,
    "framework_type": "ui_e2e",
    "questions": [{"id": "Q1", "text": "What auth method?", "category": "auth", "is_required": True}]
})

@patch("src.graph.nodes.qa_interaction.call_llm")
def test_qa_interaction_proceeds_on_high_confidence(mock_llm):
    mock_llm.return_value = MagicMock(content=MOCK_HIGH_CONFIDENCE)
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    result = qa_interaction_node(state)
    assert result["qa_completed"] is True
    assert result["current_stage"] == WorkflowStage.REQUIREMENTS_SPEC_GEN

@patch("src.graph.nodes.qa_interaction.call_llm")
def test_qa_interaction_loops_on_low_confidence(mock_llm):
    mock_llm.return_value = MagicMock(content=MOCK_LOW_CONFIDENCE)
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    result = qa_interaction_node(state)
    assert result["qa_completed"] is False
    assert result["current_stage"] == WorkflowStage.QA_INTERACTION
    assert len(result["qa_sessions"]) == 1

@patch("src.graph.nodes.qa_interaction.call_llm")
def test_qa_interaction_force_proceeds_on_max_iterations(mock_llm):
    mock_llm.return_value = MagicMock(content=MOCK_LOW_CONFIDENCE)
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["qa_iteration_count"] = 2  # Already at max
    result = qa_interaction_node(state)
    assert result["qa_completed"] is True  # Force-proceed

@patch("src.graph.nodes.qa_interaction.call_llm")
def test_qa_interaction_handles_llm_failure(mock_llm):
    mock_llm.side_effect = RuntimeError("Bedrock connection failed")
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    result = qa_interaction_node(state)
    assert result["workflow_status"].value == "FAILED"
    assert "error_message" in result
```
**Pass condition:** `pytest tests/unit/test_qa_interaction_node.py -v` → All tests GREEN (no real LLM calls — uses mocks).

---

### Task 6.2 — Implement `requirements_spec_gen_node`

**What to do:**
Implement `src/graph/nodes/requirements_spec_gen.py`.

**Logic:**
1. Read: `raw_input`, `team_context`, `qa_sessions`, `requirements_iteration_count`, `judge_requirements_evaluation` (for retry feedback), `current_requirements_spec_version`
2. Build `qa_summary` string from QA sessions answers
3. Build `judge_feedback` string from evaluation (empty on first attempt)
4. Call `call_llm(...)` with `trace_name="requirements_spec_gen"`
5. Create `DocumentVersion` with `version = current_requirements_spec_version + 1`
6. Append to `requirements_spec_history`
7. Return: `requirements_spec_content`, `current_requirements_spec_version`, `requirements_spec_history`, `requirements_iteration_count + 1`, `current_stage=JUDGE_REQUIREMENTS`

**Verification Step:**
```python
# tests/unit/test_requirements_spec_gen_node.py
from unittest.mock import patch, MagicMock
from src.graph.nodes.requirements_spec_gen import requirements_spec_gen_node
from src.graph.state import (
    create_initial_state, TeamContext, FrameworkType, WorkflowStage, DocumentVersion
)

DUMMY_CONTEXT = TeamContext("tech", "codebase", FrameworkType.API, "use httpx")

@patch("src.graph.nodes.requirements_spec_gen.call_llm")
def test_creates_document_version(mock_llm):
    mock_llm.return_value = MagicMock(content="# Requirements\n## Overview\n...")
    state = create_initial_state("Test API", DUMMY_CONTEXT, "team", 0.85)
    result = requirements_spec_gen_node(state)
    assert result["requirements_spec_content"] == "# Requirements\n## Overview\n..."
    assert result["current_requirements_spec_version"] == 1
    assert len(result["requirements_spec_history"]) == 1
    assert isinstance(result["requirements_spec_history"][0], DocumentVersion)

@patch("src.graph.nodes.requirements_spec_gen.call_llm")
def test_increments_version_on_retry(mock_llm):
    mock_llm.return_value = MagicMock(content="# Requirements v2\n...")
    state = create_initial_state("Test API", DUMMY_CONTEXT, "team", 0.85)
    state["current_requirements_spec_version"] = 1
    result = requirements_spec_gen_node(state)
    assert result["current_requirements_spec_version"] == 2

@patch("src.graph.nodes.requirements_spec_gen.call_llm")
def test_routes_to_judge_requirements(mock_llm):
    mock_llm.return_value = MagicMock(content="# Spec")
    state = create_initial_state("Test API", DUMMY_CONTEXT, "team", 0.85)
    result = requirements_spec_gen_node(state)
    assert result["current_stage"] == WorkflowStage.JUDGE_REQUIREMENTS
```
**Pass condition:** `pytest tests/unit/test_requirements_spec_gen_node.py -v` → All tests GREEN.

---

### Task 6.3 — Implement `strategy_node`

**What to do:**
Implement `src/graph/nodes/strategy.py`. Same pattern as Task 6.2.

**Key differences:** Reads `requirements_spec_content`, `judge_strategy_evaluation` (for retry feedback). Writes to `strategy_content`, `strategy_history`, `current_strategy_version`, `strategy_iteration_count`. Routes to `JUDGE_STRATEGY`.

**Verification Step:**
```python
# tests/unit/test_strategy_node.py
# Same structure as test_requirements_spec_gen_node.py
# Verify: creates DocumentVersion, increments version on retry, routes to JUDGE_STRATEGY
```
**Pass condition:** `pytest tests/unit/test_strategy_node.py -v` → All tests GREEN.

---

### Task 6.4 — Implement `test_case_generation_node`

**What to do:**
Implement `src/graph/nodes/test_case_generation.py`. This node has an **internal Gherkin validation retry loop**.

**Logic (additional to standard pattern):**
1. After receiving LLM response, call `validate_gherkin(content)`
2. If `not result.is_valid` AND internal attempt < 2: rebuild prompt with `gherkin_errors=format_validation_errors_for_prompt(result)` and retry the LLM call
3. Store `gherkin_validation_passed = result.is_valid` in return dict
4. Route to `JUDGE_TEST_CASES`

**Verification Step:**
```python
# tests/unit/test_test_case_generation_node.py
from unittest.mock import patch, MagicMock, call as mock_call
from src.graph.nodes.test_case_generation import test_case_generation_node
from src.graph.state import create_initial_state, TeamContext, FrameworkType, WorkflowStage

VALID_GHERKIN = "Feature: Login\n  Scenario: Success\n    Given I am on the login page\n    When I login\n    Then I see dashboard\n"
DUMMY_CONTEXT = TeamContext("tech", "codebase", FrameworkType.UI_E2E, "")

@patch("src.graph.nodes.test_case_generation.call_llm")
def test_valid_gherkin_passes_through(mock_llm):
    mock_llm.return_value = MagicMock(content=VALID_GHERKIN)
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["strategy_content"] = "# Strategy"
    result = test_case_generation_node(state)
    assert result["gherkin_validation_passed"] is True
    assert result["gherkin_content"] == VALID_GHERKIN
    assert mock_llm.call_count == 1  # No retry needed

@patch("src.graph.nodes.test_case_generation.call_llm")
def test_invalid_gherkin_triggers_internal_retry(mock_llm):
    invalid = "This is not gherkin"
    mock_llm.side_effect = [
        MagicMock(content=invalid),    # First attempt — invalid
        MagicMock(content=VALID_GHERKIN)  # Second attempt — valid
    ]
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["strategy_content"] = "# Strategy"
    result = test_case_generation_node(state)
    assert mock_llm.call_count == 2  # Retry happened
    assert result["gherkin_validation_passed"] is True
```
**Pass condition:** `pytest tests/unit/test_test_case_generation_node.py -v` → All tests GREEN.

---

### Task 6.5 — Implement `code_structure_planning_node`

**What to do:**
Implement `src/graph/nodes/code_structure_planning.py`.

**Key specifics from PRD Section 11.5:**
- Reads BOTH `tech_context_md` AND `codebase_map_md` from `team_context`
- Uses 16K token budget (`max_tokens=16384`) and temperature 0.2
- `trace_name="code_structure_planning"`
- Writes to `code_plan_content`, `code_plan_history`, `current_code_plan_version`, `code_plan_iteration_count`
- Routes to `JUDGE_CODE_PLAN`

**Verification Step:**
```python
# tests/unit/test_code_structure_planning_node.py
# Verify: uses trace_name="code_structure_planning", creates DocumentVersion,
# routes to JUDGE_CODE_PLAN, reads codebase_map_md from team_context
```
**Pass condition:** `pytest tests/unit/test_code_structure_planning_node.py -v` → All tests GREEN.

---

### Task 6.6 — Implement `scripting_node`

**What to do:**
Implement `src/graph/nodes/scripting.py`.

**Key specifics from PRD Sections 10 and 12.5:**
- Reads: `gherkin_content`, `code_plan_content` (PRIMARY — from approved plan), `team_context`, `judge_code_evaluation` (for retry feedback)
- Injects `code_plan_content` as the PRIMARY input to the prompt
- Routes to `JUDGE_CODE`

**Verification Step:**
```python
# tests/unit/test_scripting_node.py
# Verify: code_plan_content is present in the call to call_llm,
# creates DocumentVersion, routes to JUDGE_CODE
```
**Pass condition:** `pytest tests/unit/test_scripting_node.py -v` → All tests GREEN.

---

## PHASE 7 — Implement Judge Nodes
> **Goal:** Replace stub logic in all judge nodes. Build the shared `run_judge()` base first, then implement each judge.

---

### Task 7.1 — Implement `_judge_base.py`

**What to do:**
Implement `src/graph/nodes/_judge_base.py` with the shared `run_judge()` function from PRD Section 11.3.

**`run_judge()` logic:**
1. Accept: `state`, `system_prompt`, `user_prompt`, `trace_name`, `failure_stage`, `human_review_stage`, `pass_stage`, `iteration_count_key`, `evaluation_key`
2. Call `call_llm()` and `extract_json_from_response()`
3. Parse JSON into `JudgeEvaluation` dataclass
4. Apply routing logic: `PASS` → `pass_stage`, `FAIL` → `failure_stage`, `NEEDS_HUMAN` → `human_review_stage`
5. Check `iteration_count >= max_judge_iterations - 1`: if `FAIL`, override to `NEEDS_HUMAN`
6. Return partial state dict with evaluation and `current_stage`

**Verification Step:**
```python
# tests/unit/test_judge_base.py
from unittest.mock import patch, MagicMock
from src.graph.nodes._judge_base import run_judge
from src.graph.state import (
    create_initial_state, TeamContext, FrameworkType,
    WorkflowStage, JudgeResult
)
import json

DUMMY_CONTEXT = TeamContext("tech", "code", FrameworkType.API, "")
PASS_RESPONSE = json.dumps({"score": 85, "result": "PASS", "feedback": "Good", "issues": [], "recommendations": [], "human_question": None})
FAIL_RESPONSE = json.dumps({"score": 55, "result": "FAIL", "feedback": "Needs work", "issues": [], "recommendations": [], "human_question": None})

@patch("src.graph.nodes._judge_base.call_llm")
def test_run_judge_pass_routes_correctly(mock_llm):
    mock_llm.return_value = MagicMock(content=PASS_RESPONSE)
    state = create_initial_state("Test", DUMMY_CONTEXT, "team", 0.85)
    result = run_judge(
        state=state, system_prompt="You are a judge", user_prompt="Evaluate this",
        trace_name="judge_test", failure_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        pass_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        iteration_count_key="requirements_iteration_count",
        evaluation_key="judge_requirements_evaluation"
    )
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC

@patch("src.graph.nodes._judge_base.call_llm")
def test_run_judge_fail_at_max_iterations_escalates_to_human(mock_llm):
    mock_llm.return_value = MagicMock(content=FAIL_RESPONSE)
    state = create_initial_state("Test", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_iteration_count"] = 2  # At max (3 iterations = index 2)
    result = run_judge(
        state=state, system_prompt="", user_prompt="",
        trace_name="judge_test", failure_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        pass_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        iteration_count_key="requirements_iteration_count",
        evaluation_key="judge_requirements_evaluation"
    )
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC  # Escalated, not looped
```
**Pass condition:** `pytest tests/unit/test_judge_base.py -v` → All tests GREEN.

---

### Task 7.2 — Implement `judge_requirements_node`

**What to do:**
Replace stub in `src/graph/nodes/judge_requirements.py`. Calls `run_judge()` with the correct parameters for requirements evaluation. Pass stage is `HUMAN_REVIEW_SPEC` (spec always goes to human, even on PASS — see PRD Section 13.2).

**Verification Step:**
```python
# tests/unit/test_judge_requirements_node.py
# Verify: PASS routes to HUMAN_REVIEW_SPEC, FAIL routes to REQUIREMENTS_SPEC_GEN,
# JudgeEvaluation stored in state["judge_requirements_evaluation"]
```
**Pass condition:** `pytest tests/unit/test_judge_requirements_node.py -v` → All tests GREEN.

---

### Task 7.3 — Implement `judge_strategy_node`

**What to do:**
Same pattern as Task 7.2. Pass stage → `HUMAN_REVIEW_STRATEGY`. Fail stage → `STRATEGY`.

**Verification Step:** Same structure as Task 7.2. **Pass condition:** All tests GREEN.

---

### Task 7.4 — Implement `judge_test_cases_node`

**What to do:**
Same pattern. Pass stage → `HUMAN_REVIEW_TEST_CASES`. Fail stage → `TEST_CASE_GENERATION`.

**Verification Step:** Same structure. **Pass condition:** All tests GREEN.

---

### Task 7.5 — Implement `judge_code_plan_node` (Special Routing)

**What to do:**
This node has **special routing** from PRD Section 9 and 13.2. Cannot use `run_judge()` directly for the routing decision.

**Special routing logic:**
- `PASS` → `HUMAN_REVIEW_CODE_PLAN` (always)
- `FAIL` with `validation_checks.no_duplicate_utilities=False` OR `validation_checks.follows_conventions=False` → `CODE_STRUCTURE_PLANNING` (critical issues)
- `FAIL` (minor issues, score 50-70) → `HUMAN_REVIEW_CODE_PLAN` (inform human, don't loop)
- `NEEDS_HUMAN` → `HUMAN_REVIEW_CODE_PLAN`

**Verification Step:**
```python
# tests/unit/test_judge_code_plan_node.py
# Must test the critical/minor distinction in FAIL routing.
# Critical FAIL (duplicate utilities) → CODE_STRUCTURE_PLANNING
# Minor FAIL (score 60, no critical flags) → HUMAN_REVIEW_CODE_PLAN
```
**Pass condition:** `pytest tests/unit/test_judge_code_plan_node.py -v` → All tests GREEN.

---

### Task 7.6 — Implement `judge_code_node`

**What to do:**
Same pattern. Pass stage → `HUMAN_REVIEW_CODE`. Fail stage → `SCRIPTING`. Verify plan-adherence evaluation is part of score.

**Verification Step:** `pytest tests/unit/test_judge_code_node.py -v` → All tests GREEN.

---

## PHASE 8 — Implement Human Review Nodes
> **Goal:** All 5 human review gates use real `interrupt()`. The stub `human_review_*` nodes get replaced with implementations that actually pause the graph.

---

### Task 8.1 — Implement `_human_review_base()` and `human_review_spec_node` (Gate #1)

**What to do:**
Implement `src/graph/nodes/human_review_spec.py` including the shared `_human_review_base()` function from PRD Section 11.4.

**`_human_review_base()` logic:**
1. Build interrupt payload dict: `{gate_name, document_content, judge_score, judge_feedback, human_question}`
2. Call `human_response = interrupt(payload)` — graph pauses here
3. Parse `human_response["decision"]`: `"APPROVE"`, `"REJECT"`, or `"EDIT"`
4. `APPROVE`: set `approval_gates[gate_name].status="approved"`, `current_stage=approve_stage`
5. `EDIT`: store `human_response["edited_content"]` as the new document content, `current_stage=approve_stage`
6. `REJECT`: store `human_response["feedback"]` in `human_feedback`, `current_stage=reject_stage`
7. Return partial state dict

**Verification Step:**
```python
# tests/unit/test_human_review_spec_node.py
# NOTE: Testing interrupt() requires using the graph's interrupt mechanism.
# We test the routing logic by mocking interrupt().
from unittest.mock import patch, MagicMock
from src.graph.nodes.human_review_spec import human_review_spec_node
from src.graph.state import (
    create_initial_state, TeamContext, FrameworkType, WorkflowStage
)

DUMMY_CONTEXT = TeamContext("tech", "code", FrameworkType.API, "")

@patch("src.graph.nodes.human_review_spec.interrupt")
def test_approve_routes_to_strategy(mock_interrupt):
    mock_interrupt.return_value = {"decision": "APPROVE", "feedback": ""}
    state = create_initial_state("Test", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Spec"
    result = human_review_spec_node(state)
    assert result["current_stage"] == WorkflowStage.STRATEGY
    assert result["approval_gates"]["spec"].status == "approved"

@patch("src.graph.nodes.human_review_spec.interrupt")
def test_reject_routes_to_regenerate(mock_interrupt):
    mock_interrupt.return_value = {"decision": "REJECT", "feedback": "Missing edge cases."}
    state = create_initial_state("Test", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Spec"
    result = human_review_spec_node(state)
    assert result["current_stage"] == WorkflowStage.REQUIREMENTS_SPEC_GEN
    assert result["human_feedback"] == "Missing edge cases."

@patch("src.graph.nodes.human_review_spec.interrupt")
def test_edit_applies_content_and_routes_forward(mock_interrupt):
    mock_interrupt.return_value = {
        "decision": "EDIT", "edited_content": "# Improved Spec", "feedback": ""
    }
    state = create_initial_state("Test", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Spec"
    result = human_review_spec_node(state)
    assert result["current_stage"] == WorkflowStage.STRATEGY
    assert result["requirements_spec_content"] == "# Improved Spec"
```
**Pass condition:** `pytest tests/unit/test_human_review_spec_node.py -v` → All tests GREEN.

---

### Task 8.2 — Implement `human_review_strategy_node` (Gate #2)

Uses `_human_review_base()`. Approve stage → `TEST_CASE_GENERATION`. Reject stage → `STRATEGY`. Gate key: `"strategy"`.

**Verification Step:** `pytest tests/unit/test_human_review_strategy_node.py -v` → All tests GREEN.

---

### Task 8.3 — Implement `human_review_test_cases_node` (Gate #3)

Approve stage → `CODE_STRUCTURE_PLANNING`. Reject stage → `TEST_CASE_GENERATION`. Gate key: `"test_cases"`.

**Verification Step:** `pytest tests/unit/test_human_review_test_cases_node.py -v` → All tests GREEN.

---

### Task 8.4 — Implement `human_review_code_plan_node` (Gate #4)

**Note from PRD:** This gate is MANDATORY — there is no auto-proceed path. Approve stage → `SCRIPTING`. Reject stage → `CODE_STRUCTURE_PLANNING`. Gate key: `"code_plan"`. Interrupt payload must include the file tree parsed from the plan's file structure section.

**Verification Step:** `pytest tests/unit/test_human_review_code_plan_node.py -v` → All tests GREEN.

---

### Task 8.5 — Implement `human_review_code_node` (Gate #5)

Approve stage → `COMPLETED` (sets `workflow_status=WorkflowStatus.COMPLETED`). Reject stage → `SCRIPTING`. Gate key: `"code"`.

**Verification Step:** `pytest tests/unit/test_human_review_code_node.py -v` → All tests GREEN.

---

## PHASE 9 — V2 Infrastructure Stubs
> **Goal:** All V2 files exist at their production paths with correct signatures and `# TODO V2` comments. No logic, but importable and correctly typed.

---

### Task 9.1 — Implement Execution, Healing, and Reporting Stubs

**What to do:** Give `execution.py`, `healing.py`, and `reporting.py` real signatures and meaningful stub bodies (not empty).

- `execution_node`: log "STUB: Would run pytest here. V2 will execute the test script and parse results.", return `{"execution_result": {"status": "stub", "passed": 0, "failed": 0}, "current_stage": WorkflowStage.REPORTING}`
- `healing_node`: log "STUB: Would analyse failures and patch script. V2 implementation.", return `{"current_stage": WorkflowStage.REPORTING}`
- `reporting_node`: log "STUB: Would generate final HTML report. V2 implementation.", return `{"final_report_content": None, "current_stage": WorkflowStage.COMPLETED, "workflow_status": WorkflowStatus.COMPLETED}`

**Verification Step:**
```python
# tests/unit/test_stub_v2_nodes.py
from src.graph.nodes.execution import execution_node
from src.graph.nodes.healing import healing_node
from src.graph.nodes.reporting import reporting_node
from src.graph.state import WorkflowStage

def test_execution_stub_returns_correct_stage():
    result = execution_node({})
    assert result["current_stage"] == WorkflowStage.REPORTING
    assert "execution_result" in result

def test_healing_stub_returns_correct_stage():
    result = healing_node({})
    assert result["current_stage"] == WorkflowStage.REPORTING

def test_reporting_stub_returns_completed():
    result = reporting_node({})
    assert result["current_stage"] == WorkflowStage.COMPLETED
```
**Pass condition:** `pytest tests/unit/test_stub_v2_nodes.py -v` → All tests GREEN.

---

### Task 9.2 — Create All Remaining V2 Infrastructure Stubs

**What to do:** Create these files with correct function signatures and `# TODO V2` comments. No logic needed — just importable.

- `src/services/document_service.py` — `save_document(doc: DocumentVersion) -> None`
- `src/services/lock_service.py` — `acquire_lock(resource_id: str) -> bool`
- `src/tools/neo4j_tools.py` — `query_graph(query: str) -> list[dict]`
- `src/tools/pinecone_tools.py` — `similarity_search(query: str, top_k: int) -> list[dict]`
- `src/tools/redis_tools.py` — `cache_get(key: str) -> str | None`, `cache_set(key: str, value: str) -> None`
- `src/tools/s3_tools.py` — `upload_file(content: str, key: str) -> str`
- `src/tools/github_tools.py` — `create_pr(title: str, body: str) -> str`
- `src/tools/linter_tools.py` — `lint_python(code: str) -> list[str]`
- `src/db/postgres.py` — `get_db_connection()`
- `src/db/neo4j.py` — `get_neo4j_driver()`
- `src/db/redis.py` — `get_redis_client()`

**Verification Step:**
```bash
# All stubs must be importable without error
python -c "
from src.services.document_service import save_document
from src.services.lock_service import acquire_lock
from src.tools.neo4j_tools import query_graph
from src.tools.pinecone_tools import similarity_search
from src.tools.redis_tools import cache_get, cache_set
from src.tools.s3_tools import upload_file
from src.tools.github_tools import create_pr
from src.tools.linter_tools import lint_python
from src.db.postgres import get_db_connection
from src.db.neo4j import get_neo4j_driver
from src.db.redis import get_redis_client
print('All V2 stubs importable — OK')
"
```
**Pass condition:** No `ImportError`. All stubs importable.

---

## PHASE 10 — Context File Templates
> **Goal:** The `context_files/` directory has production-quality templates that guide users on what to provide, and the context fetcher can load them correctly.

---

### Task 10.1 — Create `context_files/tech_context.md` Template

**What to do:**
Create a well-structured Markdown template with clear instructions in comments. Must include these sections (well-commented):
1. Language & Runtime Versions
2. Test Framework & Libraries
3. Project Folder Structure
4. Coding Conventions (naming, imports, async patterns)
5. Shared Infrastructure (base URLs, auth patterns, fixture patterns)
6. DO NOT Use (anti-patterns)

Each section must have `<!-- FILL IN: instruction -->` comments.

**Verification Step:**
```python
# tests/unit/test_context_file_templates.py
from src.knowledge.retrieval.context_fetcher import fetch_context

def test_tech_context_template_is_loadable():
    """The template file can be loaded by fetch_context without error."""
    result = fetch_context(
        team_id="local_team",
        tech_context_path="context_files/tech_context.md",
        codebase_map_path="context_files/codebase_map.md",
    )
    assert len(result.tech_context_md) > 100  # Has actual content, not just empty
    assert len(result.codebase_map_md) > 100

def test_context_files_have_expected_sections():
    from pathlib import Path
    tech = Path("context_files/tech_context.md").read_text()
    codebase = Path("context_files/codebase_map.md").read_text()
    assert "convention" in tech.lower() or "Convention" in tech
    assert "existing" in codebase.lower() or "EXISTING" in codebase
```
**Pass condition:** `pytest tests/unit/test_context_file_templates.py -v` → All tests GREEN.

---

### Task 10.2 — Create `context_files/codebase_map.md` Template

**What to do:**
Create a template with these sections (well-commented with `<!-- FILL IN -->` guides):
1. Source Files Being Tested (with sample code block showing required format)
2. Existing Test Files (for style matching)
3. Shared Fixtures & Helpers (with actual signatures)
4. Known Edge Cases & Constraints
5. Available Utilities (table: Name | File Path | Signature | Description)

**Critical note in the template:** "⚠️ This file MUST contain actual code snippets, not just filenames. The Code Structure Planner uses this to identify what already exists."

**Verification Step:** Included in Task 10.1 test — same file, same test. **Pass condition:** Task 10.1 test still GREEN after this file is created.

---

## PHASE 11 — End-to-End Integration Test
> **Goal:** A single full pipeline integration test that proves the graph works with real LLM calls, from initial input through the first interrupt gate.

---

### Task 11.1 — Create Full Pipeline Integration Test

**What to do:**
Create `tests/integration/test_full_pipeline.py`. This test uses REAL LLM calls and tests the graph up to the first `interrupt()`.

**Test flow:**
1. Load settings, fetch context from templates
2. Call `create_initial_state()`
3. Call `qa_graph.stream()` — the graph should proceed through QA Interaction, Requirements Spec Gen, Judge Requirements, and then hit `interrupt()` at Human Review Spec (Gate #1)
4. Catch the `GraphInterrupt` exception and assert the payload has the correct structure

**Verification Step:**
```python
# tests/integration/test_full_pipeline.py
# Run with: pytest tests/integration/test_full_pipeline.py -m integration -v -s
import pytest
from src.graph.builder import qa_graph
from src.graph.state import create_initial_state, WorkflowStage, WorkflowStatus
from src.knowledge.retrieval.context_fetcher import fetch_context
from src.config.settings import settings

@pytest.mark.integration
def test_pipeline_reaches_first_gate():
    """
    Full pipeline test: START → QA Interaction → Spec Gen → Judge → Gate #1 interrupt.
    Requires real LLM credentials in .env.
    """
    team_context = fetch_context(team_id=settings.team_id)
    initial_state = create_initial_state(
        raw_input="Create API tests for POST /api/v1/login. Returns 200 with JWT on success, 401 on wrong credentials, 422 on missing fields.",
        team_context=team_context,
        team_id=settings.team_id,
        qa_confidence_threshold=settings.qa_confidence_threshold,
    )
    config = {"configurable": {"thread_id": initial_state["thread_id"]}}
    
    final_state = None
    try:
        for state_snapshot in qa_graph.stream(initial_state, config=config, stream_mode="values"):
            final_state = state_snapshot
            print(f"Stage: {state_snapshot.get('current_stage')}")
    except Exception as e:
        # LangGraph raises GraphInterrupt when interrupt() is called
        if "GraphInterrupt" in type(e).__name__ or "interrupt" in str(e).lower():
            pytest.skip(f"Graph correctly interrupted at gate (expected): {e}")
        raise

    # If we reach here without interrupt, verify the state is coherent
    assert final_state is not None
    assert "requirements_spec_content" in final_state
    assert len(final_state.get("requirements_spec_content", "")) > 100

@pytest.mark.integration
def test_initial_state_flows_into_graph():
    """Minimal smoke test: graph accepts initial state without crashing."""
    team_context = fetch_context(team_id="local_team")
    initial_state = create_initial_state(
        raw_input="Test the user login feature.",
        team_context=team_context,
        team_id="local_team",
        qa_confidence_threshold=0.85,
    )
    assert initial_state["workflow_id"] is not None
    assert initial_state["qa_sessions"] == []
    assert len(initial_state["approval_gates"]) == 5
```
**Pass condition (unit, no LLM):** State creation assertions pass. **Pass condition (integration):** `pytest tests/integration/test_full_pipeline.py -m integration -v -s` → Graph executes at least 2 stages without error before interrupt.

---

## PHASE 12 — Streamlit UI
> **Goal:** A working Streamlit application matching the two-column layout from PRD Section 14. Build incrementally — one component at a time.

---

### Task 12.1 — Create `app.py` Shell + Session State Initialisation

**What to do:**
Create `app.py` with:
- `sys.path.insert(0, str(PROJECT_ROOT))` at the top (Windows compatibility, PRD Section 8.6)
- `st.set_page_config(page_title="QA-GPT 🧪", layout="wide")`
- `_init_session_state()` function that sets all 8 session state keys from PRD Section 14.6 if not already set
- Call `_init_session_state()` on every run

**Session state keys to initialise:**
```python
{"messages": [], "graph_state": None, "thread_id": None,
 "workflow_running": False, "awaiting_qa": False,
 "awaiting_review": None, "bedrock_ok": None,
 "tech_context_path": settings.tech_context_path,
 "codebase_map_path": settings.codebase_map_path,
 "llm_provider": settings.llm_provider}
```

**Verification Step:**
```bash
streamlit run app.py --server.headless true &
sleep 3
curl -s http://localhost:8501 | grep -q "QA-GPT" && echo "App running OK" || echo "App failed"
pkill -f "streamlit run app.py"
```
**Pass condition:** App starts without import errors. Page title contains "QA-GPT".

---

### Task 12.2 — Implement the Sidebar

**What to do:**
Implement `_render_sidebar()` function called within `with st.sidebar:` block.

**Sidebar components (from PRD Section 14.1 and 14.7):**
1. App title: `st.title("QA-GPT 🧪")`
2. Provider display: `st.info("🔷 Using: AWS Bedrock")` or `st.info("🔶 Using: Google Gemini")`
3. `[Verify Connection]` button → calls `verify_llm_connection()` → shows `st.success` or `st.error`
4. `[Upload tech_context.md]` file uploader → saves to `st.session_state.tech_context_path`
5. `[Upload codebase_map.md]` file uploader → saves to `st.session_state.codebase_map_path`
6. Session info: `st.caption(f"Workflow: {workflow_id}")`, current stage, estimated cost
7. `[New Session]` button → clears all session state and reruns

**Verification Step:**
```bash
streamlit run app.py
# Manual check: sidebar shows provider, verify button works, uploaders visible
```
**Pass condition:** Sidebar renders without errors. Verify connection button shows success or clear error message.

---

### Task 12.3 — Implement the Pipeline Progress Bar

**What to do:**
Implement `_render_progress_bar(current_stage: WorkflowStage)` as a `st.container()` spanning full width above the columns.

**Milestones:** `Q&A → Spec → Strategy → Test Cases → Code Plan → Script → Done`

**Mapping stages to milestones:**
```python
MILESTONE_MAP = {
    WorkflowStage.QA_INTERACTION: 0,
    WorkflowStage.REQUIREMENTS_SPEC_GEN: 1, WorkflowStage.JUDGE_REQUIREMENTS: 1, WorkflowStage.HUMAN_REVIEW_SPEC: 1,
    WorkflowStage.STRATEGY: 2, WorkflowStage.JUDGE_STRATEGY: 2, WorkflowStage.HUMAN_REVIEW_STRATEGY: 2,
    WorkflowStage.TEST_CASE_GENERATION: 3, WorkflowStage.JUDGE_TEST_CASES: 3, WorkflowStage.HUMAN_REVIEW_TEST_CASES: 3,
    WorkflowStage.CODE_STRUCTURE_PLANNING: 4, WorkflowStage.JUDGE_CODE_PLAN: 4, WorkflowStage.HUMAN_REVIEW_CODE_PLAN: 4,
    WorkflowStage.SCRIPTING: 5, WorkflowStage.JUDGE_CODE: 5, WorkflowStage.HUMAN_REVIEW_CODE: 5,
    WorkflowStage.COMPLETED: 6,
}
```

Use `st.progress()` and render milestone labels as `st.columns()` with colour-coded badges.

**Verification Step:** Visual inspection — progress bar renders with 7 milestones. **Pass condition:** No exceptions thrown during render.

---

### Task 12.4 — Implement the Artifact Tabs (Right Column)

**What to do:**
Implement `_render_artifact_tabs(state: AgentState)` for the right column (`col2`).

**Five tabs (from PRD Section 14.2):**
1. `📋 Spec` — `st.markdown(state.get("requirements_spec_content", "*Not generated yet.*"))`
2. `🗺️ Strategy` — same pattern
3. `🧩 Test Cases` — `st.code(state.get("gherkin_content", ""), language="gherkin")`
4. `📐 Code Plan` — `st.markdown(state.get("code_plan_content", "*Not generated yet.*"))`
5. `💻 Script` — `st.code(state.get("script_content", ""), language="python")` + download button

**Each tab also shows:**
- `st.caption(f"Version: {version}")` if version > 0
- Judge badge: `st.success / st.warning / st.error` for `PASS / NEEDS_HUMAN / FAIL`
- Judge score

**Verification Step:** Start app, add dummy state manually in session state, verify all 5 tabs render. **Pass condition:** No exceptions on render with empty state OR with dummy data.

---

### Task 12.5 — Implement the Q&A Interface (Left Column, `awaiting_qa=True`)

**What to do:**
Implement `_render_qa_form(qa_session: QASession)` (from PRD Section 14.5).

**Q&A form components:**
1. `st.subheader("🔍 Clarifying Questions")`
2. Confidence bar: `st.progress(confidence)` with caption
3. `st.form("qa_answers")` containing one `st.text_area()` per question (required questions marked `*`)
4. Submit button → collects answers → calls `graph.update_state()` → clears `awaiting_qa` → calls `graph.stream(None, config)` to resume → reruns

**Verification Step:** Manually trigger `st.session_state.awaiting_qa = True` with a dummy `QASession`, verify form renders. **Pass condition:** Form shows, submit button works without error.

---

### Task 12.6 — Implement the Human Review Gate UI (Left Column, `awaiting_review` set)

**What to do:**
Implement `_render_human_review_gate(gate_name: str, state: AgentState)` (from PRD Section 14.4).

**Gate UI components:**
1. `st.subheader(f"👤 Human Review Required: {gate_name.title()}")`
2. If NEEDS_HUMAN: show `st.warning(human_question)` from judge evaluation
3. `st.info("Review the artifact in the panel on the right.")`
4. Radio buttons: `decision = st.radio("Decision", ["APPROVE", "REJECT", "EDIT"])`
5. If REJECT or EDIT: show `st.text_area("Feedback")`
6. If EDIT: show large `st.text_area("Edit Document", value=current_content)`
7. Submit button → calls `graph.update_state(config, {"human_response": {...}})` → resumes stream → clears `awaiting_review` → reruns

**Verification Step:** Manually trigger `st.session_state.awaiting_review = "spec"`, verify gate UI renders correctly. **Pass condition:** All decision paths render without error.

---

### Task 12.7 — Wire the Main Chat Interface and Graph Streaming Loop

**What to do:**
Implement the main chat input area and graph execution loop (left column, `col1`).

**Components:**
1. `_render_chat_history()` — display `st.session_state.messages` in a scrollable container
2. `st.chat_input("Describe the feature you want to test...")` — triggers pipeline
3. On submit: call `fetch_context()`, call `create_initial_state()`, call `qa_graph.stream()` in a `for` loop
4. In the stream loop: catch `GraphInterrupt` → set `awaiting_review` or `awaiting_qa` → set `graph_state` → `st.rerun()`
5. On normal completion: set `workflow_status=COMPLETED` → show success message

**Verification Step:**
```
Manual end-to-end test:
1. Type a feature description in the chat input
2. Verify chat message appears
3. Verify pipeline progress bar advances
4. Verify artifact tabs populate as stages complete
5. Verify Q&A form appears if confidence is low
6. Verify human review gate appears at Gate #1
```
**Pass condition:** The app successfully triggers the pipeline and reaches Gate #1 without crashing.

---

### Task 12.8 — Final Streamlit Polish and Error Handling

**What to do:**
Add production-quality error handling and UX polish:

1. Wrap all `graph.stream()` calls in `try/except` — show `st.error(error_message)` on `RuntimeError` from LLM failures
2. Add `st.spinner("🤖 Generating...")` during graph execution
3. Show `st.toast("✅ Spec approved!")` on each gate approval
4. If `workflow_status == WorkflowStatus.FAILED`: show `st.error(state["error_message"])` prominently
5. Script tab download button: `st.download_button("⬇️ Download Test Script", data=script_content, file_name="test_generated.py")`

**Verification Step:**
```
Manual test:
1. Simulate LLM failure (use invalid API key temporarily) → verify error shows cleanly
2. Complete full pipeline to Gate #1 → approve → verify toast shows
3. At Script tab → verify download button works
```
**Pass condition:** No unhandled exceptions in any error path. UX is clean and informative.

---

## PHASE 13 — README and Final Documentation
> **Goal:** A developer can clone the repo and be running in under 10 minutes by following only the README.

---

### Task 13.1 — Create `README.md`

**What to do:**
Create a comprehensive `README.md` covering:

1. **Overview** — 3-line description of what QA-GPT does
2. **Prerequisites** — Python 3.12.7, pip, AWS or Gemini credentials
3. **Installation** — `git clone`, `python -m venv`, `pip install -r requirements.txt`, `cp .env.example .env`
4. **Configuration** — Step-by-step: Office laptop (Bedrock), Personal laptop (Gemini)
5. **Context Files** — How to fill in `tech_context.md` and `codebase_map.md` with concrete examples
6. **Running the App** — `streamlit run app.py`
7. **Using the Pipeline** — Walkthrough of all 5 gates with what to expect at each
8. **Example Prompts** — Copy all 3 examples from Appendix B of the PRD
9. **Troubleshooting** — Common errors (Bedrock auth, Gemini quota, Gherkin parse errors) with solutions
10. **V2 Migration Notes** — Which files to change and what changes to make (from PRD Section 17)
11. **Running Tests** — `pytest tests/unit/` and `pytest tests/integration/ -m integration`

**Verification Step:**
```bash
# Have a colleague (or fresh terminal) follow only the README
# They should be able to run: pytest tests/unit/ -v
# And see: streamlit run app.py launch without import errors
# Checklist:
# [ ] README has no broken links
# [ ] All commands in README execute without error
# [ ] Tech context template is well-explained
python -c "
from pathlib import Path
readme = Path('README.md').read_text()
required_sections = ['Installation', 'Configuration', 'Bedrock', 'Gemini', 'tech_context', 'Troubleshooting', 'V2']
for s in required_sections:
    assert s in readme, f'Missing section: {s}'
print('README sections OK')
"
```
**Pass condition:** README script passes. A new developer can follow it from scratch and get to a running app.

---

## PHASE 14 — Final Regression & Smoke Test
> **Goal:** Every phase is still working after the full implementation. Run the complete test suite.

---

### Task 14.1 — Full Test Suite Run

**What to do:**
Run the complete unit test suite. All tests from all phases must pass simultaneously.

**Verification Step:**
```bash
# Full unit test suite (no LLM calls)
pytest tests/unit/ -v --tb=short --cov=src --cov-report=term-missing

# Expected results:
# tests/unit/test_settings.py             ✓ 3 tests
# tests/unit/test_state_enums.py          ✓ 4 tests
# tests/unit/test_state_dataclasses.py    ✓ 5 tests
# tests/unit/test_state_factory.py        ✓ 5 tests
# tests/unit/test_stub_nodes.py           ✓ 19 tests
# tests/unit/test_conditional_edges.py    ✓ 3 tests
# tests/unit/test_checkpointer.py         ✓ 2 tests
# tests/unit/test_graph_builder.py        ✓ 3 tests
# tests/unit/test_gherkin_validator.py    ✓ 4 tests
# tests/unit/test_context_fetcher.py      ✓ 5 tests
# tests/unit/test_all_prompts.py          ✓ 13 tests
# tests/unit/test_qa_interaction_node.py  ✓ 4 tests
# ... (all node tests)
# tests/unit/test_stub_v2_nodes.py        ✓ 3 tests
```
**Pass condition:** 100% of unit tests GREEN. Coverage > 75%.

---

### Task 14.2 — Full Integration Test Run (Requires Credentials)

**Verification Step:**
```bash
# Integration tests (real LLM calls)
pytest tests/integration/ -m integration -v -s --tb=short
```
**Pass condition:** `test_verify_connection` GREEN. `test_call_llm_returns_llm_response` GREEN. `test_full_pipeline` runs at least 3 stages and hits Gate #1 interrupt.

---

## TASK COMPLETION TRACKER

| Phase | Tasks | Status |
|---|---|---|
| Phase 1: Scaffold & Config | 1.1, 1.2, 1.3 | ⬜⬜⬜ |
| Phase 2: Core State & Types | 2.1, 2.2, 2.3 | ⬜⬜⬜ |
| Phase 3: Infrastructure Layer | 3.1, 3.2, 3.3 | ⬜⬜⬜ |
| Phase 4: Graph Topology | 4.1, 4.2, 4.3, 4.4 | ⬜⬜⬜⬜ |
| Phase 5: Agent Prompts | 5.1–5.12 | ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ |
| Phase 6: Generative Nodes | 6.1–6.6 | ⬜⬜⬜⬜⬜⬜ |
| Phase 7: Judge Nodes | 7.1–7.6 | ⬜⬜⬜⬜⬜⬜ |
| Phase 8: Human Review Nodes | 8.1–8.5 | ⬜⬜⬜⬜⬜ |
| Phase 9: V2 Stubs | 9.1, 9.2 | ⬜⬜ |
| Phase 10: Context Templates | 10.1, 10.2 | ⬜⬜ |
| Phase 11: E2E Integration Test | 11.1 | ⬜ |
| Phase 12: Streamlit UI | 12.1–12.8 | ⬜⬜⬜⬜⬜⬜⬜⬜ |
| Phase 13: README | 13.1 | ⬜ |
| Phase 14: Final Regression | 14.1, 14.2 | ⬜⬜ |

**Total: 56 tasks across 14 phases.**

---

## DEPENDENCY GRAPH (Critical Path)
```
1.1 → 1.2 → 1.3
              ↓
            2.1 → 2.2 → 2.3
                          ↓
              ┌────────── 3.1 (LLM Client)
              │           ↓
              │          3.2 (Context Fetcher)
              │           ↓
              │          3.3 (Gherkin Validator)
              │                    ↓
              └──────────→ 4.1 → 4.2 → 4.3 → 4.4 (Graph Skeleton)
                                               ↓
                                      5.1–5.12 (Prompts, parallel)
                                               ↓
                                      6.1–6.6 (Generative Nodes, sequential)
                                               ↓
                                      7.1 → 7.2–7.6 (Judge Nodes)
                                               ↓
                                      8.1 → 8.2–8.5 (Human Review Nodes)
                                               ↓
                                      9.1, 9.2 (V2 Stubs, parallel)
                                      10.1, 10.2 (Templates, parallel)
                                               ↓
                                      11.1 (E2E Integration Test)
                                               ↓
                                      12.1–12.8 (Streamlit UI, sequential)
                                               ↓
                                      13.1 (README)
                                               ↓
                                      14.1 → 14.2 (Final Regression)
```