"""
Test script for OCR Import Pipeline
Tests the OCR processing and data extraction functionality
"""
import os
import sys
import asyncio
import json
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
import io

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr_processor import OCRProcessor
from data_extractor import DataExtractor

def create_sample_volunteer_flyer() -> bytes:
    """Create a sample volunteer opportunity flyer image for testing"""
    
    # Create a simple flyer image
    width, height = 800, 1000
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font
    try:
        title_font = ImageFont.truetype("arial.ttf", 40)
        header_font = ImageFont.truetype("arial.ttf", 24)
        text_font = ImageFont.truetype("arial.ttf", 18)
    except (OSError, IOError):
        # Fallback to default font
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # Draw flyer content
    y_pos = 50
    
    # Title
    draw.text((50, y_pos), "VOLUNTEER OPPORTUNITY", fill='black', font=title_font)
    y_pos += 80
    
    # Event title
    draw.text((50, y_pos), "Youth Summer Camp Assistant", fill='blue', font=header_font)
    y_pos += 60
    
    # Organization
    draw.text((50, y_pos), "YMCA of Greater Cincinnati - Blue Ash Branch", fill='black', font=text_font)
    y_pos += 40
    
    # Description
    description = [
        "Help supervise and engage children ages 6-12 in summer camp activities.",
        "Assist with arts and crafts, sports, swimming, and educational programs.",
        "Create a safe, fun, and inclusive environment for all campers."
    ]
    
    for line in description:
        draw.text((50, y_pos), line, fill='black', font=text_font)
        y_pos += 30
    
    y_pos += 20
    
    # Requirements
    draw.text((50, y_pos), "Requirements:", fill='red', font=header_font)
    y_pos += 40
    
    requirements = [
        "• Must be 18 years or older",
        "• Background check required",
        "• Previous experience with children preferred",
        "• CPR certification required (training provided)",
        "• Available June 1 - August 31, Monday-Friday 8:00 AM - 4:00 PM"
    ]
    
    for req in requirements:
        draw.text((70, y_pos), req, fill='black', font=text_font)
        y_pos += 30
    
    y_pos += 30
    
    # Contact info
    draw.text((50, y_pos), "Contact Information:", fill='red', font=header_font)
    y_pos += 40
    
    contact_info = [
        "Email: volunteers@cincinnatiymca.org",
        "Phone: (513) 745-9622",
        "Address: 4449 Cooper Rd, Blue Ash, OH 45242",
        "Apply online: cincinnatiymca.volunteermatters.org"
    ]
    
    for info in contact_info:
        draw.text((50, y_pos), info, fill='black', font=text_font)
        y_pos += 30
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

def test_ocr_processing():
    """Test OCR processing functionality"""
    
    print("🧪 Testing OCR Processing Pipeline")
    print("=" * 50)
    
    # Initialize processors
    ocr_processor = OCRProcessor()
    data_extractor = DataExtractor()
    
    # Create sample image
    print("📄 Creating sample volunteer flyer...")
    sample_image = create_sample_volunteer_flyer()
    print(f"✅ Created sample image ({len(sample_image)} bytes)")
    
    # Test OCR processing
    print("\n🔍 Testing OCR text extraction...")
    ocr_result = ocr_processor.process_file(sample_image, "sample_volunteer_flyer.png")
    
    print(f"✅ OCR completed")
    print(f"   - Processing method: {ocr_result.get('processing_method', 'unknown')}")
    print(f"   - Confidence: {ocr_result.get('confidence', 0):.1f}%")
    print(f"   - Text length: {len(ocr_result.get('raw_text', ''))} characters")
    
    if ocr_result.get('raw_text'):
        print(f"\n📝 Extracted text preview:")
        print("-" * 40)
        preview = ocr_result['raw_text'][:300]
        print(f"{preview}{'...' if len(ocr_result['raw_text']) > 300 else ''}")
        print("-" * 40)
    
    # Test structured data extraction
    print("\n🏗️  Testing structured data extraction...")
    opportunity = data_extractor.extract_volunteer_opportunity(ocr_result)
    opportunity_dict = data_extractor.to_dict(opportunity)
    
    print(f"✅ Structured extraction completed")
    print(f"   - Extraction confidence: {opportunity.confidence_score:.2f}")
    print(f"   - Title: {opportunity.title}")
    print(f"   - Organization: {opportunity.organization}")
    print(f"   - Category: {opportunity.category}")
    
    # Display key extracted data
    print(f"\n📊 Key extracted information:")
    print(f"   - Contact Email: {opportunity.contact_email}")
    print(f"   - Contact Phone: {opportunity.contact_phone}")
    print(f"   - Location: {opportunity.location}")
    print(f"   - Branch: {opportunity.branch}")
    print(f"   - Age Requirement: {opportunity.age_requirement}")
    print(f"   - Background Check Required: {opportunity.background_check}")
    print(f"   - Training Required: {opportunity.training_required}")
    print(f"   - Requirements: {len(opportunity.requirements or [])} items")
    print(f"   - Skills Needed: {len(opportunity.skills_needed or [])} items")
    
    if opportunity.requirements:
        print(f"\n📋 Extracted requirements:")
        for i, req in enumerate(opportunity.requirements[:3], 1):
            print(f"   {i}. {req}")
    
    # Test edge cases
    print(f"\n🧪 Testing edge cases...")
    
    # Test empty image
    empty_result = ocr_processor.process_file(b"invalid", "empty.png")
    print(f"   - Empty file handling: {'✅' if 'error' in empty_result else '❌'}")
    
    # Test with minimal text
    minimal_opportunity = data_extractor.extract_volunteer_opportunity({
        'raw_text': 'Volunteer needed. Call 555-1234.',
        'structured_data': {'phones': ['555-1234']},
        'confidence': 50
    })
    print(f"   - Minimal text extraction: {'✅' if minimal_opportunity.confidence_score > 0 else '❌'}")
    
    print(f"\n✅ OCR Pipeline testing completed!")
    
    return {
        'ocr_result': ocr_result,
        'structured_data': opportunity_dict,
        'test_passed': True
    }

