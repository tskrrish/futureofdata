export const DASHBOARD_VIEW_ROLES = {
  PERSONAL: 'personal',
  BRANCH: 'branch',
  ORGANIZATION: 'organization'
};

export const DASHBOARD_VIEW_PERMISSIONS = {
  READ: 'read',
  WRITE: 'write',
  SHARE: 'share',
  DELETE: 'delete'
};

const STORAGE_KEY = 'dashboard_views';

class DashboardViewService {
  constructor() {
    this.currentUser = this.getCurrentUser();
    this.currentBranch = this.getCurrentBranch();
  }

  getCurrentUser() {
    return localStorage.getItem('current_user') || 'user_1';
  }

  getCurrentBranch() {
    return localStorage.getItem('current_branch') || 'default_branch';
  }

  getCurrentRole() {
    return localStorage.getItem('user_role') || 'member';
  }

  getAllViews() {
    const views = localStorage.getItem(STORAGE_KEY);
    return views ? JSON.parse(views) : [];
  }

  saveView(viewData) {
    const views = this.getAllViews();
    const viewId = this.generateId();
    
    const newView = {
      id: viewId,
      name: viewData.name,
      description: viewData.description || '',
      role: viewData.role,
      owner: this.currentUser,
      branch: this.currentBranch,
      config: {
        branchFilter: viewData.config.branchFilter,
        search: viewData.config.search,
        activeTab: viewData.config.activeTab,
        customSettings: viewData.config.customSettings || {}
      },
      permissions: this.getDefaultPermissions(viewData.role),
      sharedWith: viewData.sharedWith || [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isDefault: viewData.isDefault || false
    };

    views.push(newView);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(views));
    return newView;
  }

  updateView(viewId, updates) {
    const views = this.getAllViews();
    const viewIndex = views.findIndex(v => v.id === viewId);
    
    if (viewIndex === -1) {
      throw new Error('View not found');
    }

    if (!this.canEdit(views[viewIndex])) {
      throw new Error('Permission denied');
    }

    views[viewIndex] = {
      ...views[viewIndex],
      ...updates,
      updatedAt: new Date().toISOString()
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(views));
    return views[viewIndex];
  }

