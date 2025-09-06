# Telemetry and Feature Flags System

This system provides comprehensive usage telemetry and feature flag management for gradual rollouts with metrics tracking.

## 🚀 Features

### Telemetry System
- **Automatic Event Batching**: Events are batched and sent periodically to reduce server load
- **Session Tracking**: Track user sessions with unique session IDs
- **Performance Monitoring**: Track page load times and function performance  
- **Error Tracking**: Automatic error capture and reporting
- **Custom Events**: Track specific user actions and business metrics
- **Privacy-First**: Configurable data collection with user consent

### Feature Flags System
- **Gradual Rollouts**: Control feature exposure with percentage-based rollouts
- **User Targeting**: Target specific user segments with attributes
- **Real-time Updates**: Feature flags update without app restarts
- **A/B Testing**: Support for feature variants and experiments
- **Metrics Integration**: Automatic tracking of feature flag usage
- **Admin Interface**: Visual management of feature flags and rollouts

## 📊 Usage

### Basic Telemetry Tracking

```jsx
import { useTelemetry } from './hooks/useTelemetry';

function MyComponent() {
  const { trackEvent, trackUserAction, trackPerformance } = useTelemetry();

  const handleClick = () => {
    trackUserAction('button_click', 'save_data', { location: 'dashboard' });
  };

  const handleExport = async () => {
    const startTime = performance.now();
    await exportData();
    trackPerformance('data_export', performance.now() - startTime);
  };

  return <button onClick={handleClick}>Save</button>;
}
```

### Feature Flag Usage

```jsx
import { useFeatureFlag } from './hooks/useFeatureFlag';

function Dashboard() {
  const { isEnabled: enhancedReporting } = useFeatureFlag('enhancedReporting');
  const { isEnabled: advancedFilters } = useFeatureFlag('advancedFilters');

  return (
    <div>
      {enhancedReporting && <EnhancedReportsPanel />}
      {advancedFilters && <AdvancedFilterControls />}
    </div>
  );
}
```

### Feature Variants (A/B Testing)

```jsx
import { useFeatureVariant } from './hooks/useFeatureFlag';

function HeaderComponent() {
  const { variant } = useFeatureVariant('headerDesign', ['classic', 'modern', 'minimal']);

  return (
    <header className={`header header--${variant || 'classic'}`}>
      {/* Different header designs based on variant */}
    </header>
  );
}
```

## 🎛️ Admin Interface

Access the Feature Flag admin panel by:
1. Pressing `Ctrl+Shift+F` on the keyboard, or
2. Clicking the settings icon in the bottom-right corner

### Admin Features:
- **Toggle Features**: Enable/disable features instantly
- **Rollout Control**: Adjust rollout percentages with sliders
- **Real-time Metrics**: View feature flag evaluation counts
- **Success Rates**: Monitor feature adoption and performance
- **Export Data**: Download telemetry metrics for analysis

## 🔧 Configuration

### Default Feature Flags

```javascript
const defaultFlags = {
  newDashboardDesign: { enabled: false, rollout: 0 },
  enhancedReporting: { enabled: false, rollout: 0 },
  realTimeUpdates: { enabled: false, rollout: 0 },
  advancedFiltering: { enabled: false, rollout: 25 },
  exportEnhancements: { enabled: true, rollout: 100 },
  betaFeatures: { enabled: false, rollout: 0 }
};
```

### Gradual Rollout Strategy

The system uses consistent hashing to ensure users have a stable experience:

- **0% rollout**: Feature disabled for all users
- **25% rollout**: Feature enabled for ~25% of users (based on user ID hash)
- **50% rollout**: Feature enabled for ~50% of users
- **100% rollout**: Feature enabled for all users

Users are bucketed consistently, so they won't flip between enabled/disabled states.

## 📈 Metrics Collected

### Telemetry Events
- `page_view`: Track page navigation
- `user_action`: Track button clicks, form submissions, etc.
- `feature_flag_evaluation`: Track when flags are checked
- `feature_usage`: Track specific feature interactions
- `performance`: Track timing metrics
- `error`: Track application errors
- `export`: Track data export events
- `search_behavior`: Track search patterns

