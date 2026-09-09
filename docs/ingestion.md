# Ingestion Pipeline Architecture

## 1. Ingestion Principles
1. **Multi-Source Modality**: Adapters for Boxscore, Play-by-Play (PBP), and Video operate independently.
2. **Deterministic Extraction**: Raw contents are never mutated during parsing.
3. **Automated Hashing**: Content SHA-256 is generated before writing to normalized storage.
4. **Resilient Defaults**: When only partial sources are present (e.g. video only), the pipeline constructs valid default metadata rather than failing.
