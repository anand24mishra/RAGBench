# Observability

Each HTTP request receives a server-generated request ID. Structured JSON events cover request completion, retrieval, generation, and handled failures. Application logging omits uploaded document bodies, user questions, retrieved text, generated answers, API keys, and authorization headers.

A successful query response records query-embedding latency, Qdrant vector-search latency, generation latency, and total pipeline latency. It also returns similarity scores, source identifiers, the model identifier, and provider-reported input and output token counts when available.
