// Data formatting and normalization utilities

/**
 * Normalizes string values by trimming whitespace and handling empty values
 */
export function normalizeString(value) {
  if (value === null || value === undefined) return '';
  return String(value).trim();
}

/**
 * Normalizes numeric values, handling various input formats
 */
export function normalizeNumber(value) {
  if (value === null || value === undefined || value === '') return 0;
  
  // Handle string numbers with commas, spaces, etc.
  if (typeof value === 'string') {
    // Remove common formatting characters
    const cleanValue = value.replace(/[,$\s]/g, '');
    const num = parseFloat(cleanValue);
    return isNaN(num) ? 0 : num;
  }
  
  const num = Number(value);
  return isNaN(num) ? 0 : num;
}

/**
 * Normalizes boolean values from various input formats
 */
export function normalizeBoolean(value) {
  if (value === null || value === undefined || value === '') return false;
  
  if (typeof value === 'boolean') return value;
  
  const str = String(value).toLowerCase().trim();
  
  // Common true values
  const trueValues = ['yes', 'y', 'true', '1', 'on', 'enabled'];
  return trueValues.includes(str);
}

/**
 * Normalizes date values from various input formats
 */
export function normalizeDate(value) {
  if (value === null || value === undefined || value === '') return undefined;
  
  // If already a Date object
  if (value instanceof Date) {
    return isNaN(value.getTime()) ? undefined : value.toISOString().split('T')[0];
  }
  
  // Handle various date formats
  let dateStr = String(value).trim();
  
  // Handle Excel date serial numbers
  if (/^\d{5}$/.test(dateStr)) {
    const excelEpoch = new Date(1900, 0, 1);
    const days = parseInt(dateStr) - 2; // Excel counts from 1900-01-01 as day 1, but has a leap year bug
    const date = new Date(excelEpoch.getTime() + days * 24 * 60 * 60 * 1000);
    return date.toISOString().split('T')[0];
  }
  
  // Common date format patterns for reference
  // - ISO format: YYYY-MM-DD
  // - US format: MM/DD/YYYY or M/D/YYYY  
  // - European format: DD/MM/YYYY or D/M/YYYY
  // - With dashes: MM-DD-YYYY
  // - Long format: Month DD, YYYY
  
  let parsedDate;
  
  // Try direct parsing first
  parsedDate = new Date(dateStr);
  if (!isNaN(parsedDate.getTime())) {
    return parsedDate.toISOString().split('T')[0];
  }
  
  // Handle MM/DD/YYYY format specifically
  if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(dateStr)) {
    const [month, day, year] = dateStr.split('/');
    parsedDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    if (!isNaN(parsedDate.getTime())) {
      return parsedDate.toISOString().split('T')[0];
    }
  }
  
  return undefined;
}

/**
 * Applies data type formatting based on schema field type
 */
export function formatValue(value, fieldType) {
  switch (fieldType) {
    case 'string':
      return normalizeString(value);
    case 'number':
      return normalizeNumber(value);
    case 'boolean':
      return normalizeBoolean(value);
    case 'date':
      return normalizeDate(value);
    default:
      return normalizeString(value);
  }
}

/**
 * Cleans and standardizes common field values
 */
export function standardizeFieldValue(fieldName, value) {
  const normalizedValue = normalizeString(value);
  
  switch (fieldName) {
    case 'branch':
      // Standardize common branch name variations
      return normalizedValue
        .replace(/ymca/gi, 'YMCA')
        .replace(/\b(rc|r\.c\.)\b/gi, 'R.C.')
        .replace(/\bcenter\b/gi, 'Center')
        .replace(/\bsenior\b/gi, 'Senior');
    
    case 'project_tag':
      // Standardize project tag formats
      return normalizedValue
        .replace(/yde\s*-\s*/gi, 'YDE - ')
        .replace(/\b(ymca|y)\b/gi, 'YMCA');
    
    case 'category':
      // Standardize category names
      return normalizedValue
        .replace(/\bchildcare\b/gi, 'Childcare')
        .replace(/\bcommunity\b/gi, 'Community')
        .replace(/\beducation\b/gi, 'Education')
        .replace(/\bsports\b/gi, 'Sports')
        .replace(/\bsenior\b/gi, 'Senior')
        .replace(/\barts\b/gi, 'Arts');
    
    default:
      return normalizedValue;
  }
}