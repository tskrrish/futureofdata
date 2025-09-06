// Header detection and mapping configuration for volunteer data
export const SCHEMA_FIELDS = {
  branch: {
    required: true,
    type: 'string',
    aliases: ['branch', 'location', 'site', 'facility', 'center']
  },
  hours: {
    required: true,
    type: 'number',
    aliases: ['hours', 'hrs', 'time', 'duration', 'volunteer_hours', 'total_hours']
  },
  assignee: {
    required: true,
    type: 'string',
    aliases: ['assignee', 'name', 'volunteer_name', 'full_name', 'person', 'volunteer']
  },
  date: {
    required: true,
    type: 'date',
    aliases: ['date', 'volunteer_date', 'service_date', 'activity_date', 'day']
  },
  is_member: {
    required: false,
    type: 'boolean',
    aliases: ['is_member', 'member', 'are you a ymca member', 'membership', 'is_ymca_member']
  },
  member_branch: {
    required: false,
    type: 'string',
    aliases: ['member_branch', 'memberbranch', 'home_branch', 'membership_branch']
  },
  project_tag: {
    required: false,
    type: 'string',
    aliases: ['project_tag', 'projecttag', 'tag', 'category_tag']
  },
  project_catalog: {
    required: false,
    type: 'string',
    aliases: ['project_catalog', 'projectcatalog', 'catalog', 'service_catalog']
  },
  project: {
    required: false,
    type: 'string',
    aliases: ['project', 'activity', 'service', 'program', 'initiative']
  },
  category: {
    required: false,
    type: 'string',
    aliases: ['category', 'type', 'classification']
  },
  department: {
    required: false,
    type: 'string',
    aliases: ['department', 'dept', 'division', 'unit']
  }
};

/**
 * Normalizes header names for better matching
 */
export function normalizeHeader(header) {
  if (!header || typeof header !== 'string') return '';
  
  return header
    .toLowerCase()
    .trim()
    // Remove special characters and replace with spaces
    .replace(/[^\w\s]/g, ' ')
    // Collapse multiple spaces into single spaces
    .replace(/\s+/g, ' ')
    .trim()
    // Replace spaces with underscores for consistent comparison
    .replace(/\s/g, '_');
}

/**
 * Finds the best matching schema field for a given header
 */
export function findBestMatch(header, usedFields = new Set()) {
  const normalizedHeader = normalizeHeader(header);
  
  // First, try exact matches
  for (const [fieldName, config] of Object.entries(SCHEMA_FIELDS)) {
    if (usedFields.has(fieldName)) continue;
    
    if (config.aliases.some(alias => normalizeHeader(alias) === normalizedHeader)) {
      return fieldName;
    }
  }
  
  // Then try partial matches (contains)
  for (const [fieldName, config] of Object.entries(SCHEMA_FIELDS)) {
    if (usedFields.has(fieldName)) continue;
    
    if (config.aliases.some(alias => {
      const normalizedAlias = normalizeHeader(alias);
      return normalizedHeader.includes(normalizedAlias) || normalizedAlias.includes(normalizedHeader);
    })) {
      return fieldName;
    }
  }
  
  return null;
}

/**
 * Automatically maps headers from imported data to schema fields
 */
export function autoMapHeaders(headers) {
  const mapping = {};
  const usedFields = new Set();
  const confidence = {};
  
  // Sort headers by length (longer headers first for better matching)
  const sortedHeaders = [...headers].sort((a, b) => (b || '').length - (a || '').length);
  
  for (const header of sortedHeaders) {
    if (!header) continue;
    
    const matchedField = findBestMatch(header, usedFields);
    if (matchedField) {
      mapping[header] = matchedField;
      usedFields.add(matchedField);
      
      // Calculate confidence score
      const normalizedHeader = normalizeHeader(header);
      const config = SCHEMA_FIELDS[matchedField];
      const exactMatch = config.aliases.some(alias => normalizeHeader(alias) === normalizedHeader);
      confidence[header] = exactMatch ? 1.0 : 0.7;
    }
  }
  
  return { mapping, confidence };
}

/**
 * Validates if the mapping covers required fields
 */
export function validateMapping(mapping) {
  const mappedFields = new Set(Object.values(mapping));
  const missingRequired = [];
  
  for (const [fieldName, config] of Object.entries(SCHEMA_FIELDS)) {
    if (config.required && !mappedFields.has(fieldName)) {
      missingRequired.push(fieldName);
    }
  }
  
  return {
    isValid: missingRequired.length === 0,
    missingRequired,
    coverage: mappedFields.size / Object.keys(SCHEMA_FIELDS).length
  };
}