from typing import List, Dict, Any


def format_scorecard(scorecard_json: Dict[str, Any]) -> str:
    try:
        output = []
        
        innings = scorecard_json.get("scorecard", [])
        
        for inning in innings:
            team_name = inning.get("batteamname", "N/A")
            score = inning.get("score", 0)
            wickets = inning.get("wickets", 0)
            overs = inning.get("overs", 0)
            run_rate = inning.get("runrate", 0)
            
            output.append(f"{team_name}: {score}/{wickets} ({overs} overs) RR: {run_rate}")
            
            batsmen = inning.get("batsman", [])
            current_batsmen = []
            
            for batsman in batsmen[:2]:
                if batsman.get("outdec") == "not out" or batsman.get("inmatchchange") == "IN":
                    name = batsman.get("name", "N/A")
                    runs = batsman.get("runs", 0)
                    balls = batsman.get("balls", 0)
                    sr = batsman.get("strkrate", "0")
                    current_batsmen.append(f"{name}: {runs}({balls}) SR: {sr}")
            
            if current_batsmen:
                output.append(f"Current Batsmen:")
                output.extend(current_batsmen)
            
            bowlers = inning.get("bowler", [])
            current_bowlers = []
            
            for bowler in bowlers[:3]:
                if bowler.get("overs", "0") != "0":
                    name = bowler.get("name", "N/A")
                    overs = bowler.get("overs", "0")
                    runs = bowler.get("runs", 0)
                    wickets = bowler.get("wickets", 0)
                    econ = bowler.get("economy", "0")
                    current_bowlers.append(f"{name}: {overs} ov, {runs} runs, {wickets} wkts, Econ: {econ}")
            
            if current_bowlers:
                output.append(f"Current Bowlers:")
                output.extend(current_bowlers)
            
            output.append("")
        
        return "\n".join(output).strip()
    except Exception:
        return "Error formatting scorecard"


def format_commentary(commentary_list: List[str]) -> str:
    try:
        limited_commentary = commentary_list[-20:]
        numbered_commentary = []
        
        for i, text in enumerate(limited_commentary, 1):
            numbered_commentary.append(f"{i}. {text}")
        
        return "\n".join(numbered_commentary)
    except Exception:
        return "Error formatting commentary"


def format_match_context(match_info: Dict[str, Any]) -> str:
    try:
        venue = match_info.get("venue", "N/A")
        match_type = match_info.get("match_type", "N/A")
        series_name = match_info.get("series", "N/A")
        toss = match_info.get("toss", "N/A")
        
        context_parts = [
            f"Match: {series_name} - {match_type}",
            f"Venue: {venue}",
            f"Toss: {toss}"
        ]
        
        return " | ".join(context_parts)
    except Exception:
        return "Error formatting match context"


def format_full_match_data(scorecard: Dict[str, Any], commentary: List[str], match_info: Dict[str, Any], match_title: str) -> Dict[str, str]:
    return {
        "match_title": match_title,
        "scorecard_str": format_scorecard(scorecard),
        "commentary_str": format_commentary(commentary),
        "context_str": format_match_context(match_info)
    }


def format_player_stats(player_json: Dict[str, Any]) -> str:
    try:
        stats = []
        
        batting_stats = player_json.get("battingStats", {})
        if batting_stats:
            avg = batting_stats.get("average", "N/A")
            recent_innings = batting_stats.get("recentInnings", [])
            
            stats.append(f"Batting Average: {avg}")
            
            if recent_innings:
                recent_scores = [inn.get("runs", "0") for inn in recent_innings[-5:]]
                stats.append(f"Recent 5 innings: {', '.join(recent_scores)}")
        
        bowling_stats = player_json.get("bowlingStats", {})
        if bowling_stats:
            avg = bowling_stats.get("average", "N/A")
            stats.append(f"Bowling Average: {avg}")
        
        return " | ".join(stats) if stats else "No stats available"
    except Exception:
        return "Error formatting player stats"