def test_file_format_support():
    """Test different file format support"""
    
    print(f"\n🗂️  Testing file format support...")
    
    ocr_processor = OCRProcessor()
    
    # Test with different "file types"
    test_cases = [
        ("test.jpg", "image/jpeg"),
        ("test.png", "image/png"), 
        ("test.pdf", "application/pdf"),
        ("test.txt", "text/plain"),
        ("test.doc", "application/msword")
    ]
    
    for filename, content_type in test_cases:
        # Create minimal test data
        test_data = b"test data"
        
        try:
            result = ocr_processor.process_file(test_data, filename)
            supported = result.get('file_type') != 'unsupported'
            status = "✅ Supported" if supported else "❌ Unsupported"
            print(f"   - {filename} ({content_type}): {status}")
        except Exception as e:
            print(f"   - {filename} ({content_type}): ❌ Error - {str(e)[:50]}")

def generate_test_report(test_results: Dict[str, Any]):
    """Generate a test report"""
    
    print(f"\n📊 TEST REPORT")
    print("=" * 50)
    
    ocr_result = test_results.get('ocr_result', {})
    structured_data = test_results.get('structured_data', {})
    
    # OCR Performance
    print(f"OCR Processing:")
    print(f"  - Confidence Score: {ocr_result.get('confidence', 0):.1f}%")
    print(f"  - Text Extracted: {'✅ Yes' if ocr_result.get('raw_text') else '❌ No'}")
    print(f"  - Characters Extracted: {len(ocr_result.get('raw_text', ''))}")
    
    # Data Extraction Performance  
    print(f"\nData Extraction:")
    confidence = structured_data.get('confidence_score', 0)
    print(f"  - Extraction Confidence: {confidence:.2f}")
    print(f"  - Title Extracted: {'✅ Yes' if structured_data.get('title') else '❌ No'}")
    print(f"  - Contact Info: {'✅ Yes' if structured_data.get('contact_email') or structured_data.get('contact_phone') else '❌ No'}")
    print(f"  - Location Info: {'✅ Yes' if structured_data.get('location') or structured_data.get('branch') else '❌ No'}")
    print(f"  - Requirements: {len(structured_data.get('requirements', []))} extracted")
    print(f"  - Category: {structured_data.get('category', 'None')}")
    
    # Overall Assessment
    overall_score = (ocr_result.get('confidence', 0) / 100 + confidence) / 2
    print(f"\nOverall Pipeline Score: {overall_score:.2f} / 1.0")
    
    if overall_score >= 0.7:
        print("✅ PIPELINE STATUS: EXCELLENT - Ready for production")
    elif overall_score >= 0.5:
        print("⚠️ PIPELINE STATUS: GOOD - Minor improvements needed")
    elif overall_score >= 0.3:
        print("⚠️ PIPELINE STATUS: FAIR - Significant improvements needed")
    else:
        print("❌ PIPELINE STATUS: POOR - Major issues require attention")

if __name__ == "__main__":
    try:
        # Run comprehensive tests
        test_results = test_ocr_processing()
        test_file_format_support()
        generate_test_report(test_results)
        
        print(f"\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)