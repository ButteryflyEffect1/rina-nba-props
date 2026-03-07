import math
import time
import requests
import pandas as pd
import streamlit as st

from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, teamgamelog


# =========================
# CONFIG
# =========================
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

SPORT = "basketball_nba"
REGIONS = "us"
MARKETS = "player_points,player_rebounds,player_assists"
ODDS_FORMAT = "american"

SEASON = "2025-26"
REQUEST_SLEEP = 0.6
ODDS_SLEEP = 0.25


# =========================
# PAGE SETUP
# =========================
st.set_page_config(
    page_title="Rina's Cheatsheet",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #060b16 0%, #08101d 100%);
        color: #f8fafc;
    }

    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
        max-width: 1480px;
    }

    .title-wrap {
        margin-bottom: 0.6rem;
    }

    .app-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 0.1rem;
        line-height: 1.02;
    }

    .app-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 0;
        margin-bottom: 0.35rem;
    }

    .section-title {
        font-size: 1.9rem;
        font-weight: 800;
        margin: 0.9rem 0 0.7rem 0;
        color: #f8fafc;
    }

    .control-card {
        background: linear-gradient(180deg, rgba(18, 25, 41, 0.96), rgba(13, 19, 32, 0.96));
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 16px;
        padding: 14px 14px 10px 14px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.20);
        margin-bottom: 0.9rem;
    }

    .bet-card {
        background: linear-gradient(180deg, rgba(18, 25, 41, 0.96), rgba(13, 19, 32, 0.96));
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 15px;
        padding: 10px 11px 10px 11px;
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18);
        margin-bottom: 10px;
    }

    .bet-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 8px;
    }

    .player-name {
        font-size: 0.98rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 1px;
        line-height: 1.12;
    }

    .meta-line {
        font-size: 0.8rem;
        color: #94a3b8;
    }

    .pill-row {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-top: 6px;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 3px 8px;
        font-size: 0.68rem;
        font-weight: 700;
        border: 1px solid transparent;
    }

    .pill-stat {
        background: rgba(59, 130, 246, 0.14);
        color: #93c5fd;
        border-color: rgba(59, 130, 246, 0.25);
    }

    .pill-over {
        background: rgba(34, 197, 94, 0.16);
        color: #86efac;
        border-color: rgba(34, 197, 94, 0.28);
    }

    .pill-under {
        background: rgba(239, 68, 68, 0.16);
        color: #fca5a5;
        border-color: rgba(239, 68, 68, 0.28);
    }

    .pill-pass {
        background: rgba(250, 204, 21, 0.12);
        color: #fde68a;
        border-color: rgba(250, 204, 21, 0.24);
    }

    .card-linebox {
        text-align: right;
        min-width: 68px;
    }

    .line-label {
        color: #94a3b8;
        font-size: 0.64rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }

    .line-value {
        color: #f8fafc;
        font-size: 1.08rem;
        font-weight: 800;
        line-height: 1.05;
        margin-top: 1px;
    }

    .rank-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 24px;
        height: 24px;
        border-radius: 999px;
        background: rgba(255,255,255,0.06);
        color: #f8fafc;
        font-size: 0.72rem;
        font-weight: 800;
        margin-right: 8px;
        margin-top: 1px;
    }

    .row-head {
        display: flex;
        align-items: flex-start;
    }

    .metric-box-wrap {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(148, 163, 184, 0.10);
        border-radius: 11px;
        padding: 7px 9px;
        min-height: 56px;
    }

    .metric-label {
        color: #94a3b8;
        font-size: 0.66rem;
        margin-bottom: 2px;
        line-height: 1.1;
    }

    .metric-value {
        color: #f8fafc;
        font-size: 0.95rem;
        font-weight: 800;
        line-height: 1.15;
        word-break: break-word;
    }

    .metric-score {
        color: #60a5fa;
    }

    [data-testid="collapsedControl"] {
        display: none;
    }

    div[data-testid="stVerticalBlock"] > div:has(> div > div > div.metric-box-wrap) {
        gap: 0.45rem;
    }

    @media (max-width: 950px) {
        .app-title {
            font-size: 2.3rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="title-wrap">
        <div class="app-title">Rina's Cheatsheet</div>
        <div class="app-subtitle">NBA player props dashboard for points, rebounds, and assists</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# TEAM LOOKUPS
# =========================
TEAM_NAME_TO_ABBR = {
    "atlanta hawks": "ATL",
    "boston celtics": "BOS",
    "brooklyn nets": "BKN",
    "charlotte hornets": "CHA",
    "chicago bulls": "CHI",
    "cleveland cavaliers": "CLE",
    "dallas mavericks": "DAL",
    "denver nuggets": "DEN",
    "detroit pistons": "DET",
    "golden state warriors": "GSW",
    "houston rockets": "HOU",
    "indiana pacers": "IND",
    "los angeles clippers": "LAC",
    "la clippers": "LAC",
    "los angeles lakers": "LAL",
    "memphis grizzlies": "MEM",
    "miami heat": "MIA",
    "milwaukee bucks": "MIL",
    "minnesota timberwolves": "MIN",
    "new orleans pelicans": "NOP",
    "new york knicks": "NYK",
    "oklahoma city thunder": "OKC",
    "orlando magic": "ORL",
    "philadelphia 76ers": "PHI",
    "phoenix suns": "PHX",
    "portland trail blazers": "POR",
    "sacramento kings": "SAC",
    "san antonio spurs": "SAS",
    "toronto raptors": "TOR",
    "utah jazz": "UTA",
    "washington wizards": "WAS",
}

NBA_TEAMS = teams.get_teams()
TEAM_ABBR_TO_ID = {t["abbreviation"]: t["id"] for t in NBA_TEAMS}


def team_name_to_abbr(name: str):
    if not isinstance(name, str):
        return None
    return TEAM_NAME_TO_ABBR.get(name.strip().lower())


# =========================
# PLAYER LOOKUP
# =========================
NBA_PLAYERS = players.get_players()
PLAYER_NAME_TO_ID = {p["full_name"].lower(): p["id"] for p in NBA_PLAYERS}


def normalize_player_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return (
        name.lower()
        .replace(".", "")
        .replace("'", "")
        .replace("-", " ")
        .replace(" jr", "")
        .replace(" sr", "")
        .replace(" iii", "")
        .replace(" ii", "")
        .strip()
    )


def player_name_to_id(name: str):
    if not isinstance(name, str):
        return None

    exact = PLAYER_NAME_TO_ID.get(name.lower())
    if exact:
        return exact

    normalized_input = normalize_player_name(name)

    for p in NBA_PLAYERS:
        if normalize_player_name(p["full_name"]) == normalized_input:
            return p["id"]

    for p in NBA_PLAYERS:
        if normalized_input in normalize_player_name(p["full_name"]):
            return p["id"]

    return None


# =========================
# ODDS API HELPERS
# =========================
def api_get(url: str, params=None):
    r = requests.get(url, params=params, timeout=30)

    try:
        data = r.json()
    except Exception:
        st.error("The Odds API response was not valid JSON.")
        st.code(r.text)
        return None, r.status_code

    return data, r.status_code


@st.cache_data(ttl=300)
def get_events():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/events"
    params = {"apiKey": ODDS_API_KEY}

    data, status = api_get(url, params=params)

    if status != 200:
        st.error(f"Events endpoint returned status code {status}.")
        if data is not None:
            st.json(data)
        return []

    if not isinstance(data, list):
        st.error("Events endpoint did not return a list.")
        st.json(data)
        return []

    return data


@st.cache_data(ttl=300)
def get_event_props(event_id: str):
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
    }

    data, status = api_get(url, params=params)

    if status != 200:
        return {"error": True, "status": status, "data": data}

    return {"error": False, "data": data}


@st.cache_data(ttl=300)
def get_props():
    events = get_events()

    if not events:
        return pd.DataFrame()

    stat_map = {
        "player_points": "PTS",
        "player_rebounds": "REB",
        "player_assists": "AST",
    }

    rows = []
    skipped_events = []

    for event in events:
        if not isinstance(event, dict):
            continue

        event_id = event.get("id")
        home_team_name = event.get("home_team")
        away_team_name = event.get("away_team")
        commence_time = event.get("commence_time")

        if not event_id:
            continue

        result = get_event_props(event_id)
        time.sleep(ODDS_SLEEP)

        if result.get("error"):
            skipped_events.append(
                {
                    "event_id": event_id,
                    "home_team": home_team_name,
                    "away_team": away_team_name,
                    "status": result.get("status"),
                    "response": result.get("data"),
                }
            )
            continue

        data = result.get("data")
        if not isinstance(data, dict):
            continue

        bookmakers = data.get("bookmakers", [])
        home_abbr = team_name_to_abbr(home_team_name)
        away_abbr = team_name_to_abbr(away_team_name)

        for book in bookmakers:
            if not isinstance(book, dict):
                continue

            book_name = book.get("title", book.get("key"))

            for market in book.get("markets", []):
                if not isinstance(market, dict):
                    continue

                market_key = market.get("key")
                stat_type = stat_map.get(market_key)

                if stat_type is None:
                    continue

                for outcome in market.get("outcomes", []):
                    if not isinstance(outcome, dict):
                        continue

                    if outcome.get("name") != "Over":
                        continue

                    player_name = outcome.get("description")
                    line = outcome.get("point")

                    if player_name is None or line is None:
                        continue

                    rows.append(
                        {
                            "PLAYER_NAME": player_name,
                            "STAT": stat_type,
                            "LINE": float(line),
                            "HOME_TEAM": home_abbr,
                            "AWAY_TEAM": away_abbr,
                            "HOME_TEAM_NAME": home_team_name,
                            "AWAY_TEAM_NAME": away_team_name,
                            "COMMENCE_TIME": commence_time,
                            "BOOK": book_name,
                        }
                    )

    if skipped_events:
        with st.expander("Skipped events / API responses"):
            st.json(skipped_events)

    if not rows:
        st.warning("No player props were returned.")
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    return (
        df.groupby(["PLAYER_NAME", "STAT"], as_index=False)
        .agg(
            LINE=("LINE", "median"),
            BOOK_COUNT=("BOOK", "nunique"),
            HOME_TEAM=("HOME_TEAM", "first"),
            AWAY_TEAM=("AWAY_TEAM", "first"),
            HOME_TEAM_NAME=("HOME_TEAM_NAME", "first"),
            AWAY_TEAM_NAME=("AWAY_TEAM_NAME", "first"),
            COMMENCE_TIME=("COMMENCE_TIME", "first"),
        )
    )


# =========================
# NBA GAME LOGS
# =========================
@st.cache_data(ttl=43200)
def get_game_log(player_id: int):
    time.sleep(REQUEST_SLEEP)

    gl = playergamelog.PlayerGameLog(
        player_id=player_id,
        season=SEASON,
        season_type_all_star="Regular Season",
    )

    df = gl.get_data_frames()[0]

    if df.empty:
        return df

    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df = df.sort_values("GAME_DATE", ascending=False).reset_index(drop=True)

    if "MIN" in df.columns:
        df["MIN"] = pd.to_numeric(df["MIN"], errors="coerce")

    return df


@st.cache_data(ttl=21600)
def get_team_game_log(team_id: int):
    time.sleep(REQUEST_SLEEP)

    gl = teamgamelog.TeamGameLog(
        team_id=team_id,
        season=SEASON,
        season_type_all_star="Regular Season",
    )

    df = gl.get_data_frames()[0]

    if df.empty:
        return df

    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df = df.sort_values("GAME_DATE", ascending=False).reset_index(drop=True)
    return df


# =========================
# INJURY HELPERS
# =========================
def build_injury_map_from_selections(
    out_players,
    questionable_players,
    doubtful_players,
    probable_players,
):
    injury_map = {}

    status_dict = {
        "out": out_players or [],
        "questionable": questionable_players or [],
        "doubtful": doubtful_players or [],
        "probable": probable_players or [],
    }

    for status, plist in status_dict.items():
        for player in plist:
            pid = player_name_to_id(player)
            if pid is None:
                continue

            try:
                log = get_game_log(pid)
            except Exception:
                continue

            if log.empty:
                continue

            team = infer_team_from_log(log)
            if not team:
                continue

            if team not in injury_map:
                injury_map[team] = {
                    "out": [],
                    "questionable": [],
                    "doubtful": [],
                    "probable": [],
                }

            if player not in injury_map[team][status]:
                injury_map[team][status].append(player)

    return injury_map


def injury_adjustment(team_injuries, stat):
    out_count = len(team_injuries.get("out", []))
    questionable_count = len(team_injuries.get("questionable", []))
    doubtful_count = len(team_injuries.get("doubtful", []))
    probable_count = len(team_injuries.get("probable", []))

    if stat == "PTS":
        volume_boost = (0.014 * out_count) + (0.008 * doubtful_count)
        efficiency_penalty = (0.006 * out_count) + (0.003 * doubtful_count)
        uncertainty_penalty = 0.004 * questionable_count
        returning_penalty = 0.010 * probable_count
    elif stat == "AST":
        volume_boost = (0.010 * out_count) + (0.006 * doubtful_count)
        efficiency_penalty = (0.010 * out_count) + (0.004 * doubtful_count)
        uncertainty_penalty = 0.004 * questionable_count
        returning_penalty = 0.008 * probable_count
    else:
        volume_boost = (0.012 * out_count) + (0.007 * doubtful_count)
        efficiency_penalty = (0.003 * out_count) + (0.002 * doubtful_count)
        uncertainty_penalty = 0.003 * questionable_count
        returning_penalty = 0.006 * probable_count

    net_projection_multiplier = 1 + volume_boost - efficiency_penalty - uncertainty_penalty - returning_penalty
    net_projection_multiplier = max(0.90, min(1.08, net_projection_multiplier))

    hidden_gem_adjustment = (
        (volume_boost * 100 * 0.9)
        - (efficiency_penalty * 100 * 0.6)
        - (questionable_count * 1.2)
        - (probable_count * 1.5)
    )
    hidden_gem_adjustment = round(max(-8.0, min(8.0, hidden_gem_adjustment)), 1)

    note_parts = []
    if out_count:
        note_parts.append(f"{out_count} out")
    if doubtful_count:
        note_parts.append(f"{doubtful_count} doubtful")
    if questionable_count:
        note_parts.append(f"{questionable_count} questionable")
    if probable_count:
        note_parts.append(f"{probable_count} probable")

    if not note_parts:
        note = "No major injury context"
    else:
        direction = "slight boost" if hidden_gem_adjustment > 0.5 else "slight downgrade" if hidden_gem_adjustment < -0.5 else "mixed impact"
        note = f"{', '.join(note_parts)} • {direction}"

    return round(net_projection_multiplier, 4), hidden_gem_adjustment, note


# =========================
# MODEL HELPERS
# =========================
def stat_average(df: pd.DataFrame, stat: str, n: int):
    if df.empty or stat not in df.columns:
        return math.nan
    vals = pd.to_numeric(df.head(n)[stat], errors="coerce").dropna()
    if vals.empty:
        return math.nan
    return round(vals.mean(), 2)


def stat_hit_rate(df: pd.DataFrame, stat: str, line: float, n: int):
    if df.empty or stat not in df.columns:
        return math.nan
    vals = pd.to_numeric(df.head(n)[stat], errors="coerce").dropna()
    if vals.empty:
        return math.nan
    return round((vals > line).mean() * 100, 1)


def season_average(df: pd.DataFrame, stat: str):
    if df.empty or stat not in df.columns:
        return math.nan
    vals = pd.to_numeric(df[stat], errors="coerce").dropna()
    if vals.empty:
        return math.nan
    return round(vals.mean(), 2)


def season_hit_rate(df: pd.DataFrame, stat: str, line: float):
    if df.empty or stat not in df.columns:
        return math.nan
    vals = pd.to_numeric(df[stat], errors="coerce").dropna()
    if vals.empty:
        return math.nan
    return round((vals > line).mean() * 100, 1)


def minutes_average(df: pd.DataFrame, n: int):
    if df.empty or "MIN" not in df.columns:
        return math.nan
    mins = pd.to_numeric(df.head(n)["MIN"], errors="coerce").dropna()
    if mins.empty:
        return math.nan
    return round(mins.mean(), 2)


def season_minutes_average(df: pd.DataFrame):
    if df.empty or "MIN" not in df.columns:
        return math.nan
    mins = pd.to_numeric(df["MIN"], errors="coerce").dropna()
    if mins.empty:
        return math.nan
    return round(mins.mean(), 2)


def expected_minutes(df: pd.DataFrame):
    l5 = minutes_average(df, 5)
    l10 = minutes_average(df, 10)
    season = season_minutes_average(df)

    if all(pd.isna(v) for v in [l5, l10, season]):
        return math.nan

    l5 = 0 if pd.isna(l5) else l5
    l10 = 0 if pd.isna(l10) else l10
    season = 0 if pd.isna(season) else season

    return round(0.5 * l5 + 0.3 * l10 + 0.2 * season, 2)


def stat_per_minute(df: pd.DataFrame, stat: str):
    if df.empty or stat not in df.columns or "MIN" not in df.columns:
        return math.nan

    vals = pd.to_numeric(df[stat], errors="coerce")
    mins = pd.to_numeric(df["MIN"], errors="coerce")
    temp = pd.DataFrame({"stat": vals, "min": mins}).dropna()
    temp = temp[temp["min"] > 0]

    if temp.empty:
        return math.nan

    return round(temp["stat"].sum() / temp["min"].sum(), 4)


def minutes_based_projection(df: pd.DataFrame, stat: str):
    spm = stat_per_minute(df, stat)
    exp_min = expected_minutes(df)

    if pd.isna(spm) or pd.isna(exp_min):
        return math.nan

    return round(spm * exp_min, 2)


def build_projection(l5_avg: float, l10_avg: float, season_avg: float):
    if any(pd.isna(v) for v in [l5_avg, l10_avg, season_avg]):
        return math.nan
    return round(0.5 * l5_avg + 0.3 * l10_avg + 0.2 * season_avg, 2)


def final_projection(old_projection: float, min_projection: float):
    if pd.isna(old_projection) and pd.isna(min_projection):
        return math.nan
    if pd.isna(old_projection):
        return round(min_projection, 2)
    if pd.isna(min_projection):
        return round(old_projection, 2)
    return round(0.4 * old_projection + 0.6 * min_projection, 2)


def edge_score(edge: float):
    if pd.isna(edge):
        return 50.0
    score = 50 + edge * 10
    return max(0, min(100, round(score, 1)))


def minutes_stability_score(log_df: pd.DataFrame, n: int = 10):
    if log_df.empty or "MIN" not in log_df.columns:
        return 50.0

    mins = pd.to_numeric(log_df.head(n)["MIN"], errors="coerce").dropna()
    if len(mins) < 2:
        return 50.0

    mean = mins.mean()
    std = mins.std()

    if mean == 0 or pd.isna(std):
        return 50.0

    cv = std / mean
    score = 100 - (cv * 100)
    return max(0, min(100, round(score, 1)))


def stat_volatility_penalty(log_df: pd.DataFrame, stat: str, n: int = 10):
    if log_df.empty or stat not in log_df.columns:
        return 0.0

    vals = pd.to_numeric(log_df.head(n)[stat], errors="coerce").dropna()
    if len(vals) < 2:
        return 0.0

    mean = vals.mean()
    std = vals.std()

    if mean == 0 or pd.isna(std):
        return 0.0

    cv = std / mean
    penalty = min(20, cv * 25)
    return round(penalty, 1)


# =========================
# DVP / MATCHUP HELPERS
# =========================
def opponent_team_id(team_abbr: str):
    return TEAM_ABBR_TO_ID.get(team_abbr)


def team_defense_rank_proxy(team_log_df: pd.DataFrame):
    if team_log_df.empty:
        return 15

    sample = team_log_df.head(10).copy()
    wins = (sample["WL"] == "W").sum() if "WL" in sample.columns else 5
    win_pct = wins / max(len(sample), 1)

    if win_pct <= 0.30:
        return 26
    if win_pct <= 0.40:
        return 22
    if win_pct <= 0.50:
        return 18
    if win_pct <= 0.60:
        return 14
    if win_pct <= 0.70:
        return 10
    return 6


def dvp_multiplier_from_rank(rank_proxy: float):
    if pd.isna(rank_proxy):
        return 1.00, "Neutral matchup"
    if rank_proxy >= 26:
        return 1.07, "Elite matchup"
    if rank_proxy >= 21:
        return 1.04, "Strong matchup"
    if rank_proxy >= 16:
        return 1.01, "Slightly favorable matchup"
    if rank_proxy >= 11:
        return 0.99, "Slightly difficult matchup"
    if rank_proxy >= 6:
        return 0.96, "Tough matchup"
    return 0.93, "Very tough matchup"


def dvp_bonus_from_rank(rank_proxy: float):
    if pd.isna(rank_proxy):
        return 0.0
    if rank_proxy >= 26:
        return 5.0
    if rank_proxy >= 21:
        return 3.0
    if rank_proxy >= 16:
        return 1.0
    if rank_proxy >= 11:
        return -1.0
    if rank_proxy >= 6:
        return -3.0
    return -5.0


def opponent_dvp_context(opponent_abbr: str):
    if not opponent_abbr:
        return math.nan, 1.00, 0.0, "Neutral matchup"

    opp_id = opponent_team_id(opponent_abbr)
    if not opp_id:
        return math.nan, 1.00, 0.0, "Neutral matchup"

    try:
        team_log = get_team_game_log(opp_id)
    except Exception:
        return math.nan, 1.00, 0.0, "Neutral matchup"

    rank_proxy = team_defense_rank_proxy(team_log)
    mult, note = dvp_multiplier_from_rank(rank_proxy)
    bonus = dvp_bonus_from_rank(rank_proxy)

    return rank_proxy, mult, bonus, note


def improved_hidden_gem_score(
    l5_hit: float,
    l10_hit: float,
    edge: float,
    minutes_stability: float,
    expected_min: float,
    volatility_penalty: float,
    dvp_bonus: float = 0.0,
):
    l5 = 50.0 if pd.isna(l5_hit) else l5_hit
    l10 = 50.0 if pd.isna(l10_hit) else l10_hit
    m_stab = 50.0 if pd.isna(minutes_stability) else minutes_stability
    e_score = edge_score(edge)

    score = (
        0.22 * l5 +
        0.28 * l10 +
        0.30 * e_score +
        0.20 * m_stab
    )

    score = score - (0 if pd.isna(volatility_penalty) else volatility_penalty)
    score = score + dvp_bonus

    if not pd.isna(expected_min):
        if expected_min < 20:
            score = min(score, 58)
        elif expected_min < 24:
            score = min(score, 68)
        elif expected_min < 28:
            score = min(score, 80)

    return round(max(0, min(100, score)), 1)


def infer_team_from_log(log_df: pd.DataFrame):
    if log_df.empty or "MATCHUP" not in log_df.columns:
        return None
    matchup = str(log_df.iloc[0]["MATCHUP"]).strip()
    return matchup[:3] if len(matchup) >= 3 else None


def get_team_and_opponent(player_team: str, home_team: str, away_team: str):
    if player_team == home_team:
        return player_team, away_team
    if player_team == away_team:
        return player_team, home_team
    return player_team, None


def get_lean(projection: float, line: float, threshold: float = 1.0):
    if pd.isna(projection) or pd.isna(line):
        return "PASS"
    if projection >= line + threshold:
        return "OVER"
    if projection <= line - threshold:
        return "UNDER"
    return "PASS"


# =========================
# BUILD CHEATSHEET
# =========================
def build_cheatsheet(props_df: pd.DataFrame, injury_map: dict):
    if props_df.empty:
        return pd.DataFrame()

    rows = []
    progress_text = st.empty()
    progress_bar = st.progress(0)

    total = len(props_df)

    for i, (_, row) in enumerate(props_df.iterrows(), start=1):
        player = row["PLAYER_NAME"]
        stat = row["STAT"]
        line = row["LINE"]
        home_team = row["HOME_TEAM"]
        away_team = row["AWAY_TEAM"]
        book_count = row["BOOK_COUNT"]

        progress_text.text(f"Processing {i}/{total}: {player} {stat}")
        progress_bar.progress(min(i / total, 1.0))

        player_id = player_name_to_id(player)
        if player_id is None:
            continue

        try:
            log = get_game_log(player_id)
        except Exception:
            continue

        if log.empty:
            continue

        team = infer_team_from_log(log)
        team, opponent = get_team_and_opponent(team, home_team, away_team)

        team_injuries = injury_map.get(team, {
            "out": [],
            "questionable": [],
            "doubtful": [],
            "probable": [],
        })

        l5_hit = stat_hit_rate(log, stat, line, 5)
        l10_hit = stat_hit_rate(log, stat, line, 10)
        season_hit = season_hit_rate(log, stat, line)

        l5_avg = stat_average(log, stat, 5)
        l10_avg = stat_average(log, stat, 10)
        s_avg = season_average(log, stat)

        old_proj = build_projection(l5_avg, l10_avg, s_avg)
        min_proj = minutes_based_projection(log, stat)
        base_projection = final_projection(old_proj, min_proj)

        exp_min = expected_minutes(log)
        min_stability = minutes_stability_score(log, 10)
        volatility_pen = stat_volatility_penalty(log, stat, 10)

        dvp_rank, dvp_mult, dvp_bonus, dvp_note = opponent_dvp_context(opponent)
        proj_mult, gem_adj, injury_note = injury_adjustment(team_injuries, stat)

        projection = (
            round(base_projection * dvp_mult * proj_mult, 2)
            if not pd.isna(base_projection)
            else math.nan
        )

        edge = round(projection - line, 2) if not pd.isna(projection) else math.nan

        hidden_gem = improved_hidden_gem_score(
            l5_hit=l5_hit,
            l10_hit=l10_hit,
            edge=edge,
            minutes_stability=min_stability,
            expected_min=exp_min,
            volatility_penalty=volatility_pen,
            dvp_bonus=dvp_bonus,
        )
        hidden_gem = max(0, min(100, hidden_gem + gem_adj))

        lean = get_lean(projection, line)

        rows.append(
            {
                "PLAYER": player,
                "TEAM": team,
                "OPPONENT": opponent,
                "STAT": stat,
                "LINE": line,
                "BOOK_COUNT": book_count,
                "L5_HIT_RATE": l5_hit,
                "L10_HIT_RATE": l10_hit,
                "SEASON_HIT_RATE": season_hit,
                "L5_AVG": l5_avg,
                "L10_AVG": l10_avg,
                "SEASON_AVG": s_avg,
                "EXPECTED_MIN": exp_min,
                "MIN_STABILITY": min_stability,
                "VOLATILITY_PENALTY": volatility_pen,
                "DVP_RANK": dvp_rank,
                "DVP_NOTE": dvp_note,
                "INJURY_NOTE": injury_note,
                "PROJECTION": projection,
                "EDGE": edge,
                "CONFIDENCE": hidden_gem,
                "LEAN": lean,
            }
        )

    progress_text.empty()
    progress_bar.empty()

    cheatsheet = pd.DataFrame(rows)
    if cheatsheet.empty:
        return cheatsheet

    return cheatsheet.sort_values(
        by=["CONFIDENCE", "EDGE", "L10_HIT_RATE"],
        ascending=[False, False, False]
    ).reset_index(drop=True)


# =========================
# UI HELPERS
# =========================
def format_num(x, decimals=1):
    if pd.isna(x):
        return "-"
    return f"{float(x):.{decimals}f}"


def lean_pill_class(lean: str):
    if lean == "OVER":
        return "pill-over"
    if lean == "UNDER":
        return "pill-under"
    return "pill-pass"


def render_metric_box(label: str, value: str, score: bool = False):
    extra_class = " metric-score" if score else ""
    st.markdown(
        f"""
        <div class="metric-box-wrap">
            <div class="metric-label">{label}</div>
            <div class="metric-value{extra_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_single_card(row, rank_num=None):
    pill_class = lean_pill_class(row["LEAN"])

    with st.container():
        st.markdown('<div class="bet-card">', unsafe_allow_html=True)

        top_left, top_right = st.columns([5, 1])

        with top_left:
            rank_html = f"<span class='rank-badge'>#{rank_num}</span>" if rank_num is not None else ""
            st.markdown(
                f"""
                <div class="row-head">
                    {rank_html}
                    <div>
                        <div class="player-name">{row['PLAYER']}</div>
                        <div class="meta-line">{row['TEAM']} vs {row['OPPONENT']}</div>
                    </div>
                </div>
                <div class="pill-row">
                    <span class="pill pill-stat">{row['STAT']}</span>
                    <span class="pill {pill_class}">{row['LEAN']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with top_right:
            st.markdown(
                f"""
                <div class="card-linebox">
                    <div class="line-label">Line</div>
                    <div class="line-value">{format_num(row['LINE'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        metric_cols_1 = st.columns(4)
        with metric_cols_1[0]:
            render_metric_box("Projection", format_num(row["PROJECTION"]))
        with metric_cols_1[1]:
            render_metric_box("L10 Avg", format_num(row["L10_AVG"]))
        with metric_cols_1[2]:
            render_metric_box("L10 Hit Rate", f"{format_num(row['L10_HIT_RATE'], 0)}%")
        with metric_cols_1[3]:
            render_metric_box("Season Hit Rate", f"{format_num(row['SEASON_HIT_RATE'], 0)}%")

        metric_cols_2 = st.columns(3)
        with metric_cols_2[0]:
            render_metric_box("Hidden Gem", f"{int(round(row['CONFIDENCE'], 0))}%", score=True)
        with metric_cols_2[1]:
            render_metric_box("DVP", row["DVP_NOTE"])
        with metric_cols_2[2]:
            render_metric_box("Injury Context", row.get("INJURY_NOTE", "No major injury context"))

        st.markdown('</div>', unsafe_allow_html=True)


def render_bet_cards(df: pd.DataFrame, lean_type: str):
    subset = df[df["LEAN"] == lean_type].copy()

    if lean_type == "OVER":
        subset = subset.sort_values(
            by=["EDGE", "CONFIDENCE", "L10_HIT_RATE"],
            ascending=[False, False, False]
        ).head(5)
    else:
        subset = subset.sort_values(
            by=["EDGE", "CONFIDENCE", "L10_HIT_RATE"],
            ascending=[True, False, True]
        ).head(5)

    if subset.empty:
        st.info(f"No {lean_type} plays matched the current filters.")
        return

    for _, row in subset.iterrows():
        render_single_card(row)


def render_full_cheatsheet_cards(df: pd.DataFrame):
    if df.empty:
        st.info("No rows to display.")
        return

    ranked_df = df.head(50).copy()

    for i in range(0, len(ranked_df), 2):
        cols = st.columns(2)

        for col_idx, row_idx in enumerate([i, i + 1]):
            if row_idx >= len(ranked_df):
                continue

            row = ranked_df.iloc[row_idx]

            with cols[col_idx]:
                render_single_card(row, rank_num=row_idx + 1)


# =========================
# PREVIEW DATA FOR CONTROLS
# =========================
props_preview = get_props()

player_options_preview = []
injury_player_options = []

if not props_preview.empty:
    player_options_preview = sorted(props_preview["PLAYER_NAME"].dropna().unique().tolist())
    injury_player_options = player_options_preview.copy()


# =========================
# CENTERED CONTROLS
# =========================
left_spacer, center_col, right_spacer = st.columns([1, 5, 1])

with center_col:
    st.markdown('<div class="control-card">', unsafe_allow_html=True)

    top_controls = st.columns(4)

    with top_controls[0]:
        view_mode = st.selectbox(
            "View",
            ["All", "Best Overs", "Best Unders", "Full Cheatsheet"],
            index=0,
            key="view_mode_main",
        )

    with top_controls[1]:
        stat_filter = st.selectbox(
            "Filter stat",
            ["ALL", "PTS", "REB", "AST"],
            index=0,
            key="stat_filter_main",
        )

    filtered_player_preview = player_options_preview
    if not props_preview.empty and stat_filter != "ALL":
        filtered_player_preview = sorted(
            props_preview[props_preview["STAT"] == stat_filter]["PLAYER_NAME"].dropna().unique().tolist()
        )

    with top_controls[2]:
        selected_player = st.selectbox(
            "Search player",
            options=["All Players"] + filtered_player_preview,
            index=0,
            key="selected_player_main",
        )

    with top_controls[3]:
        run_model = st.button("Run Selected View", use_container_width=True)

    with st.expander("Pregame Injuries", expanded=False):
        injury_cols_1 = st.columns(2)
        injury_cols_2 = st.columns(2)

        with injury_cols_1[0]:
            injured_out = st.multiselect(
                "Out",
                options=injury_player_options,
                default=[],
                placeholder="Search players...",
                key="injured_out",
            )

        with injury_cols_1[1]:
            injured_questionable = st.multiselect(
                "Questionable",
                options=injury_player_options,
                default=[],
                placeholder="Search players...",
                key="injured_questionable",
            )

        with injury_cols_2[0]:
            injured_doubtful = st.multiselect(
                "Doubtful",
                options=injury_player_options,
                default=[],
                placeholder="Search players...",
                key="injured_doubtful",
            )

        with injury_cols_2[1]:
            injured_probable = st.multiselect(
                "Probable / Returning",
                options=injury_player_options,
                default=[],
                placeholder="Search players...",
                key="injured_probable",
            )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# MAIN
# =========================
if run_model:
    props_df = get_props()

    if props_df.empty:
        st.warning("No props returned.")
        st.stop()

    if stat_filter != "ALL":
        props_df = props_df[props_df["STAT"] == stat_filter].reset_index(drop=True)

    if selected_player != "All Players":
        props_df = props_df[props_df["PLAYER_NAME"] == selected_player].reset_index(drop=True)

    if props_df.empty:
        st.warning("No props matched your filters.")
        st.stop()

    injury_map = build_injury_map_from_selections(
        injured_out,
        injured_questionable,
        injured_doubtful,
        injured_probable,
    )

    cheatsheet = build_cheatsheet(props_df, injury_map)

    if cheatsheet.empty:
        st.warning("No data returned after processing.")
        st.stop()

    if view_mode == "Best Overs":
        st.markdown('<div class="section-title">🔥 Best Overs (Top 5)</div>', unsafe_allow_html=True)
        render_bet_cards(cheatsheet, "OVER")

    elif view_mode == "Best Unders":
        st.markdown('<div class="section-title">❄️ Best Unders (Top 5)</div>', unsafe_allow_html=True)
        render_bet_cards(cheatsheet, "UNDER")

    elif view_mode == "Full Cheatsheet":
        st.markdown('<div class="section-title">📋 Full Cheatsheet (ranked)</div>', unsafe_allow_html=True)
        render_full_cheatsheet_cards(cheatsheet)

    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section-title">🔥 Best Overs (Top 5)</div>', unsafe_allow_html=True)
            render_bet_cards(cheatsheet, "OVER")

        with col2:
            st.markdown('<div class="section-title">❄️ Best Unders (Top 5)</div>', unsafe_allow_html=True)
            render_bet_cards(cheatsheet, "UNDER")

        st.markdown('<div class="section-title">📋 Full Cheatsheet (ranked)</div>', unsafe_allow_html=True)
        render_full_cheatsheet_cards(cheatsheet)

    csv = cheatsheet.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="rinas_cheatsheet.csv",
        mime="text/csv",
    )

else:
    st.info("Pick your filters, add injuries in the dropdowns if needed, then click Run Selected View.")
