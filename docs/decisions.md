# Decisions Log

## Decision: Async Job Model
- **Context**: OCR can be slow; synchronous APIs block clients and limit scale.
- **Decision**: Use async job model with 202 Accepted and job polling.
- **Tradeoffs**: Simpler client logic, scalable backend, but requires polling and job tracking.

## Decision: request_id Header Tracing
- **Context**: Traceability and debugging require unique request IDs.
- **Decision**: Include request_id in body and x-request-id header for all responses.
- **Tradeoffs**: Slight overhead, but enables robust tracing and contract compliance.

## Decision: Per-Image Payload Cap (10MB)
- **Context**: Large images can exhaust resources; need strict limits.
- **Decision**: Enforce 10MB per image, 20MB total per request (decoded).
- **Tradeoffs**: Prevents abuse, ensures contract, but may reject legitimate large documents.

## Decision: Project-Scoped Job Isolation
- **Context**: Multi-tenant projects must not access each other's jobs.
- **Decision**: Jobs are scoped to project_id; GET only returns jobs for correct project_id.
- **Tradeoffs**: Strong isolation, but requires careful contract enforcement.

---
For architecture, see [architecture.md](architecture.md).
For testing, see [testing.md](testing.md).
