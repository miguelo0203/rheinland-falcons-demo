# Historical Immutability & Audit Trail Policy

## 1. Zero Mutation of Historical Evidence
1. **Append-Only Invariants**: Newly ingested fixtures are appended without modifying existing database rows or raw files.
2. **True NO-OP on Identical Payloads**: When an already ingested fixture is processed with an identical SHA-256 payload hash, the engine executes a complete NO-OP.
3. **Audit Versioning on Source Corrections**: If an external data source issues an official correction to a previous game, the existing raw payload is preserved as a timestamped backup before archiving the updated record.