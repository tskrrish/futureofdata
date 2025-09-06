import { useState, useEffect, useCallback } from 'react';
import dashboardViewService, { DASHBOARD_VIEW_ROLES } from '../services/dashboardViewService';

export function useDashboardViews() {
  const [personalViews, setPersonalViews] = useState([]);
  const [branchViews, setBranchViews] = useState([]);
  const [organizationViews, setOrganizationViews] = useState([]);
  const [currentView, setCurrentView] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadViews = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [personal, branch, org] = await Promise.all([
        dashboardViewService.getPersonalViews(),
        dashboardViewService.getBranchViews(),
        dashboardViewService.getOrganizationViews()
      ]);

      setPersonalViews(personal);
      setBranchViews(branch);
      setOrganizationViews(org);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const saveView = useCallback(async (viewData) => {
    setLoading(true);
    setError(null);
    
    try {
      const savedView = dashboardViewService.saveView(viewData);
      await loadViews();
      return savedView;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadViews]);

  const updateView = useCallback(async (viewId, updates) => {
    setLoading(true);
    setError(null);
    
    try {
      const updatedView = dashboardViewService.updateView(viewId, updates);
      await loadViews();
      return updatedView;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadViews]);

  const deleteView = useCallback(async (viewId) => {
    setLoading(true);
    setError(null);
    
    try {
      await dashboardViewService.deleteView(viewId);
      await loadViews();
      
      if (currentView && currentView.id === viewId) {
        setCurrentView(null);
      }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadViews, currentView]);

  const shareView = useCallback(async (viewId, targetUsers, permissions) => {
    setLoading(true);
    setError(null);
    
    try {
      const updatedView = dashboardViewService.shareView(viewId, targetUsers, permissions);
      await loadViews();
      return updatedView;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadViews]);

  const unshareView = useCallback(async (viewId, targetUser) => {
    setLoading(true);
    setError(null);
    
    try {
      const updatedView = dashboardViewService.unshareView(viewId, targetUser);
      await loadViews();
      return updatedView;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadViews]);

  const setDefaultView = useCallback(async (viewId, role) => {
    try {
      dashboardViewService.setDefaultView(viewId, role);
      await loadViews();
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [loadViews]);

  const getDefaultView = useCallback((role) => {
    return dashboardViewService.getDefaultView(role);
  }, []);

  const applyView = useCallback((view, dashboardState) => {
    if (!view || !view.config) return dashboardState;

    return {
      ...dashboardState,
      branchFilter: view.config.branchFilter || dashboardState.branchFilter,
      search: view.config.search || '',
      tab: view.config.activeTab || dashboardState.tab,
      customSettings: {
        ...dashboardState.customSettings,
        ...view.config.customSettings
      }
    };
  }, []);

  const createViewFromState = useCallback((name, role, dashboardState, options = {}) => {
    return {
      name,
      role,
      description: options.description || '',
      config: {
        branchFilter: dashboardState.branchFilter,
        search: dashboardState.search,
        activeTab: dashboardState.tab,
        customSettings: dashboardState.customSettings || {}
      },
      sharedWith: options.sharedWith || [],
      isDefault: options.isDefault || false
    };
  }, []);

  const getAllViews = useCallback(() => {
    return [...personalViews, ...branchViews, ...organizationViews];
  }, [personalViews, branchViews, organizationViews]);

  const getViewById = useCallback((viewId) => {
    return getAllViews().find(view => view.id === viewId);
  }, [getAllViews]);

  const canEditView = useCallback((view) => {
    return dashboardViewService.canEdit(view);
  }, []);

  const canShareView = useCallback((view) => {
    return dashboardViewService.canShare(view);
  }, []);

  const canDeleteView = useCallback((view) => {
    return dashboardViewService.canDelete(view);
  }, []);

  useEffect(() => {
    loadViews();
  }, [loadViews]);

  useEffect(() => {
    const defaultPersonalView = getDefaultView(DASHBOARD_VIEW_ROLES.PERSONAL);
    if (defaultPersonalView && !currentView) {
      setCurrentView(defaultPersonalView);
    }
  }, [personalViews, getDefaultView, currentView]);

  return {
    personalViews,
    branchViews,
    organizationViews,
    allViews: getAllViews(),
    currentView,
    loading,
    error,
    actions: {
      loadViews,
      saveView,
      updateView,
      deleteView,
      shareView,
      unshareView,
      setDefaultView,
      getDefaultView,
      setCurrentView,
      applyView,
      createViewFromState,
      getViewById,
      canEditView,
      canShareView,
      canDeleteView
    }
  };
}