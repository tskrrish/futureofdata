"""
OCR Processing Module for Paper-to-Structured Data Pipeline
Handles image processing, text extraction, and intelligent data parsing
"""
import io
import os
import re
import json
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import easyocr
from pdf2image import convert_from_bytes

class OCRProcessor:
    """Main OCR processor that handles image preprocessing, text extraction, and cleaning"""
    
    def __init__(self):
        self.easyocr_reader = None
        self._initialize_easyocr()
        
        # Common volunteer/flyer keywords for better detection
        self.volunteer_keywords = {
            'contact': ['phone', 'email', 'contact', 'call', 'reach', 'connect'],
            'location': ['address', 'location', 'where', 'venue', 'site', 'branch'],
            'time': ['time', 'when', 'date', 'schedule', 'hours', 'am', 'pm'],
            'requirements': ['require', 'need', 'must', 'should', 'background', 'check'],
            'skills': ['skill', 'experience', 'qualification', 'ability', 'knowledge'],
            'description': ['volunteer', 'help', 'assist', 'support', 'serve', 'opportunity']
        }
        
    def _initialize_easyocr(self):
        """Initialize EasyOCR reader (lazy loading)"""
        try:
            self.easyocr_reader = easyocr.Reader(['en'])
        except Exception as e:
            print(f"⚠️  EasyOCR initialization failed: {e}")
            self.easyocr_reader = None
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Enhanced image preprocessing for better OCR accuracy"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Enhance contrast using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Morphological operations to improve text
            kernel = np.ones((1,1), np.uint8)
            processed = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
            
            # Adaptive thresholding for better text/background separation
            binary = cv2.adaptiveThreshold(
                processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            return binary
            
        except Exception as e:
            print(f"❌ Image preprocessing failed: {e}")
            return image
    
    def extract_text_tesseract(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using Tesseract OCR with confidence scores"""
        try:
            # Get detailed data with confidence scores
            data = pytesseract.image_to_data(
                image, output_type=pytesseract.Output.DICT,
                config='--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,()@:-/# '
            )
            
            # Extract text with confidence filtering
            text_blocks = []
            full_text = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 30:  # Filter low-confidence text
                    text = data['text'][i].strip()
                    if text:
                        text_blocks.append({
                            'text': text,
                            'confidence': data['conf'][i],
                            'bbox': (data['left'][i], data['top'][i], 
                                   data['width'][i], data['height'][i])
                        })
                        full_text.append(text)
            
            return {
                'method': 'tesseract',
                'full_text': ' '.join(full_text),
                'text_blocks': text_blocks,
                'avg_confidence': sum(block['confidence'] for block in text_blocks) / len(text_blocks) if text_blocks else 0
            }
            
        except Exception as e:
            print(f"❌ Tesseract OCR failed: {e}")
            return {'method': 'tesseract', 'full_text': '', 'text_blocks': [], 'avg_confidence': 0}
    
    def extract_text_easyocr(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using EasyOCR"""
        if not self.easyocr_reader:
            return {'method': 'easyocr', 'full_text': '', 'text_blocks': [], 'avg_confidence': 0}
        
        try:
            results = self.easyocr_reader.readtext(image)
            
            text_blocks = []
            full_text = []
            
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Filter low-confidence results
                    text_blocks.append({
                        'text': text.strip(),
                        'confidence': confidence * 100,  # Convert to percentage
                        'bbox': bbox
                    })
                    full_text.append(text.strip())
            
            return {
                'method': 'easyocr',
                'full_text': ' '.join(full_text),
                'text_blocks': text_blocks,
                'avg_confidence': sum(block['confidence'] for block in text_blocks) / len(text_blocks) if text_blocks else 0
            }
            
        except Exception as e:
            print(f"❌ EasyOCR failed: {e}")
            return {'method': 'easyocr', 'full_text': '', 'text_blocks': [], 'avg_confidence': 0}
    
    def process_pdf(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """Process PDF and extract text from each page"""
        try:
            # Convert PDF pages to images
            images = convert_from_bytes(pdf_bytes, dpi=300)
            
            results = []
            for page_num, pil_image in enumerate(images):
                # Convert PIL to OpenCV format
                opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                
                # Process the page
                page_result = self.process_image(opencv_image)
                page_result['page_number'] = page_num + 1
                results.append(page_result)
            
            return results
            
        except Exception as e:
            print(f"❌ PDF processing failed: {e}")
            return []
    
    def process_image(self, image: np.ndarray) -> Dict[str, Any]:
        """Main image processing method that combines multiple OCR approaches"""
        try:
            # Preprocess the image
            processed_image = self.preprocess_image(image)
            
            # Try both OCR methods
            tesseract_result = self.extract_text_tesseract(processed_image)
            easyocr_result = self.extract_text_easyocr(processed_image)
            
            # Choose the best result based on confidence and text length
            if tesseract_result['avg_confidence'] > easyocr_result['avg_confidence']:
                best_result = tesseract_result
                fallback_result = easyocr_result
            else:
                best_result = easyocr_result
                fallback_result = tesseract_result
            
            # Combine results if both have decent confidence
            combined_text = best_result['full_text']
            if fallback_result['avg_confidence'] > 40 and len(fallback_result['full_text']) > len(combined_text) * 0.5:
                # Merge unique text from fallback
                fallback_words = set(fallback_result['full_text'].lower().split())
                best_words = set(combined_text.lower().split())
                unique_words = fallback_words - best_words
                if unique_words:
                    combined_text += " " + " ".join(word for word in fallback_result['full_text'].split() 
                                                  if word.lower() in unique_words)
            
            return {
                'raw_text': combined_text,
                'primary_method': best_result['method'],
                'primary_confidence': best_result['avg_confidence'],
                'fallback_method': fallback_result['method'],
                'fallback_confidence': fallback_result['avg_confidence'],
                'text_blocks': best_result['text_blocks'],
                'image_shape': image.shape
            }
            
        except Exception as e:
            print(f"❌ Image processing failed: {e}")
            return {
                'raw_text': '',
                'primary_method': 'none',
                'primary_confidence': 0,
                'fallback_method': 'none', 
                'fallback_confidence': 0,
                'text_blocks': [],
                'image_shape': image.shape if image is not None else None,
                'error': str(e)
            }
    
    def clean_and_structure_text(self, raw_text: str) -> Dict[str, Any]:
        """Clean OCR text and attempt basic structure extraction"""
        try:
            if not raw_text.strip():
                return {'structured_data': {}, 'confidence': 0, 'raw_cleaned': ''}
            
            # Basic text cleaning
            cleaned = re.sub(r'\s+', ' ', raw_text.strip())
            cleaned = re.sub(r'[^\w\s@.,():-/#+]', '', cleaned)
            
            # Extract structured information
            structured = {
                'emails': self._extract_emails(cleaned),
                'phones': self._extract_phones(cleaned), 
                'dates': self._extract_dates(cleaned),
                'times': self._extract_times(cleaned),
                'addresses': self._extract_addresses(cleaned),
                'requirements': self._extract_requirements(cleaned),
                'keywords': self._extract_keywords(cleaned)
            }
            
            # Calculate confidence based on extracted structured data
            confidence = self._calculate_structure_confidence(structured)
            
            return {
                'raw_cleaned': cleaned,
                'structured_data': structured,
                'confidence': confidence,
                'word_count': len(cleaned.split())
            }
            
        except Exception as e:
            print(f"❌ Text cleaning failed: {e}")
            return {
                'raw_cleaned': raw_text,
                'structured_data': {},
                'confidence': 0,
                'word_count': 0,
                'error': str(e)
            }
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text, re.IGNORECASE)))
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',
            r'\b\d{3}\s+\d{3}\s+\d{4}\b'
        ]
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract date patterns from text"""
        date_patterns = [
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{2,4}\b',
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b'
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(dates))
    
    def _extract_times(self, text: str) -> List[str]:
        """Extract time patterns from text"""
        time_pattern = r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b'
        return list(set(re.findall(time_pattern, text, re.IGNORECASE)))
    
    def _extract_addresses(self, text: str) -> List[str]:
        """Extract potential address patterns"""
        # Look for street addresses and locations
        address_patterns = [
            r'\b\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Ct|Court)\b',
            r'\b[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}\b'  # City, State ZIP
        ]
        addresses = []
        for pattern in address_patterns:
            addresses.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(addresses))
    
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract volunteer requirements and qualifications"""
        requirements = []
        text_lower = text.lower()
        
        # Look for requirement indicators
        requirement_indicators = [
            'background check', 'training required', 'must be', 'need to',
            'certification', 'license', 'experience', 'age requirement'
        ]
        
        sentences = text.split('.')
        for sentence in sentences:
            for indicator in requirement_indicators:
                if indicator in sentence.lower():
                    requirements.append(sentence.strip())
                    break
        
        return list(set(requirements))
    
    def _extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """Extract and categorize volunteer-related keywords"""
        text_lower = text.lower()
        found_keywords = {}
        
        for category, keywords in self.volunteer_keywords.items():
            found = []
            for keyword in keywords:
                if keyword in text_lower:
                    # Extract context around the keyword
                    pattern = rf'\b\w*{re.escape(keyword)}\w*\b'
                    matches = re.findall(pattern, text_lower)
                    found.extend(matches)
            
            if found:
                found_keywords[category] = list(set(found))
        
        return found_keywords
    
    def _calculate_structure_confidence(self, structured: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted structured data"""
        score = 0.0
        
        # Points for each type of structured data found
        if structured.get('emails'):
            score += 0.2
        if structured.get('phones'):
            score += 0.2
        if structured.get('dates'):
            score += 0.15
        if structured.get('times'):
            score += 0.15
        if structured.get('addresses'):
            score += 0.1
        if structured.get('requirements'):
            score += 0.1
        if structured.get('keywords'):
            score += 0.1 * len(structured['keywords'])
        
        return min(1.0, score)

    def process_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Main entry point for processing uploaded files"""
        try:
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.pdf':
                # Process PDF
                pdf_results = self.process_pdf(file_bytes)
                
                # Combine all pages
                combined_text = []
                all_structured = {'emails': [], 'phones': [], 'dates': [], 'times': [], 
                                'addresses': [], 'requirements': [], 'keywords': {}}
                total_confidence = 0
                
                for page_result in pdf_results:
                    if page_result.get('raw_text'):
                        combined_text.append(page_result['raw_text'])
                        
                        # Clean and structure each page
                        cleaned = self.clean_and_structure_text(page_result['raw_text'])
                        total_confidence += cleaned.get('confidence', 0)
                        
                        # Merge structured data
                        for key in all_structured.keys():
                            if key == 'keywords':
                                for cat, words in cleaned['structured_data'].get('keywords', {}).items():
                                    if cat not in all_structured['keywords']:
                                        all_structured['keywords'][cat] = []
                                    all_structured['keywords'][cat].extend(words)
                            else:
                                all_structured[key].extend(cleaned['structured_data'].get(key, []))
                
                # Remove duplicates
                for key in all_structured.keys():
                    if key == 'keywords':
                        for cat in all_structured['keywords']:
                            all_structured['keywords'][cat] = list(set(all_structured['keywords'][cat]))
                    else:
                        all_structured[key] = list(set(all_structured[key]))
                
                return {
                    'filename': filename,
                    'file_type': 'pdf',
                    'pages_processed': len(pdf_results),
                    'raw_text': ' '.join(combined_text),
                    'structured_data': all_structured,
                    'confidence': total_confidence / len(pdf_results) if pdf_results else 0,
                    'processing_method': 'pdf_multi_page'
                }
                
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                # Process image
                image_array = np.array(Image.open(io.BytesIO(file_bytes)))
                
                # Convert RGB to BGR if needed (for OpenCV)
                if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                    image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                
                ocr_result = self.process_image(image_array)
                cleaned_result = self.clean_and_structure_text(ocr_result.get('raw_text', ''))
                
                return {
                    'filename': filename,
                    'file_type': 'image',
                    'raw_text': cleaned_result['raw_cleaned'],
                    'structured_data': cleaned_result['structured_data'],
                    'confidence': (ocr_result.get('primary_confidence', 0) + cleaned_result.get('confidence', 0) * 100) / 2,
                    'processing_method': ocr_result.get('primary_method', 'unknown'),
                    'image_dimensions': ocr_result.get('image_shape', [])
                }
                
            else:
                return {
                    'filename': filename,
                    'file_type': 'unsupported',
                    'error': f'Unsupported file type: {file_ext}',
                    'supported_types': ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff']
                }
                
        except Exception as e:
            print(f"❌ File processing failed for {filename}: {e}")
            return {
                'filename': filename,
                'file_type': 'error',
                'error': str(e),
                'raw_text': '',
                'structured_data': {},
                'confidence': 0
            }