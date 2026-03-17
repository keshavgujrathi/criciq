import re
from typing import Dict, List, Any

# Required sections for each analysis mode
REQUIRED_SECTIONS = {
    "match_analyst": ["MATCH STATE", "MOMENTUM", "KEY BATTLEGROUND", "OUTCOME RANGE", "ANALYST TAKE"],
    "player_intel": ["FORM SUMMARY", "STRENGTHS IN THIS CONTEXT", "VULNERABILITIES", "HISTORICAL EDGE", "TACTICAL RECOMMENDATION"],
    "tactical": ["SITUATION ASSESSMENT", "OPTION 1", "OPTION 2", "OPTION 3", "RECOMMENDED CALL"],
}


def check_format_compliance(response_text: str, mode: str) -> Dict[str, Any]:
    """
    Check if response contains all required sections for the given mode.
    
    Args:
        response_text: The LLM response text to validate
        mode: The analysis mode (e.g., "match_analyst", "player_intel", "tactical")
    
    Returns:
        Dict with compliance information
    """
    required_sections = REQUIRED_SECTIONS.get(mode, [])
    response_lower = response_text.lower()
    
    present = []
    missing = []
    
    for section in required_sections:
        if section.lower() in response_lower:
            present.append(section)
        else:
            missing.append(section)
    
    return {
        "compliant": len(missing) == 0,
        "present": present,
        "missing": missing
    }


def check_hallucination_risk(response_text: str, context_text: str) -> Dict[str, Any]:
    """
    Check for potential hallucinations by comparing numbers in response vs context.
    
    NOTE: This is a heuristic approach, not ground truth validation. It assumes
    that factual numbers should be present in the provided context.
    
    Args:
        response_text: The LLM response text
        context_text: The context data provided to the LLM
    
    Returns:
        Dict with hallucination risk assessment
    """
    # Extract all numbers (integers and decimals) from both texts
    response_numbers = set(re.findall(r'\b\d+\.?\d*\b', response_text))
    context_numbers = set(re.findall(r'\b\d+\.?\d*\b', context_text))
    
    # Check which response numbers are grounded in context
    grounded = [num for num in response_numbers if num in context_numbers]
    ungrounded = [num for num in response_numbers if num not in context_numbers]
    
    # Calculate risk flag (more than 20% ungrounded numbers = risk)
    total_numbers = len(response_numbers)
    risk_flag = False
    
    if total_numbers > 0:
        ungrounded_percentage = len(ungrounded) / total_numbers
        risk_flag = ungrounded_percentage > 0.2
    
    return {
        "numbers_in_response": list(response_numbers),
        "numbers_grounded": grounded,
        "numbers_ungrounded": ungrounded,
        "risk_flag": risk_flag
    }


def check_consistency(responses_list: List[str]) -> Dict[str, Any]:
    """
    Check structural consistency across multiple responses to the same prompt.
    
    Args:
        responses_list: List of response strings from multiple runs
    
    Returns:
        Dict with consistency analysis
    """
    if len(responses_list) != 3:
        raise ValueError("Expected exactly 3 responses for consistency check")
    
    section_presence = {}
    all_sections = set()
    
    # Collect all sections that appear in any response
    for response in responses_list:
        for sections in REQUIRED_SECTIONS.values():
            for section in sections:
                if section.lower() in response.lower():
                    all_sections.add(section)
    
    # Check presence of each section across all responses
    for section in all_sections:
        presence = []
        for response in responses_list:
            present = section.lower() in response.lower()
            presence.append(present)
        section_presence[section] = presence
    
    # Check if all sections are present in all responses
    structurally_consistent = all(all(presence) for presence in section_presence.values())
    
    return {
        "structurally_consistent": structurally_consistent,
        "section_presence": section_presence
    }


def run_full_validation(response_text: str, context_text: str, mode: str) -> Dict[str, Any]:
    """
    Run complete validation on a response.
    
    Args:
        response_text: The LLM response to validate
        context_text: The context provided to the LLM
        mode: The analysis mode
    
    Returns:
        Combined validation results
    """
    format_result = check_format_compliance(response_text, mode)
    hallucination_result = check_hallucination_risk(response_text, context_text)
    
    return {
        "mode": mode,
        **format_result,
        **hallucination_result
    }
