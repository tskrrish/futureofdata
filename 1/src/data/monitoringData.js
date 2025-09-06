import { CheckTypes, CheckStatus, BudgetMetrics } from '../types/monitoring';

// Sample synthetic checks data
export const SAMPLE_SYNTHETIC_CHECKS = [
  {
    id: '1',
    name: 'YMCA Homepage Health',
    type: CheckTypes.PAGE_LOAD,
    url: 'https://ymcacincinnati.org',
    method: 'GET',
    headers: {},
    body: '',
    expectedStatus: 200,
    timeout: 30000,
    interval: 300000,
    enabled: true,
    createdAt: '2025-01-15T10:00:00Z',
    lastRun: '2025-01-15T12:30:00Z',
    status: CheckStatus.SUCCESS,
    lastDuration: 1250,
    successRate: 98.5
  },
  {
    id: '2',
    name: 'Volunteer API Endpoint',
    type: CheckTypes.API_RESPONSE,
    url: '/api/volunteers',
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: '',
    expectedStatus: 200,
    timeout: 10000,
    interval: 180000,
    enabled: true,
    createdAt: '2025-01-15T10:15:00Z',
    lastRun: '2025-01-15T12:28:00Z',
    status: CheckStatus.SUCCESS,
    lastDuration: 450,
    successRate: 99.2
  },
  {
    id: '3',
    name: 'Member Portal Login Flow',
    type: CheckTypes.USER_FLOW,
    url: 'https://ymcacincinnati.org/login',
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{"username": "test@example.com", "password": "testpass"}',
    expectedStatus: 200,
    timeout: 15000,
    interval: 600000,
    enabled: true,
    createdAt: '2025-01-15T09:45:00Z',
    lastRun: '2025-01-15T12:25:00Z',
    status: CheckStatus.WARNING,
    lastDuration: 3200,
    successRate: 95.8
  }
];

// Sample performance budgets data
export const SAMPLE_PERFORMANCE_BUDGETS = [
  {
    id: '1',
    name: 'YMCA Homepage Performance',
    url: 'https://ymcacincinnati.org',
    metrics: {
      [BudgetMetrics.RESPONSE_TIME]: { threshold: 1000, enabled: true, current: 850, status: 'passing' },
      [BudgetMetrics.PAGE_LOAD_TIME]: { threshold: 3000, enabled: true, current: 2100, status: 'passing' },
      [BudgetMetrics.FIRST_CONTENTFUL_PAINT]: { threshold: 1500, enabled: true, current: 1200, status: 'passing' },
      [BudgetMetrics.LARGEST_CONTENTFUL_PAINT]: { threshold: 2500, enabled: true, current: 2800, status: 'failing' },
      [BudgetMetrics.CUMULATIVE_LAYOUT_SHIFT]: { threshold: 0.1, enabled: true, current: 0.05, status: 'passing' },
      [BudgetMetrics.TOTAL_BLOCKING_TIME]: { threshold: 300, enabled: true, current: 180, status: 'passing' }
    },
    enabled: true,
    createdAt: '2025-01-15T10:00:00Z',
    lastCheck: '2025-01-15T12:30:00Z',
    overallStatus: 'warning'
  },
  {
    id: '2',
    name: 'Volunteer Dashboard Performance',
    url: '/volunteer-dashboard',
    metrics: {
      [BudgetMetrics.RESPONSE_TIME]: { threshold: 800, enabled: true, current: 650, status: 'passing' },
      [BudgetMetrics.PAGE_LOAD_TIME]: { threshold: 2000, enabled: true, current: 1800, status: 'passing' },
      [BudgetMetrics.FIRST_CONTENTFUL_PAINT]: { threshold: 1000, enabled: true, current: 900, status: 'passing' },
      [BudgetMetrics.LARGEST_CONTENTFUL_PAINT]: { threshold: 2000, enabled: true, current: 1600, status: 'passing' },
      [BudgetMetrics.CUMULATIVE_LAYOUT_SHIFT]: { threshold: 0.1, enabled: true, current: 0.03, status: 'passing' },
      [BudgetMetrics.TOTAL_BLOCKING_TIME]: { threshold: 200, enabled: true, current: 120, status: 'passing' }
    },
    enabled: true,
    createdAt: '2025-01-15T10:30:00Z',
    lastCheck: '2025-01-15T12:28:00Z',
    overallStatus: 'passing'
  }
];

// Sample monitoring alerts data
export const SAMPLE_MONITORING_ALERTS = [
  {
    id: '1',
    type: 'performance_budget',
    title: 'Performance Budget Violation',
    message: 'YMCA Homepage LCP exceeds budget threshold',
    severity: 'warning',
    timestamp: '2025-01-15T12:30:00Z',
    resolved: false,
    checkId: '1',
    metric: BudgetMetrics.LARGEST_CONTENTFUL_PAINT,
    threshold: 2500,
    actual: 2800
  },
  {
    id: '2',
    type: 'synthetic_check',
    title: 'Synthetic Check Degraded',
    message: 'Member Portal Login Flow response time increased',
    severity: 'warning',
    timestamp: '2025-01-15T12:25:00Z',
    resolved: false,
    checkId: '3',
    threshold: 2000,
    actual: 3200
  },
  {
    id: '3',
    type: 'synthetic_check',
    title: 'Synthetic Check Recovered',
    message: 'YMCA Homepage Health check back to normal',
    severity: 'info',
    timestamp: '2025-01-15T11:45:00Z',
    resolved: true,
    checkId: '1'
  }
];