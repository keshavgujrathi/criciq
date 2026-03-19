import streamlit as st
import os
import time
from dotenv import load_dotenv
from data.fetcher import CricbuzzFetcher
from data.formatter import format_full_match_data, format_player_stats
from engine.prompt_loader import load_prompt, fill_template, list_prompt_versions
from engine.llm_client import GroqClient
from engine.validator import run_full_validation

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="CricIQ", 
    page_icon="🏏", 
    layout="wide"
)

# Initialize cached resources
@st.cache_resource
def init_fetcher():
    key = os.getenv("RAPIDAPI_KEY")
    if not key:
        try:
            key = st.secrets["RAPIDAPI_KEY"]
        except:
            raise RuntimeError("RAPIDAPI_KEY not found in environment or secrets")
    return CricbuzzFetcher(key)

@st.cache_resource
def init_llm_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        try:
            key = st.secrets["GROQ_API_KEY"]
        except:
            raise RuntimeError("GROQ_API_KEY not found in environment or secrets")
    return GroqClient(key)

@st.cache_data(ttl=120)
def get_matches():
    """Get live matches with 2-minute cache."""
    fetcher = init_fetcher()
    return fetcher.get_live_matches()

@st.cache_data(ttl=120)
def get_match_data(match_id, match_title):
    fetcher = init_fetcher()
    scorecard = fetcher.get_match_scorecard(match_id)
    commentary = fetcher.get_match_commentary(match_id)
    match_info = fetcher.get_match_info(match_id)
    return format_full_match_data(scorecard, commentary, match_info, match_title)

