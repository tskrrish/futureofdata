"""
Example configuration for Volunteer PathFinder
Copy to config.py and set your keys
"""
import os

class Settings:
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')
    SUPABASE_SERVICE_KEY: str = os.getenv('SUPABASE_SERVICE_KEY', '')

    INFERENCE_NET_API_KEY: str = os.getenv('INFERENCE_NET_API_KEY', '')
    INFERENCE_NET_MODEL: str = 'meta-llama/llama-3.2-11b-instruct/fp-16'
    INFERENCE_NET_BASE_URL: str = 'https://api.inference.net/v1'

    VOLUNTEER_MATTERS_API_BASE: str = 'https://cincinnatiymca.volunteermatters.org/api'

    SECRET_KEY: str = os.getenv('SECRET_KEY', 'change-me')
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    DEBUG: bool = os.getenv('DEBUG', 'true').lower() == 'true'

    YMCA_VOLUNTEER_PAGE: str = 'https://www.myy.org/volunteering'
    VOLUNTEER_MATTERS_CATALOG: str = 'https://cincinnatiymca.volunteermatters.org/project-catalog'
    VOLUNTEER_INTEREST_FORM: str = 'https://ymcacincinnati.qualtrics.com/jfe/form/SV_0JklTjQEJTQmS2i'

    VOLUNTEER_DATA_PATH: str = 'Y Volunteer Raw Data - Jan- August 2025.xlsx'

    # Airtable/Notion Sync Configuration
    AIRTABLE_API_KEY: str = os.getenv('AIRTABLE_API_KEY', '')
    AIRTABLE_BASE_ID: str = os.getenv('AIRTABLE_BASE_ID', '')
    AIRTABLE_VOLUNTEER_TABLE: str = os.getenv('AIRTABLE_VOLUNTEER_TABLE', 'Volunteers')
    AIRTABLE_PROJECT_TABLE: str = os.getenv('AIRTABLE_PROJECT_TABLE', 'Projects')

    NOTION_API_KEY: str = os.getenv('NOTION_API_KEY', '')
    NOTION_VOLUNTEER_DB_ID: str = os.getenv('NOTION_VOLUNTEER_DB_ID', '')
    NOTION_PROJECT_DB_ID: str = os.getenv('NOTION_PROJECT_DB_ID', '')

    SYNC_ENABLED: bool = os.getenv('SYNC_ENABLED', 'false').lower() == 'true'
    SYNC_INTERVAL_MINUTES: int = int(os.getenv('SYNC_INTERVAL_MINUTES', '30'))
    SYNC_DIRECTION: str = os.getenv('SYNC_DIRECTION', 'bidirectional')  # airtable_to_notion, notion_to_airtable, bidirectional
    CONFLICT_RESOLUTION: str = os.getenv('CONFLICT_RESOLUTION', 'notion_wins')  # notion_wins, airtable_wins, manual

settings = Settings()
