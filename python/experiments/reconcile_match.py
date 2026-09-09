"""Reconcile PBP events with Boxscore for match 9995585 to test data integrity."""

import json
from pathlib import Path

def test_reconciliation():
    decoded_file = Path("reports/source_audit/samples/match_9995585_decoded.json")
    data = json.loads(decoded_file.read_text(encoding="utf-8"))
    
    team_stats = data["team_stats"]
    player_stats = data["player_stats"]
    actions = data["actions"]
    scorelist = data["scorelist"]
    
    print("=== Reconciling Boxscore and PBP for Match 9995585 ===")
    
    # 1. Final Score from Boxscore Teams
    # Team A = Rheinland, Team B = Isar Bulls
    team_a = next(t for t in team_stats if t["teamcode"] == "A")
    team_b = next(t for t in team_stats if t["teamcode"] == "B")
    
    # Calculate boxscore points
    box_pts_a = team_a["FT_points"] + team_a["P2_points"] + team_a["P3_points"]
    box_pts_b = team_b["FT_points"] + team_b["P2_points"] + team_b["P3_points"]
    print(f"Team A (Rheinland) Boxscore Points: {box_pts_a} (FT={team_a['FT_points']}, 2P={team_a['P2_points']}, 3P={team_a['P3_points']})")
    print(f"Team B (Isar Bulls) Boxscore Points: {box_pts_b} (FT={team_b['FT_points']}, 2P={team_b['P2_points']}, 3P={team_b['P3_points']})")
    
    # 2. Player sum points
    p_pts_a = sum(p["points"] for p in player_stats if p["teamcode"] == "A")
    p_pts_b = sum(p["points"] for p in player_stats if p["teamcode"] == "B")
    print(f"\nPlayer Points Sum A: {p_pts_a} vs Team Total: {box_pts_a} (Diff: {p_pts_a - box_pts_a})")
    print(f"Player Points Sum B: {p_pts_b} vs Team Total: {box_pts_b} (Diff: {p_pts_b - box_pts_b})")
    
    # 3. Scorelist Final Score
    last_score = scorelist[-1]
    print(f"\nScorelist Final Score: {last_score['points_1']} - {last_score['points_2']}")
    
    # 4. PBP Actions Scoring Sum
    pbp_pts_by_player = {}
    pbp_pts_a = 0
    pbp_pts_b = 0
    shots_count = 0
    shots_with_coords = 0
    
    for a in actions:
        act = a.get("action")
        res = a.get("result")
        pts = 0
        if act == "FT" and res == "+":
            pts = 1
        elif act in ["P2", "JS", "LU", "DU", "AO", "TI"] and res == "+" and a.get("info2") != 3: # 2pt made
            pts = 2
        elif act == "P3" and res == "+":
            pts = 3
        elif res == "+" and a.get("info2") == 3: # 3pt
            pts = 3
        elif res == "+" and a.get("info2") == 2: # 2pt
            pts = 2

        if act in ["P2", "P3", "JS", "FT"]:
            shots_count += 1
            if a.get("x") is not None and a.get("y") is not None:
                shots_with_coords += 1

        if pts > 0:
            pid = a.get("player_id1")
            pbp_pts_by_player[pid] = pbp_pts_by_player.get(pid, 0) + pts
            if a.get("teamcode") == "A":
                pbp_pts_a += pts
            elif a.get("teamcode") == "B":
                pbp_pts_b += pts

    print(f"\nPBP Calculated Points A: {pbp_pts_a} vs Boxscore A: {box_pts_a}")
    print(f"PBP Calculated Points B: {pbp_pts_b} vs Boxscore B: {box_pts_b}")
    print(f"Total Shots in PBP: {shots_count}, Shots with X,Y Court Coordinates: {shots_with_coords} ({round(shots_with_coords/shots_count*100, 1)}%)")

    # 5. Player Level Reconciliation Sample
    print("\n--- Player Points Reconciliation (Sample) ---")
    for p in player_stats[:8]:
        pid = p["player_id"]
        box_pts = p["points"]
        pbp_p = pbp_pts_by_player.get(pid, 0)
        status = "MATCH" if box_pts == pbp_p else f"DIFF ({pbp_p - box_pts})"
        print(f"Player {p['player_nr']} (ID {pid}, Team {p['teamcode']}): Boxscore={box_pts}, PBP={pbp_p} -> {status}")

if __name__ == "__main__":
    test_reconciliation()