def main():
    st.title("CricIQ")
    st.caption("AI Cricket Intelligence")
    
    # Initialize clients
    fetcher = init_fetcher()
    llm_client = init_llm_client()
    
    # Sidebar
    with st.sidebar:
        st.header("Match Selection")
        
        # Refresh button
        if st.button("🔄 Refresh Matches"):
            get_matches.clear()
            get_match_data.clear()
            st.rerun()
        
        # Get matches
        try:
            matches = get_matches()
            if not matches:
                st.warning("No matches available")
                return
            
            # Match selection
            match_options = {
                i: f"{match['match_title']} — {match['status']}" 
                for i, match in enumerate(matches)
            }
            
            selected_idx = st.selectbox(
                "Select Match",
                options=list(match_options.keys()),
                format_func=lambda x: match_options[x]
            )
            
            if selected_idx is not None:
                selected_match = matches[selected_idx]
                st.caption(f"**{selected_match['series']}**")
                
                # Store in session state
                st.session_state.selected_match = selected_match
                
        except Exception as e:
            st.error(f"Failed to load matches: {str(e)}")
            return
    
    # Check if match is selected
    if 'selected_match' not in st.session_state:
        st.info("Select a match from the sidebar to begin analysis")
        return
    
    selected_match = st.session_state.selected_match
    
    # Get match data
    try:
        match_data = get_match_data(
            selected_match['match_id'],
            selected_match['match_title']
        )
    except Exception as e:
        st.error(f"Failed to load match data: {str(e)}")
        return
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["Match Analyst", "Player Intel", "Tactical Predictor"])
    
    with tab1:
        st.header("Match Analyst")
        
        # Display current match info
        col1, col2 = st.columns([2, 1])
        with col1:
            st.code(match_data['scorecard_str'], language=None)
        with col2:
            st.caption("Match Context")
            st.write(match_data['context_str'])
        
        # Prompt version selection
        versions = list_prompt_versions('match_analyst')
        if versions:
            selected_version = st.selectbox(
                "Version",
                options=versions,
                index=versions.index('v1') if 'v1' in versions else 0,
                format_func=lambda x: f"Version: {x}"
            )
            
            compare_versions = st.checkbox("Compare Versions")
            
            # Analyse button
            if st.button("Analyse", key="match_analyse"):
                with st.spinner("Analyzing match..."):
                    try:
                        if compare_versions and 'v2' in versions:
                            # Load both versions with identical data
                            prompt_v1 = load_prompt('match_analyst', 'v1')
                            prompt_v2 = load_prompt('match_analyst', 'v2')
                            
                            system_prompt_v1, user_prompt_v1 = fill_template(prompt_v1, **match_data)
                            system_prompt_v2, user_prompt_v2 = fill_template(prompt_v2, **match_data)
                            
                            # Get responses and times
                            start_time_v1 = time.time()
                            response_v1 = llm_client.complete(
                                system_prompt_v1, user_prompt_v1, 
                                prompt_v1['model'], prompt_v1['temperature']
                            )
                            response_time_v1 = (time.time() - start_time_v1) * 1000
                            
                            start_time_v2 = time.time()
                            response_v2 = llm_client.complete(
                                system_prompt_v2, user_prompt_v2, 
                                prompt_v2['model'], prompt_v2['temperature']
                            )
                            response_time_v2 = (time.time() - start_time_v2) * 1000
                            
                            # Display side by side
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown("### Version 1")
                                st.markdown(response_v1)
                                
                                # Validation for v1
                                context_text = match_data['scorecard_str'] + match_data['context_str']
                                validation_v1 = run_full_validation(response_v1, context_text, 'match_analyst')
                                
                                with st.expander("Output Validation"):
                                    if validation_v1['compliant']:
                                        st.success("Format compliant")
                                    else:
                                        st.error(f"Missing sections: {validation_v1['missing']}")
                                    
                                    if validation_v1['risk_flag']:
                                        st.warning(f"Hallucination risk flagged — {len(validation_v1['numbers_ungrounded'])} ungrounded numbers detected")
                                    else:
                                        st.success("No hallucination risk detected")
                                
                                st.metric("Response Time", f"{response_time_v1:.0f} ms")
                            
                            with col_b:
                                st.markdown("### Version 2")
                                st.markdown(response_v2)
                                
                                # Validation for v2
                                validation_v2 = run_full_validation(response_v2, context_text, 'match_analyst')
                                
                                with st.expander("Output Validation"):
                                    if validation_v2['compliant']:
                                        st.success("Format compliant")
                                    else:
                                        st.error(f"Missing sections: {validation_v2['missing']}")
                                    
                                    if validation_v2['risk_flag']:
                                        st.warning(f"Hallucination risk flagged — {len(validation_v2['numbers_ungrounded'])} ungrounded numbers detected")
                                    else:
                                        st.success("No hallucination risk detected")
                                
                                st.metric("Response Time", f"{response_time_v2:.0f} ms")
                        else:
                            # Single version
                            start_time = time.time()
                            prompt = load_prompt('match_analyst', selected_version)
                            system_prompt, user_prompt = fill_template(prompt, **match_data)
                            
                            response = llm_client.complete(
                                system_prompt, user_prompt, 
                                prompt['model'], prompt['temperature']
                            )
                            response_time = (time.time() - start_time) * 1000
                            
                            st.markdown(response)
                            
                            # Validation
                            context_text = match_data['scorecard_str'] + match_data['context_str']
                            validation = run_full_validation(response, context_text, 'match_analyst')
                            
                            with st.expander("Output Validation"):
                                if validation['compliant']:
                                    st.success("Format compliant")
                                else:
                                    st.error(f"Missing sections: {validation['missing']}")
                                
                                if validation['risk_flag']:
                                    st.warning(f"Hallucination risk flagged — {len(validation['numbers_ungrounded'])} ungrounded numbers detected")
                                else:
                                    st.success("No hallucination risk detected")
                            
                            # Metrics
                            metric_col1, metric_col2, metric_col3 = st.columns(3)
                            with metric_col1:
                                st.metric("Model", prompt['model'])
                            with metric_col2:
                                st.metric("Prompt Version", selected_version)
                            with metric_col3:
                                st.metric("Response Time", f"{response_time:.0f} ms")
                    
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
    
    with tab2:
        st.header("Player Intelligence")
        
        # Player inputs
        col1, col2 = st.columns([2, 1])
        with col1:
            player_name = st.text_input("Enter player name")
            player_id = st.text_input(
                "Player ID (from Cricbuzz)", 
                help="Find this in the Cricbuzz URL for the player's profile page"
            )
        with col2:
            st.caption("Current Match Context")
            st.code(match_data['scorecard_str'], language=None)
        
        # Analyse button
        if st.button("Analyse Player", key="player_analyse"):
            if not player_name and not player_id:
                st.error("Please enter either player name or player ID")
                return
            
            with st.spinner("Analyzing player..."):
                try:
                    # Get player stats
                    if player_id:
                        player_stats = fetcher.get_player_stats(player_id)
                    else:
                        st.warning("Player ID required for stats lookup")
                        return
                    
                    player_stats_str = format_player_stats(player_stats)
                    
                    # Load and fill prompt
                    prompt = load_prompt('player_intel', 'v1')
                    prompt_data = {
                        'match_title': match_data['match_title'],
                        'context_str': match_data['context_str'],
                        'scorecard_str': match_data['scorecard_str'],
                        'player_name': player_name,
                        'player_stats_str': player_stats_str
                    }
                    
                    system_prompt, user_prompt = fill_template(prompt, **prompt_data)
                    
                    # Get response
                    response = llm_client.complete(
                        system_prompt, user_prompt, 
                        prompt['model'], prompt['temperature']
                    )
                    
                    st.markdown(response)
                    
                    # Metrics
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    with metric_col1:
                        st.metric("Model", prompt['model'])
                    with metric_col2:
                        st.metric("Prompt Version", 'v1')
                    with metric_col3:
                        st.metric("Player", player_name)
                
                except Exception as e:
                    st.error(f"Player analysis failed: {str(e)}")
    
    with tab3:
        st.header("Tactical Predictor")
        
        # Display current match info
        col1, col2 = st.columns([2, 1])
        with col1:
            st.code(match_data['scorecard_str'], language=None)
        with col2:
            st.caption("Match Context")
            st.write(match_data['context_str'])
        
        # Prompt version selection
        versions = list_prompt_versions('tactical')
        if versions:
            selected_version = st.selectbox(
                "Version",
                options=versions,
                index=0,
                format_func=lambda x: f"Version: {x}"
            )
        
        # Analyse button
        if st.button("Analyse Tactics", key="tactical_analyse"):
            with st.spinner("Analyzing tactics..."):
                start_time = time.time()
                
                try:
                    prompt = load_prompt('tactical', selected_version)
                    system_prompt, user_prompt = fill_template(prompt, **match_data)
                    
                    response = llm_client.complete(
                        system_prompt, user_prompt, 
                        prompt['model'], prompt['temperature']
                    )
                    
                    st.markdown(response)
                    
                    # Validation
                    context_text = match_data['scorecard_str'] + match_data['context_str']
                    validation = run_full_validation(response, context_text, 'tactical')
                    
                    with st.expander("Output Validation"):
                        if validation['compliant']:
                            st.success("Format compliant")
                        else:
                            st.error(f"Missing sections: {validation['missing']}")
                        
                        if validation['risk_flag']:
                            st.warning(f"Hallucination risk flagged — {len(validation['numbers_ungrounded'])} ungrounded numbers detected")
                        else:
                            st.success("No hallucination risk detected")
                    
                    # Metrics
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    with metric_col1:
                        st.metric("Model", prompt['model'])
                    with metric_col2:
                        st.metric("Prompt Version", selected_version)
                    with metric_col3:
                        st.metric("Response Time", f"{(time.time() - start_time) * 1000:.0f} ms")
                
                except Exception as e:
                    st.error(f"Tactical analysis failed: {str(e)}")

if __name__ == "__main__":
    main()
