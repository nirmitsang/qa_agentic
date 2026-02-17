# Mock Artifacts for KStream & OpenShift Testing

Use these artifacts to test the QA-GPT flow for your specific Kafka Stream use case.

## 1. Context Files (Upload these to the app)

### `tech_context.md`
*Describes the system architecture, data flow, and available tools.*

```markdown
# Technical Context: Geo-Filter KStream Application

## System Overview
A Kafka Stream (KStream) application that consumes user activity data and splits it into two streams based on the `bib` (country code) field.

## Architecture
- **Framework**: Kotlin / Kafka Streams 3.5.0
- **Deployment**: OpenShift / Kubernetes
- **Input Topic**: `user-activity-input`
- **Output Topic A** (Target): `china-user-activity` (where `bib` == "china" case-insensitive)
- **Output Topic B** (Other): `global-user-activity` (where `bib` != "china")

## Data Schema (JSON)
```json
{
  "userId": "string (uuid)",
  "bib": "string",       // Country code, e.g., "china", "usa", "india"
  "activity": "string",  // e.g., "login", "purchase"
  "timestamp": "long"
}
```

## Available Test Helpers
The test framework provides the following pre-built clients:

1.  **`KafkaTestClient`**
    *   `produce(topic, message)`: Send JSON message to a topic.
    *   `consume_all(topic, timeout_ms)`: return List<String> of messages from a topic.

2.  **`OpenShiftClient`**
    *   `is_job_running(job_name)`: Returns `True` if the KStream job pod is active and ready.
    *   `restart_job(job_name)`: Triggers a rollout restart.
```

---

### `codebase_map.md`
*Describes the project structure so QA-GPT knows where code lives.*

```markdown
# Codebase Map

## Source Code
- `src/main/kotlin/com/example/geo/GeoFilterTopology.kt`: Defines the KStream topology and split logic.
- `src/main/kotlin/com/example/geo/Serdes.kt`: JSON custom serializers/deserializers.

## Test Infrastructure
- `src/test/utils/KafkaTestClient.py`: Python wrapper for confluent-kafka (available in test runtime).
- `src/test/utils/OpenShiftClient.py`: Python wrapper for oc/kubectl commands.
- `src/test/e2e/base_test.py`: Base class handling setup/teardown.

## Existing Tests
- `src/test/e2e/test_health.py`: Simple health checks.
```

---

## 2. Test Scenarios & Prompts

Copy these prompts into the specific "active interaction" chat areas in the Streamlit UI.

### Scenario A: Happy Path (Filter Logic)
**Goal**: Verify data routing is correct.

**Prompt for Chat:**
> I want to test the KStream logic that filters traffic for China. It should read from `user-activity-input`. If the "bib" field is "china", it goes to the `china-user-activity` topic. Otherwise, it goes to `global-user-activity`. Use the existing `KafkaTestClient` to push messages and verify they land in the right topics.

### Scenario B: Infrastructure Pre-condition (OpenShift)
**Goal**: Verify the job is actually running before testing.

**Prompt for Chat:**
> Test the Geo-Filter stream, but first ensure the OpenShift job "geo-filter-v1" is running using the `OpenShiftClient`. If it's not running, fail the test immediately. Then proceed to test that "bib": "china" messages are routed correctly.

### Scenario C: Edge Case (Null/Missing Fields)
**Goal**: Verify robustness against bad data.

**Prompt for Chat:**
> Write a test for the KStream application that handles edge cases. Specifically, what happens if the input JSON has a null "bib" field or is missing the "bib" field entirely? It should probably go to the global topic or a dead-letter queue (assume global for now). Send malformed JSON and verify the application doesn't crash, checking the pod status with `OpenShiftClient`.
```
