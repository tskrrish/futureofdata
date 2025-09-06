import dashboardViewService, { DASHBOARD_VIEW_ROLES, DASHBOARD_VIEW_PERMISSIONS } from '../services/dashboardViewService';

export const setupDemoData = () => {
  localStorage.setItem('current_user', 'john.doe@ymca.org');
  localStorage.setItem('current_branch', 'Cincinnati Main');
  localStorage.setItem('user_role', 'admin');

  const demoViews = [
    {
      id: 'demo_personal_1',
      name: 'My Daily Overview',
      description: 'Personal view focusing on active volunteers and key metrics',
      role: DASHBOARD_VIEW_ROLES.PERSONAL,
      owner: 'john.doe@ymca.org',
      branch: 'Cincinnati Main',
      config: {
        branchFilter: 'All',
        search: '',
        activeTab: 'overview',
        customSettings: {}
      },
      permissions: [DASHBOARD_VIEW_PERMISSIONS.READ, DASHBOARD_VIEW_PERMISSIONS.WRITE, DASHBOARD_VIEW_PERMISSIONS.DELETE],
      sharedWith: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isDefault: true
    },
    {
      id: 'demo_branch_1',
      name: 'Branch Performance Dashboard',
      description: 'Branch-level view for tracking team performance',
      role: DASHBOARD_VIEW_ROLES.BRANCH,
      owner: 'manager@ymca.org',
      branch: 'Cincinnati Main',
      config: {
        branchFilter: 'Cincinnati Main',
        search: '',
        activeTab: 'branches',
        customSettings: {}
      },
      permissions: [DASHBOARD_VIEW_PERMISSIONS.READ, DASHBOARD_VIEW_PERMISSIONS.SHARE],
      sharedWith: [
        {
          user: 'john.doe@ymca.org',
          permissions: [DASHBOARD_VIEW_PERMISSIONS.READ],
          sharedAt: new Date().toISOString()
        }
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isDefault: false
    },
    {
      id: 'demo_org_1',
      name: 'Organization-wide Volunteer Analytics',
      description: 'Comprehensive view of all volunteer activities across the organization',
      role: DASHBOARD_VIEW_ROLES.ORGANIZATION,
      owner: 'admin@ymca.org',
      branch: 'Corporate',
      config: {
        branchFilter: 'All',
        search: '',
        activeTab: 'overview',
        customSettings: {}
      },
      permissions: [DASHBOARD_VIEW_PERMISSIONS.READ],
      sharedWith: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isDefault: false
    }
  ];

  localStorage.setItem('dashboard_views', JSON.stringify(demoViews));
  console.log('Demo dashboard views have been set up!');
  console.log('Available views:', demoViews.map(v => v.name));
};

export const clearDemoData = () => {
  localStorage.removeItem('dashboard_views');
  localStorage.removeItem('current_user');
  localStorage.removeItem('current_branch');
  localStorage.removeItem('user_role');
  console.log('Demo data cleared!');
};