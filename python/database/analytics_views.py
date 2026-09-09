import sys
sys.path.insert(0, ".")
from python.database.duckdb_manager import DuckDBManager

def create_analytics_views(db: DuckDBManager):
    """Initializes all analytical SQL views in DuckDB."""
    conn = db.conn

    # 1. Team Game Ratings & Four Factors View
    conn.execute("""
    CREATE OR REPLACE VIEW view_team_game_ratings AS
    WITH team_stats AS (
        SELECT
            bt.game_id,
            bt.team_id,
            t.canonical_name AS team_name,
            bt.is_home,
            bt.points,
            bt.fgm,
            bt.fga,
            bt.fg2m,
            bt.fg2a,
            bt.fg3m,
            bt.fg3a,
            bt.ftm,
            bt.fta,
            bt.orb,
            bt.drb,
            bt.trb,
            bt.stl,
            bt.blk,
            bt.tov,
            bt.pf,
            bt.team_rebounds,
            -- Opponent stats join
            opp.team_id AS opp_team_id,
            opp.canonical_name AS opp_name,
            opp.points AS opp_points,
            opp.fga AS opp_fga,
            opp.fta AS opp_fta,
            opp.orb AS opp_orb,
            opp.drb AS opp_drb,
            opp.tov AS opp_tov
        FROM boxscore_team bt
        JOIN team t ON bt.team_id = t.team_id
        JOIN (
            SELECT bt2.game_id, bt2.team_id, t2.canonical_name, bt2.points, bt2.fga, bt2.fta, bt2.orb, bt2.drb, bt2.tov
            FROM boxscore_team bt2
            JOIN team t2 ON bt2.team_id = t2.team_id
        ) opp ON bt.game_id = opp.game_id AND bt.team_id != opp.team_id
    )
    SELECT
        game_id,
        team_id,
        team_name,
        is_home,
        points,
        opp_points,
        points - opp_points AS point_diff,
        fgm,
        fga,
        fg3m,
        fg3a,
        ftm,
        fta,
        orb,
        drb,
        tov,
        opp_drb,
        -- Possessions estimation (Dean Oliver FIBA model)
        ROUND(fga + 0.44 * fta - orb + tov, 1) AS possessions,
        -- Four Factors
        ROUND((fgm + 0.5 * fg3m) / NULLIF(fga, 0) * 100.0, 1) AS efg_pct,
        ROUND(tov / NULLIF(fga + 0.44 * fta + tov, 0) * 100.0, 1) AS tov_pct,
        ROUND(orb / NULLIF(orb + opp_drb, 0) * 100.0, 1) AS orb_pct,
        ROUND(fta / NULLIF(fga, 0), 3) AS ftr,
        -- Offensive & Defensive Rating
        ROUND(100.0 * points / NULLIF(fga + 0.44 * fta - orb + tov, 0), 1) AS ortg,
        ROUND(100.0 * opp_points / NULLIF(opp_fga + 0.44 * opp_fta - opp_orb + opp_tov, 0), 1) AS drtg,
        ROUND(100.0 * (points - opp_points) / NULLIF(fga + 0.44 * fta - orb + tov, 0), 1) AS net_rtg
    FROM team_stats;
    """)

    # 2. Player Aggregated Boxscore Statistics View
    conn.execute("""
    CREATE OR REPLACE VIEW view_player_season_stats AS
    SELECT
        p.player_id,
        p.canonical_name,
        bp.team_id,
        t.canonical_name AS team_name,
        COUNT(DISTINCT bp.game_id) AS games_played,
        ROUND(AVG(bp.seconds_played / 60.0), 1) AS mpg,
        ROUND(AVG(bp.points), 1) AS ppg,
        ROUND(AVG(bp.trb), 1) AS rpg,
        ROUND(AVG(bp.ast), 1) AS apg,
        ROUND(AVG(bp.stl), 1) AS spg,
        ROUND(AVG(bp.blk), 1) AS bpg,
        ROUND(AVG(bp.tov), 1) AS topg,
        SUM(bp.fgm) AS total_fgm,
        SUM(bp.fga) AS total_fga,
        ROUND(SUM(bp.fgm) * 100.0 / NULLIF(SUM(bp.fga), 0), 1) AS fg_pct,
        SUM(bp.fg3m) AS total_fg3m,
        SUM(bp.fg3a) AS total_fg3a,
        ROUND(SUM(bp.fg3m) * 100.0 / NULLIF(SUM(bp.fg3a), 0), 1) AS fg3_pct,
        SUM(bp.ftm) AS total_ftm,
        SUM(bp.fta) AS total_fta,
        ROUND(SUM(bp.ftm) * 100.0 / NULLIF(SUM(bp.fta), 0), 1) AS ft_pct,
        -- True Shooting %
        ROUND(SUM(bp.points) * 100.0 / NULLIF(2 * (SUM(bp.fga) + 0.44 * SUM(bp.fta)), 0), 1) AS ts_pct
    FROM boxscore_player bp
    JOIN player p ON bp.player_id = p.player_id
    JOIN team t ON bp.team_id = t.team_id
    WHERE bp.is_dnp = FALSE
    GROUP BY p.player_id, p.canonical_name, bp.team_id, t.canonical_name
    HAVING COUNT(DISTINCT bp.game_id) >= 1;
    """)

    # 3. Shot Spatial Distribution View
    conn.execute("""
    CREATE OR REPLACE VIEW view_shot_spatial_summary AS
    SELECT
        s.team_id,
        t.canonical_name AS team_name,
        s.shot_type,
        s.shot_location_status,
        COUNT(*) AS total_shots,
        SUM(CASE WHEN s.is_made THEN 1 ELSE 0 END) AS made_shots,
        ROUND(SUM(CASE WHEN s.is_made THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS fg_pct,
        SUM(s.points) AS total_points,
        AVG(s.x_coord) AS avg_x,
        AVG(s.y_coord) AS avg_y
    FROM shot s
    JOIN team t ON s.team_id = t.team_id
    GROUP BY s.team_id, t.canonical_name, s.shot_type, s.shot_location_status;
    """)

    print("Analytical SQL views initialized successfully in DuckDB.")

if __name__ == "__main__":
    db = DuckDBManager()
    create_analytics_views(db)
