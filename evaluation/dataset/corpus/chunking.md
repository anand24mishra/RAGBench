# Chunking

The V1 baseline uses fixed-size character chunks. The default chunk size is 800 characters and the default overlap is 100 characters. The next chunk begins at `chunk_size - chunk_overlap`.

Each chunk preserves the source document ID and metadata. Its metadata adds a zero-based chunk index plus start and end character offsets. The chunk ID is a SHA-256 digest derived from the document ID and those start and end offsets, making the result deterministic for unchanged content and configuration.
