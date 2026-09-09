# Phase 7: Recovery and Backup Policy

## Key Principle
**FAILED OPERATION → NO PARTIAL CORRUPTED STATE → RECOVERABLE**

## 1. Failed Ingestion Recovery
The platform processes input files atomically. If data ingestion fails midway through, DuckDB's transaction rollback mechanism prevents partial states. Corrupted or invalid JSON states should throw an error, roll back, and leave the source database completely unaffected.

## 2. Malformed Input Handling
Any malformed inputs detected during the validation phase should be rejected upfront. These items should not halt the entire pipeline indefinitely but should be moved or preserved in a designated `rejected/` directory for manual inspection.

## 3. Failed Database Transaction Recovery
The database relies on atomic commits. If a DuckDB transaction fails (e.g., due to a constraint violation), the system natively drops all changes within that scope. Automated scripts should log the stack trace and exit gracefully, ensuring that data integrity is maintained.

## 4. Failed Recomputation Recovery
Derived analytical datasets (Parquet files) are wholly dependent on the DuckDB source of truth. If a recomputation pipeline fails, no data is permanently lost. The system simply falls back to the previous intact Parquet files or triggers a full recomputation once the issue is resolved.

## 5. Interrupted Operation Recovery
All ingestion routines must be designed iteratively. If an operation is interrupted (SIGINT, power loss), rerunning the command should identify already processed `game_id` entities and resume appropriately without causing duplication. Overwrite logic should drop and replace whole scopes securely if required.

## 6. Corrupted Derived Parquet Recovery
Should Parquet files become corrupted or accidentally deleted, they can be flawlessly reconstructed via a CLI command that spins up DuckDB, executes the materialized views and complex queries, and dumps the tables straight back out to disk.

## 7. Corrected Source Payload Handling
In cases where a raw input file is corrected externally after prior ingestion, the application should cleanly delete dependencies in the correct relational order (shot → pbp_event → boxscore_player → boxscore_team → game) before re-inserting the corrected dataset. (Note: Current operations simply delete and re-insert; this should be explicitly monitored for FK constraint violations).
