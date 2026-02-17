# Technical Context: Geo-Filter KStream Application

## System Overview
A Kafka Stream (KStream) application that consumes user activity data and splits it into two streams based on the `bib` (country code) field.

## Architecture
- **Framework**: JVM-based (Java/Kotlin) using Kafka Streams API
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
