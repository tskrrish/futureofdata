import { SmartImporter } from '../utils/smartImporter.js';

export function useFileUpload(setRaw) {
  async function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    
    try {
      const importer = new SmartImporter({
        autoMapHeaders: true,
        normalizeData: true,
        validateData: true,
        skipEmptyRows: true,
        requireMandatoryFields: false // Allow flexible imports
      });
      
      const result = await importer.importFile(file);
      
      // Filter out zero-hour entries to match existing behavior
      const filteredData = result.data.filter(row => row.hours && row.hours > 0);
      
      // Show import statistics to user
      const stats = importer.getImportStats();
      if (stats && (stats.errorCount > 0 || stats.warningCount > 0)) {
        const messages = [];
        if (stats.errorCount > 0) {
          messages.push(`${stats.errorCount} errors`);
        }
        if (stats.warningCount > 0) {
          messages.push(`${stats.warningCount} warnings`);
        }
        if (stats.skippedRows > 0) {
          messages.push(`${stats.skippedRows} rows skipped`);
        }
        
        const message = `Import completed with ${messages.join(', ')}.\nProcessed ${stats.validRows} valid rows out of ${stats.totalRows} total.`;
        console.log('Import details:', result);
        alert(message);
      } else {
        console.log(`Successfully imported ${filteredData.length} volunteer records`);
      }
      
      setRaw(filteredData);
      
    } catch (err) {
      console.error('Import error:', err);
      alert(`Import failed: ${err.message}\n\nPlease ensure your file contains the required columns: branch, hours, assignee, date`);
    }
  }

  return handleFile;
}