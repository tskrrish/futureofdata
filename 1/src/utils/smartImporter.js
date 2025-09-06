import Papa from "papaparse";
import * as XLSX from "xlsx";
import { autoMapHeaders, validateMapping, SCHEMA_FIELDS } from './headerMapping.js';
import { formatValue, standardizeFieldValue } from './dataFormatter.js';

/**
 * Smart CSV/Excel Importer with Auto-Mapping and Format Normalization
 */
export class SmartImporter {
  constructor(options = {}) {
    this.options = {
      autoMapHeaders: true,
      normalizeData: true,
      validateData: true,
      skipEmptyRows: true,
      requireMandatoryFields: true,
      ...options
    };
    
    this.importResult = null;
    this.errors = [];
    this.warnings = [];
  }

  /**
   * Main import method - detects file type and processes accordingly
   */
  async importFile(file) {
    this.reset();
    
    try {
      const fileName = file.name.toLowerCase();
      
      if (fileName.endsWith('.csv')) {
        return await this.importCSV(file);
      } else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
        return await this.importExcel(file);
      } else {
        throw new Error('Unsupported file format. Please use CSV or Excel files.');
      }
    } catch (error) {
      this.errors.push(error.message);
      throw error;
    }
  }

  /**
   * Import CSV file using PapaParse
   */
  async importCSV(file) {
    return new Promise((resolve, reject) => {
      Papa.parse(file, {
        header: true,
        skipEmptyLines: this.options.skipEmptyRows,
        transformHeader: (header) => header.trim(),
        complete: (results) => {
          try {
            const processedData = this.processRawData(results.data, results.meta.fields);
            resolve(processedData);
          } catch (error) {
            reject(error);
          }
        },
        error: (error) => {
          reject(new Error(`CSV parsing error: ${error.message}`));
        }
      });
    });
  }

  /**
   * Import Excel file using XLSX
   */
  async importExcel(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
          
          // Use the first sheet
          const sheetName = workbook.SheetNames[0];
          const sheet = workbook.Sheets[sheetName];
          
          // Convert to JSON with header row
          const rawData = XLSX.utils.sheet_to_json(sheet, { 
            header: 1,
            defval: '',
            blankrows: !this.options.skipEmptyRows
          });
          
          if (rawData.length === 0) {
            throw new Error('Excel file appears to be empty');
          }
          
          // Extract headers and data
          const headers = rawData[0].map(header => String(header).trim());
          const dataRows = rawData.slice(1).filter(row => 
            !this.options.skipEmptyRows || row.some(cell => cell !== '' && cell !== null && cell !== undefined)
          );
          
          // Convert to objects
          const objectData = dataRows.map(row => {
            const obj = {};
            headers.forEach((header, index) => {
              obj[header] = row[index] !== undefined ? row[index] : '';
            });
            return obj;
          });
          
          const processedData = this.processRawData(objectData, headers);
          resolve(processedData);
        } catch (error) {
          reject(new Error(`Excel parsing error: ${error.message}`));
        }
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read Excel file'));
      };
      
      reader.readAsArrayBuffer(file);
    });
  }

  /**
   * Process raw data with auto-mapping and normalization
   */
  processRawData(rawData, originalHeaders) {
    if (!rawData || rawData.length === 0) {
      throw new Error('No data found in file');
    }

    // Auto-map headers
    let headerMapping = {};
    let mappingConfidence = {};
    
    if (this.options.autoMapHeaders) {
      const mappingResult = autoMapHeaders(originalHeaders);
      headerMapping = mappingResult.mapping;
      mappingConfidence = mappingResult.confidence;
      
      // Validate mapping
      const validation = validateMapping(headerMapping);
      if (this.options.requireMandatoryFields && !validation.isValid) {
        const missingFields = validation.missingRequired.join(', ');
        throw new Error(`Missing required fields: ${missingFields}`);
      }
      
      if (validation.missingRequired.length > 0) {
        this.warnings.push(`Missing optional fields: ${validation.missingRequired.join(', ')}`);
      }
    }

    // Process each row
    const processedRows = [];
    const rowErrors = [];

    rawData.forEach((row, index) => {
      try {
        const processedRow = this.processRow(row, headerMapping);
        if (processedRow && this.isValidRow(processedRow)) {
          processedRows.push(processedRow);
        }
      } catch (error) {
        rowErrors.push(`Row ${index + 1}: ${error.message}`);
      }
    });

    // Filter out invalid rows if validation is enabled
    const validRows = this.options.validateData 
      ? processedRows.filter(row => this.validateRow(row))
      : processedRows;

    this.importResult = {
      data: validRows,
      metadata: {
        originalRowCount: rawData.length,
        processedRowCount: processedRows.length,
        validRowCount: validRows.length,
        headerMapping,
        mappingConfidence,
        originalHeaders,
        mappedFields: Object.values(headerMapping)
      },
      errors: rowErrors,
      warnings: this.warnings
    };

    return this.importResult;
  }

  /**
   * Process a single row of data
   */
  processRow(row, headerMapping) {
    const processedRow = {};

    // Apply header mapping and data formatting
    for (const [originalHeader, value] of Object.entries(row)) {
      const mappedField = headerMapping[originalHeader] || originalHeader;
      const fieldConfig = SCHEMA_FIELDS[mappedField];
      
      if (fieldConfig) {
        // Apply type formatting
        let formattedValue = formatValue(value, fieldConfig.type);
        
        // Apply field-specific standardization
        if (this.options.normalizeData) {
          formattedValue = standardizeFieldValue(mappedField, formattedValue);
        }
        
        processedRow[mappedField] = formattedValue;
      } else {
        // Keep unmapped fields as-is but normalize strings
        processedRow[mappedField] = formatValue(value, 'string');
      }
    }

    // Set defaults for missing required fields
    for (const [fieldName, config] of Object.entries(SCHEMA_FIELDS)) {
      if (config.required && !(fieldName in processedRow)) {
        switch (config.type) {
          case 'string':
            processedRow[fieldName] = '';
            break;
          case 'number':
            processedRow[fieldName] = 0;
            break;
          case 'boolean':
            processedRow[fieldName] = false;
            break;
          case 'date':
            processedRow[fieldName] = undefined;
            break;
        }
      }
    }

    return processedRow;
  }

  /**
   * Basic row validation - checks if row has meaningful data
   */
  isValidRow(row) {
    if (!row) return false;
    
    // Check if row has at least some non-empty values
    const nonEmptyValues = Object.values(row).filter(value => 
      value !== '' && value !== null && value !== undefined && value !== 0
    );
    
    return nonEmptyValues.length > 0;
  }

  /**
   * Detailed row validation against schema requirements
   */
  validateRow(row) {
    if (!row) return false;

    // Check required fields
    for (const [fieldName, config] of Object.entries(SCHEMA_FIELDS)) {
      if (config.required) {
        const value = row[fieldName];
        
        switch (config.type) {
          case 'string':
            if (!value || value.trim() === '') return false;
            break;
          case 'number':
            if (typeof value !== 'number' || isNaN(value) || value < 0) return false;
            break;
          case 'boolean':
            if (typeof value !== 'boolean') return false;
            break;
          case 'date':
            if (!value) return false;
            break;
        }
      }
    }

    // Additional business logic validations
    if (row.hours && row.hours <= 0) return false;
    
    return true;
  }

  /**
   * Reset importer state
   */
  reset() {
    this.importResult = null;
    this.errors = [];
    this.warnings = [];
  }

  /**
   * Get import statistics
   */
  getImportStats() {
    if (!this.importResult) return null;
    
    const { metadata, errors, warnings } = this.importResult;
    
    return {
      totalRows: metadata.originalRowCount,
      processedRows: metadata.processedRowCount,
      validRows: metadata.validRowCount,
      skippedRows: metadata.originalRowCount - metadata.validRowCount,
      errorCount: errors.length,
      warningCount: warnings.length,
      mappingCoverage: metadata.mappedFields.length / Object.keys(SCHEMA_FIELDS).length,
      confidence: Object.values(metadata.mappingConfidence).length > 0
        ? Object.values(metadata.mappingConfidence).reduce((a, b) => a + b, 0) / Object.values(metadata.mappingConfidence).length
        : 0
    };
  }
}

/**
 * Convenience function for quick imports
 */
export async function importVolunteerData(file, options = {}) {
  const importer = new SmartImporter(options);
  return await importer.importFile(file);
}