### Performance Metrics
- Page load times
- Function execution times
- Network request durations
- Error rates and counts
- Feature flag evaluation performance

### User Behavior Analytics
- Session duration
- Page interaction counts
- Feature adoption rates
- Search effectiveness
- Export usage patterns

## 🔒 Privacy & Security

### Data Collection
- **No PII**: Personal information is never tracked
- **Hashed IDs**: User identifiers are hashed for privacy
- **Configurable**: Telemetry can be disabled per user
- **Local Storage**: Feature flags cached locally to reduce server calls

### Data Retention
- **Batched Sending**: Events sent in batches to reduce network overhead
- **Automatic Cleanup**: Old metrics cleaned up automatically
- **Consent Aware**: Respects user privacy preferences

## 🚀 Deployment

### Server Integration

The system expects these API endpoints:

```
POST /api/telemetry
- Receives batched telemetry events
- Should return 200 OK for successful ingestion

GET /api/feature-flags  
- Returns current feature flag configuration
- Should return JSON with flag definitions
```

### Example Server Response

```json
{
  "enhancedReporting": { "enabled": true, "rollout": 50 },
  "advancedFiltering": { "enabled": true, "rollout": 75 },
  "exportEnhancements": { "enabled": true, "rollout": 100 }
}
```

## 📊 Analytics Integration

The telemetry system can be integrated with analytics platforms:

```javascript
// Example: Send to Google Analytics
telemetry.track('user_action', {
  action: 'button_click',
  target: 'export_data',
  value: recordCount
});

// Example: Send to custom analytics
metrics.exportMetrics(); // Downloads JSON file for analysis
```

## 🧪 Testing Feature Flags

For testing and development:

```javascript
// Force enable a feature
featureFlags.forceEnable('enhancedReporting');

// Force disable a feature  
featureFlags.forceDisable('advancedFiltering');

// Set specific rollout percentage
featureFlags.setRollout('newFeature', 25);
```

## 📱 Responsive Design

The admin panel is responsive and works on:
- Desktop browsers
- Tablet devices  
- Mobile phones (with touch-friendly controls)

## 🔧 Troubleshooting

### Common Issues

1. **Feature flags not loading**
   - Check browser console for API errors
   - Verify `/api/feature-flags` endpoint is accessible

2. **Telemetry not sending**
   - Check network tab for failed POST requests
   - Verify `/api/telemetry` endpoint accepts JSON

3. **Admin panel not appearing**
   - Try keyboard shortcut `Ctrl+Shift+F`
   - Check browser console for JavaScript errors

### Debug Mode

Enable debug logging:

```javascript
window.DEBUG_TELEMETRY = true;
window.DEBUG_FEATURE_FLAGS = true;
```

This will log detailed information about feature flag evaluations and telemetry events to the browser console.

## 🎯 Best Practices

### Feature Flag Management
- **Small Rollouts**: Start with 5-10% rollouts for new features
- **Monitor Metrics**: Watch error rates during rollouts  
- **Quick Rollback**: Be prepared to disable features quickly if issues arise
- **Clean Up**: Remove unused feature flags from code regularly

### Telemetry Best Practices
- **Meaningful Events**: Track business-relevant actions, not every click
- **Performance Impact**: Batch events to minimize performance impact
- **Privacy First**: Never track sensitive user information
- **Error Handling**: Gracefully handle telemetry failures

## 🚀 Future Enhancements

Planned features:
- **Geographic Targeting**: Enable features by user location
- **Time-based Rollouts**: Schedule feature releases
- **Dependency Management**: Define feature flag dependencies  
- **Custom Dashboards**: Build analytics dashboards
- **Automated Rollouts**: ML-driven gradual rollout optimization
- **Integration APIs**: Connect with external feature flag services

---

*Built for YMCA Cincinnati Volunteer Dashboard - Hackathon: Platform for Belonging*