#!/usr/bin/env python3
"""
Test script for Contact Enrichment with Privacy Gates
Tests the functionality of the contact enrichment service
"""
import asyncio
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contact_enrichment import (
    ContactEnrichmentService, 
    PrivacyGateManager, 
    EnrichmentSettings, 
    PrivacyLevel, 
    EnrichmentType
)
from datetime import datetime

async def test_contact_enrichment():
    """Test the contact enrichment functionality"""
    print("🧪 Testing Contact Enrichment Service")
    print("=" * 50)
    
    # Initialize the service
    service = ContactEnrichmentService()
    privacy_manager = PrivacyGateManager()
    
    # Test emails for different scenarios
    test_emails = [
        "john.doe@gmail.com",
        "sarah.smith@outlook.com", 
        "alex.johnson@yahoo.com",
        "test@example.com",
        "contact@tembo.io"
    ]
    
    print("\n📧 Testing Domain Extraction")
    print("-" * 30)
    for email in test_emails:
        domain = service.extract_domain(email)
        print(f"  {email} → {domain}")
    
    print("\n🔒 Testing Privacy Levels")
    print("-" * 30)
    for level in PrivacyLevel:
        description = privacy_manager.get_privacy_level_description(level)
        print(f"  {level.value}: {description}")
    
    print("\n⚙️ Testing Settings Validation")
    print("-" * 30)
    
    # Test invalid settings
    invalid_settings = EnrichmentSettings(
        enabled=True,
        privacy_level=PrivacyLevel.NONE
    )
    is_valid, error = privacy_manager.validate_privacy_settings(invalid_settings)
    print(f"  Invalid settings validation: {is_valid} - {error}")
    
    # Test valid settings
    valid_settings = EnrichmentSettings(
        enabled=True,
        privacy_level=PrivacyLevel.STANDARD,
        allowed_types=[EnrichmentType.DOMAIN, EnrichmentType.AVATAR],
        consent_date=datetime.now()
    )
    is_valid, error = privacy_manager.validate_privacy_settings(valid_settings)
    print(f"  Valid settings validation: {is_valid} - {error}")
    
    print("\n🌐 Testing Domain Enrichment")
    print("-" * 30)
    
    test_domains = ["gmail.com", "yahoo.com", "outlook.com", "example.com", "tembo.io"]
    for domain in test_domains:
        domain_info = await service.enrich_domain(domain)
        if domain_info:
            print(f"  {domain}:")
            print(f"    Organization: {domain_info.organization}")
            print(f"    Type: {domain_info.domain_type}")
            print(f"    Corporate: {domain_info.is_corporate}")
            print(f"    Website: {domain_info.website_url}")
        else:
            print(f"  {domain}: No information found")
        print()
    
    print("\n👤 Testing Avatar Generation")
    print("-" * 30)
    
    for email in test_emails[:3]:  # Test first 3 emails
        gravatar_url = service.generate_gravatar_url(email)
        print(f"  {email}")
        print(f"    Gravatar URL: {gravatar_url}")
        
        # Note: We won't test actual HTTP requests in this basic test
        # In a real environment, you might want to check if Gravatar exists
        print()
    
    print("\n🔄 Testing Complete Contact Enrichment")
    print("-" * 30)
    
    # Test with different privacy levels
    privacy_levels_to_test = [PrivacyLevel.MINIMAL, PrivacyLevel.STANDARD, PrivacyLevel.FULL]
    
    for privacy_level in privacy_levels_to_test:
        print(f"\n  Testing with {privacy_level.value} privacy level:")
        
        settings = EnrichmentSettings(
            enabled=True,
            privacy_level=privacy_level,
            allowed_types=[EnrichmentType.DOMAIN, EnrichmentType.AVATAR],
            consent_date=datetime.now()
        )
        
        test_email = "john.doe@gmail.com"
        enriched = await service.enrich_contact(test_email, settings)
        
        if enriched:
            print(f"    Email: {enriched.email}")
            print(f"    Privacy Compliant: {enriched.privacy_compliant}")
            print(f"    Enrichment Date: {enriched.enrichment_date}")
            
            if enriched.domain_info:
                print(f"    Domain Info:")
                print(f"      Domain: {enriched.domain_info.domain}")
                print(f"      Organization: {enriched.domain_info.organization}")
                print(f"      Type: {enriched.domain_info.domain_type}")
            
            if enriched.avatar_info:
                print(f"    Avatar Info:")
                print(f"      Gravatar URL: {enriched.avatar_info.gravatar_url}")
                print(f"      Source: {enriched.avatar_info.source}")
        else:
            print(f"    No enrichment performed for {test_email}")
    
    print("\n📊 Testing Batch Enrichment")
    print("-" * 30)
    
    # Test batch enrichment
    contacts = [{"email": email} for email in test_emails[:3]]
    batch_settings = EnrichmentSettings(
        enabled=True,
        privacy_level=PrivacyLevel.STANDARD,
        allowed_types=[EnrichmentType.DOMAIN, EnrichmentType.AVATAR],
        consent_date=datetime.now()
    )
    
    enriched_batch = await service.enrich_contacts_batch(contacts, batch_settings)
    print(f"  Processed {len(contacts)} contacts")
    print(f"  Enriched {len(enriched_batch)} contacts")
    
    for enriched in enriched_batch:
        print(f"    {enriched.email}: Domain={enriched.domain_info.domain if enriched.domain_info else 'None'}")
    
    print("\n✅ Contact Enrichment Testing Complete!")
    print("=" * 50)

