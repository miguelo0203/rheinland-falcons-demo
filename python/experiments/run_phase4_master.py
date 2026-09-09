"""Phase 4 Master Orchestrator for Statistical Analysis & Coach Analytical Layer."""

import sys
import time
from pathlib import Path

sys.path.insert(0, ".")

from python.analytics.phase4_population_audit import audit_populations_and_denominators
from python.analytics.phase4_statistical_engine import run_statistical_engine
from python.analytics.phase4_player_engine import run_player_evolution_engine
from python.analytics.phase4_shot_engine import run_shot_engine
from python.analytics.phase4_evidence_and_coach_layer import build_coach_and_evidence_layers

def run_full_phase4():
    print("==========================================================================")
    print("   STARTING PHASE 4: STATISTICAL ANALYSIS & COACH ANALYTICAL LAYER        ")
    print("==========================================================================")
    t0 = time.time()

    # Step 1: Pre-Analysis Population & Denominator Audit
    print("\n--- [STEP 1/5] Auditing Populations & Denominators ---")
    denoms = audit_populations_and_denominators()

    # Step 2: Statistical Engine & Four Factors Significance
    print("\n--- [STEP 2/5] Running Statistical Engine & Four Factors Analysis ---")
    df_tga, df_tsa, df_lca = run_statistical_engine()

    # Step 3: Longitudinal Player Performance & Evolution
    print("\n--- [STEP 3/5] Running Player Longitudinal & Role Evolution Engine ---")
    df_pga, df_pra, df_pwa = run_player_evolution_engine()

    # Step 4: Shot Spatial Breakdown & Zone Analysis
    print("\n--- [STEP 4/5] Running Shot Spatial & Zone Engine ---")
    df_shots, zone_summary = run_shot_engine()

    # Step 5: Coach Summary Layer & Evidence Traceability
    print("\n--- [STEP 5/5] Building Coach Findings, Evidence Trail & Hypotheses ---")
    build_coach_and_evidence_layers()

    elapsed = round(time.time() - t0, 2)
    print("\n==========================================================================")
    print(f"   PHASE 4 COMPLETE: ALL 10 PARQUET DATASETS & 6 DOCS GENERATED IN {elapsed}s")
    print("==========================================================================")

if __name__ == "__main__":
    run_full_phase4()
