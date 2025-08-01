import os
import json
from pathlib import Path
from dotenv import load_dotenv
from config.config_manager import ConfigManager

# Load environment variables from .env file
load_dotenv()

# Global variable to hold the configuration - initialize as None
_config = None

def init_config():
    """Initialize the configuration for Elimu Research Assistant."""
    global _config
    
    # Set up config directory with educational branding
    config_dir = Path.home() / ".elimu_research_assistant"
    config_file = config_dir / "config.json"
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(exist_ok=True)
    
    # Load configuration from file if it exists
    file_config = {}
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                file_config = json.load(f)
        except json.JSONDecodeError:
            file_config = {}
    
    # Merge default config with file config - educational focus
    merged_config = {**{
        "timeout": 30,
        "max_search_results": 8,  # Increased for better educational content
        "output_format": "markdown",
        "log_level": "INFO",
        "educational_focus": True,
        "prioritize_kenyan_sources": True,
        "default_education_level": "secondary",
        "supported_subjects": ["all"],
        "language_support": ["english", "swahili"]
    }, **file_config}
    
    # Override with API keys from environment variables
    if os.environ.get("GEMINI_API_KEY"):
        merged_config["gemini_api_key"] = os.environ.get("GEMINI_API_KEY")
    if os.environ.get("SERPER_API_KEY"):
        merged_config["serper_api_key"] = os.environ.get("SERPER_API_KEY")
    
    # Create a ConfigManager instance and assign to global
    _config = ConfigManager(merged_config)
    return _config

def get_config():
    """Get the current configuration."""
    global _config
    if _config is None:
        _config = init_config()
    return _config

def update_config(key, value):
    """Update configuration and save to file."""
    
    if _config is None:
        get_config()  # This will initialize _config
    
    # Update the value
    _config[key] = value
    
    # Save to file
    config_dir = Path.home() / ".elimu_research_assistant"
    config_file = config_dir / "config.json"
    
    with open(config_file, "w") as f:
        json.dump(_config, f, indent=2)
    
    return _config

# Fix the update function to properly handle two arguments
def update(key, value=None):
    """
    Update a configuration value.
    
    This function handles both the old API (update(key, value)) 
    and the new method-style API from ConfigManager (used as config.update(key, value)).
    """
    # Check if this is being called as a method on a dict-like object
    if value is None and hasattr(key, 'items'):
        # Being used as object.update(dict) - not supported in our case
        raise TypeError("Dictionary update not supported, use key-value pairs")
        
    # Otherwise use the normal update_config function
    return update_config(key, value)

# Add ConfigManager class for backwards compatibility
class ConfigManager(dict):
    """Compatibility class that behaves like both the new ConfigManager and the old config dict."""
    
    # Add ENV_MAPPING class attribute to match config_manager.py
    ENV_MAPPING = {
        "GEMINI_API_KEY": "gemini_api_key",
        "SERPER_API_KEY": "serper_api_key",
        "LOG_LEVEL": "log_level",
        "MAX_SEARCH_RESULTS": "max_search_results",
        "MEMORY_LIMIT": "memory_limit",
        "OUTPUT_FORMAT": "output_format",
        "REQUEST_TIMEOUT": "timeout",
        "USE_KEYRING": "use_keyring",
    }
    
    def __init__(self, config_dict=None):
        dict.__init__(self, config_dict or {})
        # Expose the class-level ENV_MAPPING on the instance
        self.ENV_MAPPING = self.__class__.ENV_MAPPING
        
    def update(self, key, value, store_in_keyring=False):
        """Update method that matches the new ConfigManager.update() signature."""
        update_config(key, value)
        return False  # No keyring support in this fallback
        
    def get(self, key, default=None):
        """Get a configuration value."""
        return super().get(key, default)
        
    def items(self):
        """Get all items in the configuration."""
        return super().items()
        
    def securely_stored_keys(self):
        """Compatibility method for secure key storage."""
        return {}  # No keys are securely stored in this fallback

# Re-export for backwards compatibility
__all__ = ['get_config', 'init_config', 'ConfigManager', 'update', 'update_config']