async def test_api_simulation():
    """Simulate API calls without actually starting the server"""
    print("\n🚀 Simulating API Functionality")
    print("=" * 50)
    
    service = ContactEnrichmentService()
    
    # Simulate the test endpoint
    print("\n🧪 Testing single email enrichment (simulating /api/enrichment/test/{email})")
    test_email = "john.doe@gmail.com"
    
    settings = EnrichmentSettings(
        enabled=True,
        privacy_level=PrivacyLevel.STANDARD,
        allowed_types=[EnrichmentType.DOMAIN, EnrichmentType.AVATAR]
    )
    
    enriched = await service.enrich_contact(test_email, settings)
    
    if enriched:
        # Simulate the API response format
        api_response = {
            "email": enriched.email,
            "enrichment_date": enriched.enrichment_date.isoformat() if enriched.enrichment_date else None,
            "privacy_compliant": enriched.privacy_compliant
        }
        
        if enriched.domain_info:
            api_response["domain_info"] = {
                "domain": enriched.domain_info.domain,
                "organization": enriched.domain_info.organization,
                "domain_type": enriched.domain_info.domain_type,
                "is_corporate": enriched.domain_info.is_corporate,
                "website_url": enriched.domain_info.website_url
            }
        
        if enriched.avatar_info:
            api_response["avatar_info"] = {
                "avatar_url": enriched.avatar_info.avatar_url,
                "gravatar_url": enriched.avatar_info.gravatar_url,
                "source": enriched.avatar_info.source,
                "size": enriched.avatar_info.size
            }
        
        print(f"  API Response for {test_email}:")
        import json
        print(json.dumps(api_response, indent=4))
    
    print("\n✅ API Simulation Complete!")

if __name__ == "__main__":
    print("🧪 Contact Enrichment Test Suite")
    print("=" * 50)
    
    try:
        # Run the tests
        asyncio.run(test_contact_enrichment())
        asyncio.run(test_api_simulation())
        
        print("\n🎉 All tests completed successfully!")
        print("\nTo test the full system:")
        print("1. Run: python main.py")
        print("2. Visit: http://localhost:8000/privacy-settings")
        print("3. Test API: http://localhost:8000/api/enrichment/test/john.doe@gmail.com")
        print("4. View docs: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)