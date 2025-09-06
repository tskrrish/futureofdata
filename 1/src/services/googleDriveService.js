class GoogleDriveService {
  constructor() {
    this.gapi = null;
    this.isAuthenticated = false;
    this.vaultFolderId = null;
    this.authInstance = null;
  }

  async initialize(clientId, apiKey, discoveryDocs = ['https://www.googleapis.com/discovery/v1/apis/drive/v3/rest']) {
    try {
      await this.loadGapi();
      
      await this.gapi.load('client:auth2', async () => {
        await this.gapi.client.init({
          apiKey: apiKey,
          clientId: clientId,
          discoveryDocs: discoveryDocs,
          scope: 'https://www.googleapis.com/auth/drive.file'
        });

        this.authInstance = this.gapi.auth2.getAuthInstance();
      });

      return true;
    } catch (error) {
      console.error('Failed to initialize Google Drive service:', error);
      return false;
    }
  }

  async loadGapi() {
    return new Promise((resolve, reject) => {
      if (window.gapi) {
        this.gapi = window.gapi;
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://apis.google.com/js/api.js';
      script.onload = () => {
        this.gapi = window.gapi;
        resolve();
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  async authenticate() {
    try {
      if (!this.authInstance) {
        throw new Error('Google API not initialized');
      }

      if (!this.authInstance.isSignedIn.get()) {
        const result = await this.authInstance.signIn();
        if (!result.isSignedIn()) {
          throw new Error('User cancelled authentication');
        }
      }

      this.isAuthenticated = true;
      await this.ensureVaultFolder();
      return true;
    } catch (error) {
      console.error('Authentication failed:', error);
      this.isAuthenticated = false;
      throw error;
    }
  }

  async ensureVaultFolder() {
    try {
      const folderName = 'YMCA File Vault';
      
      const response = await this.gapi.client.drive.files.list({
        q: `name='${folderName}' and mimeType='application/vnd.google-apps.folder' and trashed=false`,
        fields: 'files(id, name)'
      });

      if (response.result.files && response.result.files.length > 0) {
        this.vaultFolderId = response.result.files[0].id;
      } else {
        const folderResponse = await this.gapi.client.drive.files.create({
          resource: {
            name: folderName,
            mimeType: 'application/vnd.google-apps.folder'
          },
          fields: 'id'
        });
        this.vaultFolderId = folderResponse.result.id;
      }

      return this.vaultFolderId;
    } catch (error) {
      console.error('Failed to ensure vault folder:', error);
      throw error;
    }
  }

  async createStructuredFolder(category) {
    if (!this.isAuthenticated || !this.vaultFolderId) {
      throw new Error('Not authenticated or vault folder not created');
    }

    try {
      const folderName = `${category}_${new Date().getFullYear()}`;
      
      const response = await this.gapi.client.drive.files.list({
        q: `name='${folderName}' and parents in '${this.vaultFolderId}' and mimeType='application/vnd.google-apps.folder' and trashed=false`,
        fields: 'files(id, name)'
      });

      if (response.result.files && response.result.files.length > 0) {
        return response.result.files[0].id;
      }

      const folderResponse = await this.gapi.client.drive.files.create({
        resource: {
          name: folderName,
          mimeType: 'application/vnd.google-apps.folder',
          parents: [this.vaultFolderId]
        },
        fields: 'id'
      });

      return folderResponse.result.id;
    } catch (error) {
      console.error('Failed to create structured folder:', error);
      throw error;
    }
  }

  async uploadDocument(file, category, metadata = {}) {
    if (!this.isAuthenticated || !this.vaultFolderId) {
      throw new Error('Not authenticated or vault folder not created');
    }

    try {
      const folderId = await this.createStructuredFolder(category);
      const timestamp = new Date().toISOString().slice(0, 10);
      const fileName = `${timestamp}_${metadata.name || file.name}`;

      const fileMetadata = {
        name: fileName,
        parents: [folderId],
        description: JSON.stringify({
          category,
          uploadDate: new Date().toISOString(),
          originalName: file.name,
          ...metadata
        })
      };

      const form = new FormData();
      form.append('metadata', new Blob([JSON.stringify(fileMetadata)], { type: 'application/json' }));
      form.append('file', file);

      const response = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,createdTime,size,mimeType', {
        method: 'POST',
        headers: new Headers({
          'Authorization': `Bearer ${this.gapi.auth2.getAuthInstance().currentUser.get().getAuthResponse().access_token}`
        }),
        body: form
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Failed to upload document:', error);
      throw error;
    }
  }

  async listDocuments(category = null) {
    if (!this.isAuthenticated || !this.vaultFolderId) {
      throw new Error('Not authenticated or vault folder not created');
    }

    try {
      let query = `parents in '${this.vaultFolderId}' and trashed=false`;
      
      if (category) {
        const folderId = await this.createStructuredFolder(category);
        query = `parents in '${folderId}' and trashed=false`;
      }

      const response = await this.gapi.client.drive.files.list({
        q: query,
        fields: 'files(id, name, createdTime, modifiedTime, size, mimeType, description, parents)',
        orderBy: 'createdTime desc'
      });

      return response.result.files || [];
    } catch (error) {
      console.error('Failed to list documents:', error);
      throw error;
    }
  }

  async downloadDocument(fileId, fileName) {
    if (!this.isAuthenticated) {
      throw new Error('Not authenticated');
    }

    try {
      const response = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`, {
        headers: {
          'Authorization': `Bearer ${this.gapi.auth2.getAuthInstance().currentUser.get().getAuthResponse().access_token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      a.click();
      URL.revokeObjectURL(url);

      return true;
    } catch (error) {
      console.error('Failed to download document:', error);
      throw error;
    }
  }

  async deleteDocument(fileId) {
    if (!this.isAuthenticated) {
      throw new Error('Not authenticated');
    }

    try {
      const response = await this.gapi.client.drive.files.delete({
        fileId: fileId
      });
      return true;
    } catch (error) {
      console.error('Failed to delete document:', error);
      throw error;
    }
  }

  async exportToGoogleSheets(data, filename, category = 'Reports') {
    if (!this.isAuthenticated || !this.vaultFolderId) {
      throw new Error('Not authenticated or vault folder not created');
    }

    try {
      const folderId = await this.createStructuredFolder(category);
      const timestamp = new Date().toISOString().slice(0, 10);
      const sheetName = `${timestamp}_${filename}`;

      const headers = Object.keys(data[0] || {});
      const values = [headers, ...data.map(row => headers.map(header => row[header] || ''))];

      const resource = {
        name: sheetName,
        parents: [folderId],
        mimeType: 'application/vnd.google-apps.spreadsheet'
      };

      const createResponse = await this.gapi.client.drive.files.create({
        resource: resource,
        fields: 'id, name, webViewLink'
      });

      const spreadsheetId = createResponse.result.id;

      await this.gapi.client.load('sheets', 'v4');

      const updateResponse = await this.gapi.client.sheets.spreadsheets.values.update({
        spreadsheetId: spreadsheetId,
        range: 'Sheet1!A1',
        valueInputOption: 'RAW',
        resource: { values }
      });

      return createResponse.result;
    } catch (error) {
      console.error('Failed to export to Google Sheets:', error);
      throw error;
    }
  }

  getAuthUrl() {
    return null;
  }

  isConnected() {
    return this.isAuthenticated && this.authInstance?.isSignedIn.get();
  }

  disconnect() {
    this.isAuthenticated = false;
    this.vaultFolderId = null;
    
    if (this.authInstance) {
      this.authInstance.signOut();
    }
  }
}

export const googleDriveService = new GoogleDriveService();