  deleteView(viewId) {
    const views = this.getAllViews();
    const view = views.find(v => v.id === viewId);
    
    if (!view) {
      throw new Error('View not found');
    }

    if (!this.canDelete(view)) {
      throw new Error('Permission denied');
    }

    const filteredViews = views.filter(v => v.id !== viewId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filteredViews));
    return true;
  }

  getViewsByRole(role) {
    const views = this.getAllViews();
    return views.filter(view => {
      if (view.role === role) {
        return this.canView(view);
      }
      return false;
    });
  }

  getPersonalViews() {
    return this.getViewsByRole(DASHBOARD_VIEW_ROLES.PERSONAL);
  }

  getBranchViews() {
    return this.getViewsByRole(DASHBOARD_VIEW_ROLES.BRANCH);
  }

  getOrganizationViews() {
    return this.getViewsByRole(DASHBOARD_VIEW_ROLES.ORGANIZATION);
  }

  shareView(viewId, targetUsers, permissions = [DASHBOARD_VIEW_PERMISSIONS.READ]) {
    const views = this.getAllViews();
    const view = views.find(v => v.id === viewId);
    
    if (!view) {
      throw new Error('View not found');
    }

    if (!this.canShare(view)) {
      throw new Error('Permission denied');
    }

    const sharedWith = view.sharedWith || [];
    targetUsers.forEach(user => {
      const existingShare = sharedWith.find(s => s.user === user);
      if (existingShare) {
        existingShare.permissions = permissions;
      } else {
        sharedWith.push({
          user,
          permissions,
          sharedAt: new Date().toISOString()
        });
      }
    });

    return this.updateView(viewId, { sharedWith });
  }

  unshareView(viewId, targetUser) {
    const views = this.getAllViews();
    const view = views.find(v => v.id === viewId);
    
    if (!view) {
      throw new Error('View not found');
    }

    if (!this.canShare(view)) {
      throw new Error('Permission denied');
    }

    const sharedWith = (view.sharedWith || []).filter(s => s.user !== targetUser);
    return this.updateView(viewId, { sharedWith });
  }

  canView(view) {
    if (view.owner === this.currentUser) return true;
    
    if (view.role === DASHBOARD_VIEW_ROLES.PERSONAL) {
      return view.owner === this.currentUser;
    }
    
    if (view.role === DASHBOARD_VIEW_ROLES.BRANCH) {
      if (view.branch === this.currentBranch) return true;
    }
    
    if (view.role === DASHBOARD_VIEW_ROLES.ORGANIZATION) {
      return true;
    }

    const sharedWith = view.sharedWith || [];
    return sharedWith.some(s => s.user === this.currentUser);
  }

  canEdit(view) {
    if (view.owner === this.currentUser) return true;
    
    const sharedWith = view.sharedWith || [];
    const userShare = sharedWith.find(s => s.user === this.currentUser);
    return userShare && userShare.permissions.includes(DASHBOARD_VIEW_PERMISSIONS.WRITE);
  }

  canShare(view) {
    if (view.owner === this.currentUser) return true;
    
    const sharedWith = view.sharedWith || [];
    const userShare = sharedWith.find(s => s.user === this.currentUser);
    return userShare && userShare.permissions.includes(DASHBOARD_VIEW_PERMISSIONS.SHARE);
  }

  canDelete(view) {
    if (view.owner === this.currentUser) return true;
    
    const sharedWith = view.sharedWith || [];
    const userShare = sharedWith.find(s => s.user === this.currentUser);
    return userShare && userShare.permissions.includes(DASHBOARD_VIEW_PERMISSIONS.DELETE);
  }

  getDefaultPermissions(role) {
    switch (role) {
      case DASHBOARD_VIEW_ROLES.PERSONAL:
        return [DASHBOARD_VIEW_PERMISSIONS.READ, DASHBOARD_VIEW_PERMISSIONS.WRITE, DASHBOARD_VIEW_PERMISSIONS.DELETE];
      case DASHBOARD_VIEW_ROLES.BRANCH:
        return [DASHBOARD_VIEW_PERMISSIONS.READ, DASHBOARD_VIEW_PERMISSIONS.WRITE, DASHBOARD_VIEW_PERMISSIONS.SHARE];
      case DASHBOARD_VIEW_ROLES.ORGANIZATION:
        return [DASHBOARD_VIEW_PERMISSIONS.READ, DASHBOARD_VIEW_PERMISSIONS.SHARE];
      default:
        return [DASHBOARD_VIEW_PERMISSIONS.READ];
    }
  }

  setDefaultView(viewId, role) {
    const views = this.getAllViews();
    
    views.forEach(view => {
      if (view.role === role && view.owner === this.currentUser) {
        view.isDefault = view.id === viewId;
      }
    });

    localStorage.setItem(STORAGE_KEY, JSON.stringify(views));
  }

  getDefaultView(role) {
    const views = this.getViewsByRole(role);
    return views.find(view => view.isDefault && view.owner === this.currentUser);
  }

  generateId() {
    return 'view_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  }

  exportViews() {
    return this.getAllViews();
  }

  importViews(viewsData) {
    if (!Array.isArray(viewsData)) {
      throw new Error('Invalid views data format');
    }

    const existingViews = this.getAllViews();
    const mergedViews = [...existingViews];

    viewsData.forEach(importView => {
      const existingIndex = mergedViews.findIndex(v => v.id === importView.id);
      if (existingIndex === -1) {
        mergedViews.push({
          ...importView,
          importedAt: new Date().toISOString()
        });
      }
    });

    localStorage.setItem(STORAGE_KEY, JSON.stringify(mergedViews));
    return mergedViews.length - existingViews.length;
  }
}

export default new DashboardViewService();