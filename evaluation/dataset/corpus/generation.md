# Generation

Generation uses an asynchronous OpenAI-compatible provider selected through typed configuration. The provider reads `LLM_API_KEY` from environment-backed settings and never hard-codes the credential. Model, base URL, timeout, temperature, and maximum output tokens are configurable.

The prompt instructs the model to answer from retrieved context and report when evidence is insufficient. If retrieval returns no chunks, the pipeline returns an insufficient-context answer without calling the LLM provider. This behavior does not guarantee that all hallucinations are prevented.
