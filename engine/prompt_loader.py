import os
import yaml
from typing import Dict, List, Tuple


def _get_prompts_dir() -> str:
    """Get absolute path to prompts directory from project root."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    return os.path.join(project_root, "prompts")


def load_prompt(mode: str, version: str) -> Dict:
    """
    Load a specific prompt configuration from YAML file.
    
    Args:
        mode: The prompt mode (e.g., "match_analyst", "player_intel", "tactical_predictor")
        version: The version (e.g., "v1", "v2")
    
    Returns:
        Dict containing the prompt configuration
    
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    filename = f"{mode}_{version}.yaml"
    prompts_dir = _get_prompts_dir()
    filepath = os.path.join(prompts_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Prompt file not found: {filepath}")
    
    with open(filepath, 'r') as file:
        return yaml.safe_load(file)


def list_prompt_versions(mode: str) -> List[str]:
    """
    List all available versions for a given prompt mode.
    
    Args:
        mode: The prompt mode (e.g., "match_analyst", "player_intel", "tactical_predictor")
    
    Returns:
        List of version strings (e.g., ["v1", "v2"])
    """
    prompts_dir = _get_prompts_dir()
    
    if not os.path.exists(prompts_dir):
        return []
    
    versions = []
    prefix = f"{mode}_"
    
    for filename in os.listdir(prompts_dir):
        if filename.startswith(prefix) and filename.endswith(".yaml"):
            version_part = filename[len(prefix):-5]  # Remove prefix and .yaml
            versions.append(version_part)
    
    return sorted(versions)


def fill_template(prompt_dict: Dict, **kwargs) -> Tuple[str, str]:
    """
    Fill a prompt template with provided keyword arguments.
    
    Args:
        prompt_dict: Dictionary containing prompt configuration
        **kwargs: Keyword arguments to substitute into the template
    
    Returns:
        Tuple of (system_prompt, filled_user_prompt)
    """
    system_prompt = prompt_dict.get("system_prompt", "")
    template = prompt_dict.get("user_prompt_template", "")
    
    try:
        filled_user_prompt = template.format(**kwargs)
    except KeyError as e:
        raise KeyError(f"Missing template variable: {e}")
    except Exception as e:
        raise ValueError(f"Error filling template: {e}")
    
    return system_prompt, filled_user_prompt
