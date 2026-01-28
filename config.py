"""
MAAS Practice - Configuration
"""

import os

# API Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"  # Good balance of quality and cost
MAX_TOKENS = 500

# App Settings
APP_TITLE = "MAAS Practice"
APP_SUBTITLE = "Patient Responses Adapted to Clinical Technique in Calibrated Encounters"

# Session Settings
MAX_TURNS = 50  # Maximum conversation turns before auto-end
