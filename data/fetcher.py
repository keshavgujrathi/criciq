import requests
from typing import List, Dict, Any


class CricbuzzFetcher:
    def __init__(self, rapidapi_key: str):
        self.rapidapi_key = rapidapi_key
        self.headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
        }
        self.base_url = "https://cricbuzz-cricket.p.rapidapi.com"

    def get_live_matches(self) -> List[Dict[str, Any]]:
        try:
            all_matches = []
            seen_ids = set()
            
            # Fetch live matches
            live_url = f"{self.base_url}/matches/v1/live"
            live_response = requests.get(live_url, headers=self.headers)
            live_response.raise_for_status()
            live_data = live_response.json()
            
            for match in live_data.get("typeMatches", []):
                for series_matches in match.get("seriesMatches", []):
                    series_wrapper = series_matches.get("seriesAdWrapper")
                    if not series_wrapper:
                        continue
                    
                    for match_info in series_wrapper.get("matches", []):
                        match_data = match_info.get("matchInfo", {})
                        if not match_data:
                            continue
                        
                        match_id = match_data.get("matchId")
                        if not match_id or match_id in seen_ids:
                            continue
                        
                        team1 = match_data.get("team1", {})
                        team2 = match_data.get("team2", {})
                        team1_name = team1.get("teamName", "N/A")
                        team2_name = team2.get("teamName", "N/A")
                        
                        match_title = f"{team1_name} vs {team2_name}"
                        
                        all_matches.append({
                            "match_id": match_id,
                            "match_title": match_title,
                            "status": match_data.get("status", "N/A"),
                            "series": match_data.get("seriesName", "N/A")
                        })
                        seen_ids.add(match_id)
            
            # Fetch recent matches if no live matches or to supplement
            recent_url = f"{self.base_url}/matches/v1/recent"
            recent_response = requests.get(recent_url, headers=self.headers)
            recent_response.raise_for_status()
            recent_data = recent_response.json()
            
            for match in recent_data.get("typeMatches", []):
                for series_matches in match.get("seriesMatches", []):
                    series_wrapper = series_matches.get("seriesAdWrapper")
                    if not series_wrapper:
                        continue
                    
                    for match_info in series_wrapper.get("matches", []):
                        match_data = match_info.get("matchInfo", {})
                        if not match_data:
                            continue
                        
                        match_id = match_data.get("matchId")
                        if not match_id or match_id in seen_ids:
                            continue
                        
                        team1 = match_data.get("team1", {})
                        team2 = match_data.get("team2", {})
                        team1_name = team1.get("teamName", "N/A")
                        team2_name = team2.get("teamName", "N/A")
                        
                        match_title = f"{team1_name} vs {team2_name}"
                        
                        all_matches.append({
                            "match_id": match_id,
                            "match_title": match_title,
                            "status": match_data.get("status", "N/A"),
                            "series": match_data.get("seriesName", "N/A")
                        })
                        seen_ids.add(match_id)
            
            return all_matches
        except Exception as e:
            raise RuntimeError(f"Failed to fetch live matches: {str(e)}")

    def get_match_scorecard(self, match_id: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/mcenter/v1/{match_id}/hscard"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch match scorecard: {str(e)}")

    def get_match_commentary(self, match_id: str) -> List[str]:
        try:
            # First try live commentary endpoint
            url = f"{self.base_url}/mcenter/v1/{match_id}/comm"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            commentary_list = data.get("commentaryList", [])
            
            if commentary_list:
                commentary_texts = []
                for item in commentary_list[-25:]:
                    comm_text = item.get("commtxt", "")
                    if comm_text and comm_text.strip():
                        commentary_texts.append(comm_text.strip())
                
                return commentary_texts if commentary_texts else ["No commentary available"]
            
            # Fallback: try to get over summaries from scorecard
            scorecard_url = f"{self.base_url}/mcenter/v1/{match_id}/hscard"
            scorecard_response = requests.get(scorecard_url, headers=self.headers)
            scorecard_response.raise_for_status()
            
            scorecard_data = scorecard_response.json()
            innings = scorecard_data.get("scorecard", [])
            
            over_summaries = []
            for inning in innings:
                over_summary = inning.get("overSummaryList", [])
                for over in over_summary[-10:]:  # Last 10 overs
                    summary = over.get("overSummary", "")
                    if summary and summary.strip():
                        over_summaries.append(f"Over {over.get('overNum', 'N/A')}: {summary}")
            
            if over_summaries:
                return over_summaries
            
            return ["Match completed - no live commentary available. Analysis based on final scorecard."]
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch match commentary: {str(e)}")

    def get_match_info(self, match_id: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/mcenter/v1/{match_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            venue_info = data.get("venueinfo", {})
            venue = venue_info.get("ground", "N/A") if isinstance(venue_info, dict) else "N/A"
            city = venue_info.get("city", "N/A") if isinstance(venue_info, dict) else "N/A"
            
            toss_status = data.get("tossstatus", "N/A")
            
            return {
                "venue": f"{venue}, {city}" if city != "N/A" and venue != "N/A" else venue or "N/A",
                "match_type": data.get("matchtype", "N/A"),
                "toss": toss_status,
                "series": data.get("seriesname", "N/A")
            }
        except Exception as e:
            raise RuntimeError(f"Failed to fetch match info: {str(e)}")

    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/stats/v1/player/{player_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch player stats: {str(e)}")
