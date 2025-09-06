// Browser-compatible Google Sheets client using REST API
class GoogleSheetsClient {
  constructor() {
    this.apiKey = null;
    this.accessToken = null;
    this.isAuthenticated = false;
    this.baseUrl = 'https://sheets.googleapis.com/v4/spreadsheets';
  }

  async authenticate(credentials) {
    try {
      if (credentials.apiKey) {
        // API Key authentication (public sheets only)
        this.apiKey = credentials.apiKey;
        this.isAuthenticated = true;
        return true;
      } else if (credentials.accessToken) {
        // OAuth2 access token
        this.accessToken = credentials.accessToken;
        this.isAuthenticated = true;
        return true;
      } else {
        throw new Error('No valid authentication method provided. Use either apiKey or accessToken.');
      }
    } catch (error) {
      console.error('Authentication failed:', error);
      this.isAuthenticated = false;
      return false;
    }
  }

  getAuthHeaders() {
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }
    
    return headers;
  }

  buildUrl(path, params = {}) {
    const url = new URL(`${this.baseUrl}${path}`);
    
    if (this.apiKey) {
      params.key = this.apiKey;
    }
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, value);
      }
    });
    
    return url.toString();
  }

  async getSpreadsheetData(spreadsheetId, range = 'Sheet1!A:Z') {
    if (!this.isAuthenticated) {
      throw new Error('Not authenticated. Call authenticate() first.');
    }

    try {
      const url = this.buildUrl(`/${spreadsheetId}/values/${encodeURIComponent(range)}`);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`API Error: ${response.status} - ${errorData.error?.message || response.statusText}`);
      }

      const data = await response.json();
      const values = data.values || [];
      
      if (values.length === 0) {
        return { headers: [], data: [] };
      }

      const headers = values[0];
      const dataRows = values.slice(1);

      return { headers, data: dataRows, rawValues: values };
    } catch (error) {
      console.error('Error fetching spreadsheet data:', error);
      throw error;
    }
  }

  async getSpreadsheetMetadata(spreadsheetId) {
    if (!this.isAuthenticated) {
      throw new Error('Not authenticated. Call authenticate() first.');
    }

    try {
      const url = this.buildUrl(`/${spreadsheetId}`, {
        fields: 'properties,sheets.properties'
      });
      
      const response = await fetch(url, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`API Error: ${response.status} - ${errorData.error?.message || response.statusText}`);
      }

      const data = await response.json();

      return {
        title: data.properties?.title || 'Unknown',
        sheets: (data.sheets || []).map(sheet => ({
          sheetId: sheet.properties?.sheetId,
          title: sheet.properties?.title,
          index: sheet.properties?.index
        })),
        lastUpdated: data.properties?.timeZone || new Date().toISOString()
      };
    } catch (error) {
      console.error('Error fetching spreadsheet metadata:', error);
      throw error;
    }
  }

  async batchGet(spreadsheetId, ranges) {
    if (!this.isAuthenticated) {
      throw new Error('Not authenticated. Call authenticate() first.');
    }

    try {
      const rangeParams = ranges.map(range => `ranges=${encodeURIComponent(range)}`).join('&');
      const url = this.buildUrl(`/${spreadsheetId}/values:batchGet`) + '&' + rangeParams;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`API Error: ${response.status} - ${errorData.error?.message || response.statusText}`);
      }

      const data = await response.json();
      return data.valueRanges || [];
    } catch (error) {
      console.error('Error in batch get operation:', error);
      throw error;
    }
  }

  transformToVolunteerData(headers, data) {
    return data.map(row => {
      const volunteer = {};
      headers.forEach((header, index) => {
        const key = this.normalizeHeader(header);
        volunteer[key] = row[index] || '';
      });
      
      // Ensure required fields exist
      volunteer.hours = parseFloat(volunteer.hours) || 0;
      volunteer.is_member = volunteer.is_member === 'Yes' || volunteer.is_member === true;
      
      return volunteer;
    });
  }

  normalizeHeader(header) {
    // Convert header names to match the expected format
    const mapping = {
      'Assignee': 'assignee',
      'Branch': 'branch',
      'Project Tag': 'project_tag',
      'Project Catalog': 'project_catalog',
      'Project': 'project',
      'Hours': 'hours',
      'Date': 'date',
      'Are you a YMCA Member?': 'is_member',
      'Member Branch': 'member_branch'
    };

    return mapping[header] || header.toLowerCase().replace(/\s+/g, '_');
  }
}

export default GoogleSheetsClient;