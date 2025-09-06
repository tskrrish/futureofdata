// Fuzzy matching utilities for multi-file merge wizard

// Calculate Levenshtein distance between two strings
function levenshteinDistance(str1, str2) {
  if (!str1 || !str2) return str1 === str2 ? 0 : Math.max(str1?.length || 0, str2?.length || 0);
  
  str1 = str1.toLowerCase().trim();
  str2 = str2.toLowerCase().trim();
  
  if (str1 === str2) return 0;
  
  const matrix = Array(str2.length + 1).fill(null).map(() => Array(str1.length + 1).fill(null));
  
  for (let i = 0; i <= str1.length; i++) matrix[0][i] = i;
  for (let j = 0; j <= str2.length; j++) matrix[j][0] = j;
  
  for (let j = 1; j <= str2.length; j++) {
    for (let i = 1; i <= str1.length; i++) {
      const substitutionCost = str1[i - 1] === str2[j - 1] ? 0 : 1;
      matrix[j][i] = Math.min(
        matrix[j][i - 1] + 1, // insertion
        matrix[j - 1][i] + 1, // deletion
        matrix[j - 1][i - 1] + substitutionCost // substitution
      );
    }
  }
  
  return matrix[str2.length][str1.length];
}

// Calculate similarity score (0-1) based on Levenshtein distance
function calculateSimilarity(str1, str2) {
  if (!str1 && !str2) return 1;
  if (!str1 || !str2) return 0;
  
  const maxLength = Math.max(str1.length, str2.length);
  if (maxLength === 0) return 1;
  
  const distance = levenshteinDistance(str1, str2);
  return 1 - (distance / maxLength);
}

// Normalize phone numbers for comparison
function normalizePhone(phone) {
  if (!phone) return '';
  return phone.toString().replace(/\D/g, '').slice(-10);
}

// Normalize names for comparison
function normalizeName(name) {
  if (!name) return '';
  return name.toLowerCase()
    .replace(/[^a-z\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// Normalize email for comparison
function normalizeEmail(email) {
  if (!email) return '';
  return email.toLowerCase().trim();
}

// Calculate match confidence based on multiple fields
export function calculateMatchConfidence(recordA, recordB, weights = { name: 0.4, email: 0.4, phone: 0.2 }) {
  const similarities = {};
  let totalWeight = 0;
  let weightedScore = 0;
  
  // Name matching
  if (recordA.name || recordB.name) {
    const nameA = normalizeName(recordA.name);
    const nameB = normalizeName(recordB.name);
    similarities.name = calculateSimilarity(nameA, nameB);
    weightedScore += similarities.name * weights.name;
    totalWeight += weights.name;
  }
  
  // Email matching
  if (recordA.email || recordB.email) {
    const emailA = normalizeEmail(recordA.email);
    const emailB = normalizeEmail(recordB.email);
    
    // Exact match bonus for emails
    if (emailA && emailB && emailA === emailB) {
      similarities.email = 1.0;
    } else {
      similarities.email = calculateSimilarity(emailA, emailB);
    }
    
    weightedScore += similarities.email * weights.email;
    totalWeight += weights.email;
  }
  
  // Phone matching
  if (recordA.phone || recordB.phone) {
    const phoneA = normalizePhone(recordA.phone);
    const phoneB = normalizePhone(recordB.phone);
    
    // Exact match bonus for phones
    if (phoneA && phoneB && phoneA === phoneB) {
      similarities.phone = 1.0;
    } else {
      similarities.phone = calculateSimilarity(phoneA, phoneB);
    }
    
    weightedScore += similarities.phone * weights.phone;
    totalWeight += weights.phone;
  }
  
  const confidence = totalWeight > 0 ? weightedScore / totalWeight : 0;
  
  return {
    confidence,
    details: similarities
  };
}

// Find potential matches between two datasets
export function findPotentialMatches(dataA, dataB, options = {}) {
  const {
    threshold = 0.5,
    maxMatches = 50,
    weights = { name: 0.4, email: 0.4, phone: 0.2 }
  } = options;
  
  const matches = [];
  
  dataA.forEach((recordA, indexA) => {
    dataB.forEach((recordB, indexB) => {
      const { confidence, details } = calculateMatchConfidence(recordA, recordB, weights);
      
      if (confidence >= threshold) {
        matches.push({
          recordA,
          recordB,
          indexA,
          indexB,
          confidence,
          details
        });
      }
    });
  });
  
  // Sort by confidence (highest first) and limit results
  return matches
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, maxMatches);
}

// Find best matches (avoiding duplicates)
export function findBestMatches(dataA, dataB, options = {}) {
  const potentialMatches = findPotentialMatches(dataA, dataB, options);
  const usedA = new Set();
  const usedB = new Set();
  const bestMatches = [];
  
  // Greedy selection of best non-overlapping matches
  for (const match of potentialMatches) {
    if (!usedA.has(match.indexA) && !usedB.has(match.indexB)) {
      bestMatches.push(match);
      usedA.add(match.indexA);
      usedB.add(match.indexB);
    }
  }
  
  return bestMatches;
}

// Simple fuzzy matching function for basic use cases
export function fuzzyMatch(str1, str2, threshold = 0.7) {
  const similarity = calculateSimilarity(str1, str2);
  return similarity >= threshold;
}

// Get field mappings from CSV headers
export function detectFieldMappings(headers) {
  const mappings = { name: null, email: null, phone: null };
  const headerLower = headers.map(h => h.toLowerCase());
  
  // Name field detection
  const namePatterns = ['name', 'full name', 'fullname', 'first name', 'last name', 'volunteer name'];
  for (const pattern of namePatterns) {
    const index = headerLower.findIndex(h => h.includes(pattern));
    if (index !== -1) {
      mappings.name = headers[index];
      break;
    }
  }
  
  // Email field detection
  const emailPatterns = ['email', 'e-mail', 'email address'];
  for (const pattern of emailPatterns) {
    const index = headerLower.findIndex(h => h.includes(pattern));
    if (index !== -1) {
      mappings.email = headers[index];
      break;
    }
  }
  
  // Phone field detection
  const phonePatterns = ['phone', 'telephone', 'mobile', 'cell', 'contact', 'phone number'];
  for (const pattern of phonePatterns) {
    const index = headerLower.findIndex(h => h.includes(pattern));
    if (index !== -1) {
      mappings.phone = headers[index];
      break;
    }
  }
  
  return mappings;
}

// Normalize record fields for consistent matching
export function normalizeRecord(record, fieldMappings) {
  const normalized = { ...record };
  
  // Map detected fields to standard names
  if (fieldMappings.name && record[fieldMappings.name]) {
    normalized.name = record[fieldMappings.name];
  }
  if (fieldMappings.email && record[fieldMappings.email]) {
    normalized.email = record[fieldMappings.email];
  }
  if (fieldMappings.phone && record[fieldMappings.phone]) {
    normalized.phone = record[fieldMappings.phone];
  }
  
  return normalized;
}