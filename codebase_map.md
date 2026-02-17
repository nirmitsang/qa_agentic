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
