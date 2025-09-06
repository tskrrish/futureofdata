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
    
    # Google Calendar Integration
    BASE_URL: str = os.getenv('BASE_URL', 'http://localhost:8000')
    GOOGLE_CREDENTIALS_PATH: str = 'google_credentials.json'

settings = Settings()
