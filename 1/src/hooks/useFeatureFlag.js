import { useState, useEffect } from 'react';
import featureFlags from '../services/featureFlags.js';
import metrics from '../services/metrics.js';

export function useFeatureFlag(flagName) {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkFlag = async () => {
      setIsLoading(true);
      try {
        await featureFlags.initialize();
        const enabled = featureFlags.evaluate(flagName);
        setIsEnabled(enabled);
        
        // Track feature flag evaluation
        metrics.trackFeatureFlagUsage(flagName, enabled);
      } catch (error) {
        console.error(`Error evaluating feature flag ${flagName}:`, error);
        metrics.trackError(error, { context: 'feature_flag_evaluation', flagName });
        setIsEnabled(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkFlag();
  }, [flagName]);

  return { isEnabled, isLoading };
}

export function useFeatureVariant(flagName, variants = []) {
  const [variant, setVariant] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkVariant = async () => {
      setIsLoading(true);
      try {
        await featureFlags.initialize();
        const selectedVariant = featureFlags.getVariant(flagName, variants);
        setVariant(selectedVariant);
        
        // Track variant selection
        metrics.trackFeatureFlagUsage(flagName, selectedVariant !== null, {
          variant: selectedVariant,
          availableVariants: variants.length
        });
      } catch (error) {
        console.error(`Error getting feature variant ${flagName}:`, error);
        metrics.trackError(error, { context: 'feature_variant_evaluation', flagName });
        setVariant(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkVariant();
  }, [flagName, variants]);

  return { variant, isLoading };
}

export function useAllFeatureFlags() {
  const [flags, setFlags] = useState({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadAllFlags = async () => {
      setIsLoading(true);
      try {
        await featureFlags.initialize();
        const allFlags = featureFlags.getAllFlags();
        setFlags(allFlags);
      } catch (error) {
        console.error('Error loading all feature flags:', error);
        metrics.trackError(error, { context: 'load_all_feature_flags' });
        setFlags({});
      } finally {
        setIsLoading(false);
      }
    };

    loadAllFlags();
  }, []);

  return { flags, isLoading };
}