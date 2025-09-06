// Synthetic Check Types
export const CheckTypes = {
  HTTP_ENDPOINT: 'http_endpoint',
  PAGE_LOAD: 'page_load',
  API_RESPONSE: 'api_response',
  USER_FLOW: 'user_flow'
};

export const CheckStatus = {
  SUCCESS: 'success',
  FAILURE: 'failure',
  WARNING: 'warning',
  PENDING: 'pending'
};

// Performance Budget Metrics
export const BudgetMetrics = {
  RESPONSE_TIME: 'response_time',
  PAGE_LOAD_TIME: 'page_load_time',
  FIRST_CONTENTFUL_PAINT: 'first_contentful_paint',
  LARGEST_CONTENTFUL_PAINT: 'largest_contentful_paint',
  CUMULATIVE_LAYOUT_SHIFT: 'cumulative_layout_shift',
  TOTAL_BLOCKING_TIME: 'total_blocking_time'
};

// Default synthetic check configuration
export const createDefaultSyntheticCheck = () => ({
  id: Date.now().toString(),
  name: '',
  type: CheckTypes.HTTP_ENDPOINT,
  url: '',
  method: 'GET',
  headers: {},
  body: '',
  expectedStatus: 200,
  timeout: 30000,
  interval: 300000, // 5 minutes
  enabled: true,
  createdAt: new Date().toISOString(),
  lastRun: null,
  status: CheckStatus.PENDING
});

// Default performance budget configuration
export const createDefaultPerformanceBudget = () => ({
  id: Date.now().toString(),
  name: '',
  url: '',
  metrics: {
    [BudgetMetrics.RESPONSE_TIME]: { threshold: 1000, enabled: true },
    [BudgetMetrics.PAGE_LOAD_TIME]: { threshold: 3000, enabled: true },
    [BudgetMetrics.FIRST_CONTENTFUL_PAINT]: { threshold: 1500, enabled: true },
    [BudgetMetrics.LARGEST_CONTENTFUL_PAINT]: { threshold: 2500, enabled: true },
    [BudgetMetrics.CUMULATIVE_LAYOUT_SHIFT]: { threshold: 0.1, enabled: true },
    [BudgetMetrics.TOTAL_BLOCKING_TIME]: { threshold: 300, enabled: true }
  },
  enabled: true,
  createdAt: new Date().toISOString(),
  lastCheck: null
});