# Python Experiments Directory

This directory is designated for experimental parsing, source exploration, and prototype transformations for JBBL/NBBL youth league data.

## Guidelines
1. **Isolated Exploration**: Scripts here can test candidate adapters, regex patterns, or dirty data handlers without polluting canonical ingestion modules (`python/ingestion/`).
2. **Transfer to Production**: Once an experimental adapter or validation check is proven against real JBBL/NBBL data, it can be formalized as a canonical adapter in `python/ingestion/` and transferred to production.
3. **Traceability**: Always log source format findings, edge cases, and unexpected provider structures.
