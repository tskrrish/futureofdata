import { useEffect, useRef } from 'react';
import telemetry from '../services/telemetry.js';
import metrics from '../services/metrics.js';

export function useTelemetry() {
  const trackingRef = useRef({
    pageStartTime: Date.now(),
    interactions: 0
  });

  useEffect(() => {
    // Track page view on mount
    const currentPage = window.location.pathname;
    telemetry.trackPageView(currentPage);
    metrics.trackPageView(currentPage);

    // Track page leave and time spent
    return () => {
      const startTime = trackingRef.current.pageStartTime;
      const timeSpent = Date.now() - startTime;
      metrics.trackTimeSpent(currentPage, timeSpent);
    };
  }, []);

  const trackEvent = (event, properties = {}) => {
    trackingRef.current.interactions++;
    return telemetry.track(event, properties);
  };

  const trackUserAction = (action, target, metadata = {}) => {
    trackingRef.current.interactions++;
    return metrics.trackUserAction(action, target, metadata);
  };

  const trackPerformance = (name, duration) => {
    return telemetry.trackPerformance(name, duration);
  };

  const trackError = (error, context = {}) => {
    return telemetry.trackError(error, context);
  };

  return {
    trackEvent,
    trackUserAction,
    trackPerformance,
    trackError,
    getSessionStats: () => ({
      interactions: trackingRef.current.interactions,
      sessionDuration: Date.now() - trackingRef.current.pageStartTime
    })
  };
}

export function usePageTracking(pageName) {
  const startTime = useRef(Date.now());

  useEffect(() => {
    telemetry.trackPageView(pageName);
    metrics.trackPageView(pageName);

    return () => {
      const start = startTime.current;
      const duration = Date.now() - start;
      metrics.trackTimeSpent(pageName, duration);
    };
  }, [pageName]);
}

export function usePerformanceTracking() {
  const measureSync = (name, fn) => {
    return metrics.measurePerformance(name, fn);
  };

  const measureAsync = async (name, asyncFn) => {
    return await metrics.measureAsyncPerformance(name, asyncFn);
  };

  return { measureSync, measureAsync };
}