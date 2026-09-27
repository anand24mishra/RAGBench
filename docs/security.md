# Security

## Status

V1 implements bounded uploads, typed request validation, restricted file types, secret-backed provider configuration, conservative prompt boundaries, and content-minimizing logs. Authentication, authorization, rate limiting, malware scanning, and a production secret manager are not implemented. The API should not be exposed to an untrusted network in its current form.

## Control inventory

| Area | Status | Current behavior |
| --- | --- | --- |
| API authentication | Planned | All endpoints are unauthenticated |
| Input validation | Implemented | Pydantic rejects malformed queries; loader limits formats, encoding, empty content, and upload size |
| Prompt injection | Partial | Retrieved content is delimited and the system prompt says it is untrusted evidence; no model-independent policy enforcement exists |
| Malicious documents | Partial | Size, extension, and UTF-8 checks exist; no malware scan or parser isolation is needed for V1 text decoding, but resource abuse remains possible |
| Secret handling | Implemented | API key comes from environment or `.env`, uses `SecretStr`, and is excluded from logs |
| Sensitive-content logging | Implemented | `JsonFormatter` recursively redacts `authorization`, `api_key`, `secret`, `password`, `token` to `[REDACTED]` |
| Network timeout boundaries | Implemented | Explicit deadlines configured for all external calls (`llm_timeout_seconds`) |
| Dependency security | Planned | Version ranges and a pinned Qdrant image exist; no lockfile or vulnerability scanner exists |
| Rate limiting | Planned | No request or provider quota protection exists |

## Prompt injection

Documents are untrusted input. The context format labels each retrieved section as source content, and the system prompt instructs the model not to treat retrieved instructions as system instructions. This does not prevent all prompt injection. V1-V5 has no tools or data-changing model actions, which limits impact, but generated text can still be manipulated. Future tool use would require permissions outside the model and output validation.

## Document handling

The API reads at most `MAX_UPLOAD_BYTES + 1` bytes before rejecting an oversized upload. It accepts only filenames ending in `.txt`, `.md`, or `.markdown`, decodes as UTF-8, and rejects whitespace-only files. The original bytes are not written to the application filesystem. Chunk text is stored in Qdrant payloads.

Filename extensions are not proof of content type. Text decoding is strictly enforced and invalid UTF-8 sequences trigger `DocumentDecodeError`.

## Provider credentials

`LLM_API_KEY` is required for commercial providers. `.env.example` contains placeholders and `.gitignore` excludes `.env`. The key is sent only as a bearer header to `LLM_BASE_URL`. Operators must verify that a custom base URL is trusted because the application will send the configured key to it.

## Error and Log Exposure

External provider and Qdrant exception details are replaced with typed application messages at the HTTP boundary. Validation responses do not echo invalid user content. `JsonFormatter` automatically redacts sensitive substrings and bearer authorization tokens.

## Benchmark and Evaluation Artifact Privacy

Benchmark and generation evaluation reports (`evaluation/reports/*.json`, `*.md`) persist questions, retrieved chunks, generated answers, and reference answers for inspection:
- **Sensitivity Assumption**: Evaluation datasets (`evaluation/dataset/`) are assumed to contain non-confidential, public engineering documentation.
- **Enterprise Precaution**: Do not run RAGBench evaluations against proprietary or personally identifiable information (PII) without restricting access to the resulting report directory and version-control repositories.

## Remaining requirements before public deployment

- authentication and authorization;
- TLS at the deployment boundary;
- rate and upload concurrency limits;
- a managed secret source and rotation process;
- Qdrant network isolation and storage controls;
- pinned dependency resolution and automated vulnerability scanning; and
- a retention policy for vector payloads and logs.
