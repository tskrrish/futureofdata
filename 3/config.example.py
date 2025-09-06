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

    # QuickBooks Integration
    QUICKBOOKS_CLIENT_ID: str = os.getenv('QUICKBOOKS_CLIENT_ID', '')
    QUICKBOOKS_CLIENT_SECRET: str = os.getenv('QUICKBOOKS_CLIENT_SECRET', '')
    QUICKBOOKS_REDIRECT_URI: str = os.getenv('QUICKBOOKS_REDIRECT_URI', 'http://localhost:8000/api/integration/quickbooks/callback')
    QUICKBOOKS_DEFAULT_EXPENSE_ACCOUNT: str = os.getenv('QUICKBOOKS_DEFAULT_EXPENSE_ACCOUNT', '1')

    # Xero Integration
    XERO_CLIENT_ID: str = os.getenv('XERO_CLIENT_ID', '')
    XERO_CLIENT_SECRET: str = os.getenv('XERO_CLIENT_SECRET', '')
    XERO_REDIRECT_URI: str = os.getenv('XERO_REDIRECT_URI', 'http://localhost:8000/api/integration/xero/callback')
    XERO_DEFAULT_EXPENSE_ACCOUNT: str = os.getenv('XERO_DEFAULT_EXPENSE_ACCOUNT', '400')

    # Twilio SMS Configuration
    TWILIO_ACCOUNT_SID: str = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN: str = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER: str = os.getenv('TWILIO_PHONE_NUMBER', '')
    SMS_WEBHOOK_URL: str = os.getenv('SMS_WEBHOOK_URL', 'http://localhost:8000/webhooks/sms')

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

    # Slack Integration Settings
    SLACK_BOT_TOKEN: str = os.getenv('SLACK_BOT_TOKEN', '')
    SLACK_APP_TOKEN: str = os.getenv('SLACK_APP_TOKEN', '')
    SLACK_SIGNING_SECRET: str = os.getenv('SLACK_SIGNING_SECRET', '')
    
    # Default Slack channels
    SLACK_ANNOUNCEMENTS_CHANNEL: str = os.getenv('SLACK_ANNOUNCEMENTS_CHANNEL', '#volunteer-announcements')
    SLACK_SHIFT_CHANNEL: str = os.getenv('SLACK_SHIFT_CHANNEL', '#shift-notifications')
    SLACK_APPROVALS_CHANNEL: str = os.getenv('SLACK_APPROVALS_CHANNEL', '#volunteer-approvals')
    
    # Slack integration enabled
    SLACK_ENABLED: bool = os.getenv('SLACK_ENABLED', 'false').lower() == 'true'

    # Salesforce Nonprofit Cloud Configuration
    SALESFORCE_INSTANCE_URL: str = os.getenv('SALESFORCE_INSTANCE_URL', '')
    SALESFORCE_CLIENT_ID: str = os.getenv('SALESFORCE_CLIENT_ID', '')
    SALESFORCE_CLIENT_SECRET: str = os.getenv('SALESFORCE_CLIENT_SECRET', '')
    SALESFORCE_USERNAME: str = os.getenv('SALESFORCE_USERNAME', '')
    SALESFORCE_PASSWORD: str = os.getenv('SALESFORCE_PASSWORD', '')
    SALESFORCE_SECURITY_TOKEN: str = os.getenv('SALESFORCE_SECURITY_TOKEN', '')
    SALESFORCE_API_VERSION: str = os.getenv('SALESFORCE_API_VERSION', 'v58.0')
    
    # Salesforce sync settings
    SALESFORCE_SYNC_ENABLED: bool = os.getenv('SALESFORCE_SYNC_ENABLED', 'false').lower() == 'true'
    SALESFORCE_SYNC_INTERVAL_HOURS: int = int(os.getenv('SALESFORCE_SYNC_INTERVAL_HOURS', '24'))
    SALESFORCE_BATCH_SIZE: int = int(os.getenv('SALESFORCE_BATCH_SIZE', '50'))

settings = Settings()
