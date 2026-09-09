# JBBL / NBBL Sandbox Guide

## Purpose
This sandbox environment is created to test, inspect, and evaluate incoming JBBL/NBBL youth basketball data before promoting adapters and schemas to the production Club Analytics system.

## Isolation Philosophy
- **Workspace**: `f:\Rheinland Falcons Prueba`
- **Database**: `database/jbbl_sandbox.duckdb`
- **Zero Production Mutations**: Production files and database in `f:\Rheinland Falcons` are strictly isolated.

## Experimental Workflow
1. **Source Audit**: Place raw sample files in `data/raw/boxscore/` or `data/raw/pbp/`.
2. **Experimental Parsing**: Develop candidate parsers under `python/experiments/`.
3. **Canonical Mapping**: Verify whether fields fit the canonical schema without inventing unnecessary tables.
4. **Validation & Quality Assessment**: Check mathematical reconciliation and quality tiering.
5. **Promotion to Production**: Once verified and stable, adapter code and schema refinements can be safely migrated to the production repository.
