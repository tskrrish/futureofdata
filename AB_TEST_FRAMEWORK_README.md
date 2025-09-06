# A/B Test Framework for Campaign Message Impact on Volunteer Turnout

A comprehensive A/B testing system designed to measure the impact of different campaign messages and schedules on volunteer turnout and engagement. This framework integrates seamlessly with the existing YMCA Volunteer PathFinder system.

## 🎯 Overview

This A/B testing framework allows organizations to:
- Test different message variants (tone, personalization, urgency)
- Experiment with sending schedules (timing, frequency, reminders)
- Measure impact on volunteer turnout, engagement, and retention
- Make data-driven decisions about campaign messaging
- Continuously optimize volunteer recruitment efforts

## 🏗️ Architecture

The framework consists of several key components:

### Core Components

1. **A/B Test Framework** (`ab_test_framework.py`)
   - Test configuration and variant management
   - User assignment and tracking
   - Event collection and storage
   - Statistical result calculation

2. **Campaign Manager** (`campaign_manager.py`)
   - High-level campaign orchestration
   - Message personalization and delivery
   - Turnout tracking integration
   - Performance monitoring

3. **Statistical Analysis** (`statistical_analysis.py`)
   - Robust statistical testing (frequentist and Bayesian)
   - Power analysis and sample size calculations
   - Multi-variant testing support
   - Sequential analysis for early stopping

4. **API Endpoints** (`api_endpoints.py`)
   - RESTful API for managing tests and campaigns
   - Real-time event tracking
   - Performance data retrieval

5. **Dashboard Components** (`ABTestDashboard.jsx`)
   - React-based visualization interface
   - Real-time performance monitoring
   - Statistical significance indicators
   - Variant comparison tools

## 🚀 Features

### Test Types
- **Message Testing**: Compare different message variants (tone, length, personalization)
- **Schedule Testing**: Optimize sending times and frequencies
- **Hybrid Testing**: Combine message and schedule variations

### Metrics Tracked
- **Turnout Rate**: Percentage of contacted users who actually attended events
- **Engagement Rate**: Message open rates, click-through rates
- **Conversion Rate**: Registration rates from initial contact
- **Retention Rate**: Repeat volunteer participation

### Statistical Methods
- Chi-square tests for conversion rates
- T-tests and Mann-Whitney U for continuous metrics
- Bayesian analysis with Beta-Binomial modeling
- Multi-variant ANOVA with Bonferroni correction
- Sequential analysis for early stopping decisions

## 📊 Database Schema

The framework adds several tables to the existing database:

```sql
-- A/B test configurations
ab_tests (id, name, description, test_type, status, start_date, end_date, ...)

-- User assignments to test variants
ab_test_participants (id, test_id, user_id, variant_id, assigned_at, ...)

-- Event tracking for analysis
ab_test_events (id, test_id, user_id, variant_id, event_type, timestamp, ...)

-- Statistical results storage
ab_test_results (id, test_id, variant_id, sample_size, metrics, ...)

-- Campaign management
campaigns (id, name, test_id, status, target_audience, ...)

-- Volunteer turnout tracking
volunteer_turnout_tracking (id, test_id, user_id, event_id, attended, ...)
```

## 🛠️ Setup and Installation

### 1. Database Setup

Run the SQL schema to create required tables:

```bash
# Apply the database schema
psql -d your_database -f ab_test_database_schema.sql
```

### 2. Python Dependencies

Install additional dependencies for statistical analysis:

```bash
pip install scipy numpy pandas
```

### 3. Frontend Components

The dashboard uses React with Recharts for visualization:

```bash
npm install recharts lucide-react
```

### 4. API Integration

The framework automatically integrates with the existing FastAPI application. A/B test endpoints will be available at `/api/ab-tests/*` and `/api/campaigns/*`.

## 📈 Usage Examples

### Creating an A/B Test

```python
from ab_test_framework import ABTestFramework
from campaign_manager import CampaignManager

# Initialize framework
ab_framework = ABTestFramework(database)
campaign_manager = CampaignManager(ab_framework, database)

# Create a campaign with A/B testing
campaign_data = {
    'name': 'Youth Mentorship Drive 2025',
    'description': 'Testing message impact on mentorship volunteer recruitment',
    'channel': 'email',
    'start_date': '2025-02-01T00:00:00',
    'end_date': '2025-03-01T00:00:00',
    'target_audience': {
        'age': {'min': 18, 'max': 65},
        'interests': ['youth development', 'mentoring']
    },
    'created_by': 'campaign_manager'
}

campaign_id = await campaign_manager.create_volunteer_campaign(campaign_data)
await campaign_manager.launch_campaign(campaign_id)
```

### Tracking User Interactions

```python
# Send personalized message
user_profile = {
    'first_name': 'Sarah',
    'interests': 'youth development',
    'city': 'Cincinnati'
}

await campaign_manager.send_personalized_message(
    campaign_id, 'user_123', user_profile
)

# Track engagement
await campaign_manager.track_user_engagement(
    campaign_id, 'user_123', 'message_opened'
)

# Track registration and attendance
event_details = {
    'event_id': 'mentorship_training_001',
    'event_name': 'Youth Mentorship Training',
    'event_date': '2025-02-15T14:00:00',
    'hours': 3
}

await campaign_manager.track_volunteer_registration(
    campaign_id, 'user_123', event_details
)

await campaign_manager.track_volunteer_attendance(
    campaign_id, 'user_123', True, event_details
)
```

### API Usage

```bash
# Create a new A/B test
curl -X POST "http://localhost:8000/api/ab-tests" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Message Tone Test",
    "description": "Testing urgent vs friendly message tones",
    "test_type": "message",
    "start_date": "2025-02-01T00:00:00",
    "end_date": "2025-03-01T00:00:00",
    "primary_metric": "turnout_rate",
    "created_by": "api_user"
  }'

# Get test results
curl "http://localhost:8000/api/ab-tests/{test_id}/results"

# Track an event
curl -X POST "http://localhost:8000/api/ab-tests/track-event" \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "test_123",
    "user_id": "user_456",
    "event_type": "attended",
    "metadata": {"hours": 3, "satisfaction": 4}
  }'
```

## 📊 Dashboard Features

The React dashboard provides:

### Real-Time Monitoring
- Live test performance metrics
- Variant comparison charts
- Statistical significance indicators
- Timeline visualization of results

### Statistical Analysis
- Confidence intervals and p-values
- Bayesian probability assessments
- Effect size calculations
- Power analysis recommendations

### Campaign Management
- Test configuration interface
- Message variant preview
- Target audience settings
- Automated recommendations

## 🔬 Statistical Methodology

### Frequentist Analysis
- **Proportion Tests**: Chi-square tests for conversion rates
- **Continuous Metrics**: Welch's t-test or Mann-Whitney U test
- **Multiple Comparisons**: Bonferroni correction for family-wise error rate
- **Power Analysis**: Sample size recommendations and post-hoc power calculations

### Bayesian Analysis
- **Beta-Binomial Model**: For conversion rate estimation
- **Monte Carlo Simulation**: For credible interval calculation
- **Decision Theory**: Risk assessment and expected value calculations
- **Sequential Updates**: Real-time posterior updates as data arrives

### Quality Assurance
- **Randomization**: Hash-based consistent user assignment
- **A/A Testing**: Capability for sanity checks
- **Multiple Testing**: Proper correction for multiple comparisons
- **Early Stopping**: Sequential analysis with error rate control

## 🎛️ Configuration Options

### Message Variants
- **Tone**: Professional, friendly, urgent, casual
- **Personalization**: None, basic (name/location), advanced (history/interests)
- **Length**: Short, medium, long
- **Call-to-Action**: Various phrases and urgency levels

### Schedule Variants
- **Send Time**: Morning, afternoon, evening schedules
- **Frequency**: One-time, weekly, bi-weekly campaigns
- **Reminders**: Configurable reminder sequences
- **Days of Week**: Optimal day selection

### Target Audiences
- **Demographics**: Age, location, membership status
- **Interests**: Volunteer categories and preferences
- **Behavior**: Past volunteer history and engagement
- **Custom Filters**: Flexible criteria definition

## 📋 Best Practices

### Test Design
1. **Clear Hypotheses**: Define specific, measurable hypotheses
2. **Single Variables**: Test one element at a time when possible
3. **Adequate Power**: Ensure sufficient sample sizes
4. **Randomization**: Verify proper user assignment
5. **Duration**: Run tests long enough to account for weekly cycles

### Statistical Analysis
1. **Pre-Specification**: Define metrics and stopping criteria upfront
2. **Multiple Testing**: Apply appropriate corrections
3. **Practical Significance**: Consider effect sizes, not just p-values
4. **Confidence Intervals**: Report uncertainty ranges
5. **Bayesian Interpretation**: Use Bayesian methods for decision-making

### Implementation
1. **Gradual Rollout**: Start with small percentages
2. **Monitoring**: Watch for unexpected patterns
3. **Documentation**: Record all decisions and changes
4. **Validation**: Verify tracking accuracy
5. **Learning**: Document insights for future tests

## 🚦 Monitoring and Alerts

The framework includes monitoring capabilities:

- **Performance Alerts**: Automatic notifications for significant results
- **Data Quality Checks**: Validation of tracking accuracy
- **Statistical Monitoring**: Sequential analysis for early stopping
- **System Health**: Monitoring of test execution and data collection

## 🔧 Troubleshooting

### Common Issues

1. **Low Statistical Power**
   - Increase sample size
   - Extend test duration
   - Focus on larger effect sizes

2. **Data Quality Problems**
   - Verify tracking implementation
   - Check for selection bias
   - Validate randomization

3. **Inconsistent Results**
   - Look for external factors
   - Check for interaction effects
   - Consider seasonal variations

### Debug Tools

- Test assignment verification endpoints
- Event tracking validation
- Statistical calculation debugging
- Data export for external analysis

## 🔮 Future Enhancements

### Planned Features
1. **Machine Learning Integration**: Automated variant generation
2. **Multi-Armed Bandits**: Dynamic traffic allocation
3. **Segmentation Analysis**: Automatic subgroup identification
4. **Cross-Campaign Learning**: Knowledge transfer between tests
5. **Advanced Personalization**: AI-driven message customization

### Integration Opportunities
1. **Email Service Integration**: Automated sending via SendGrid/Mailgun
2. **SMS Integration**: Text message variant testing
3. **Push Notification Testing**: Mobile app integration
4. **Calendar Integration**: Event scheduling optimization
5. **CRM Integration**: Enhanced user profiling

## 📚 References and Resources

### Statistical Methods
- Kohavi, R., & Longbotham, R. (2017). Online Controlled Experiments and A/B Testing
- VWO A/B Testing Guide: Statistical Significance and Confidence Intervals
- Optimizely Stats Engine: Bayesian A/B Testing

### Implementation Patterns
- Martin Fowler: Feature Toggles and A/B Testing
- Stripe's approach to statistical rigor in A/B testing
- Netflix's experimentation platform design

---

## 📞 Support

For questions or issues with the A/B testing framework:

1. **Documentation**: Check this README and inline code comments
2. **Logs**: Review application logs for error details  
3. **API**: Use the `/api/ab-tests/dashboard-data` endpoint for system status
4. **Database**: Query the A/B test tables directly for debugging

This framework provides a robust foundation for data-driven optimization of volunteer recruitment campaigns. The combination of rigorous statistical methods, comprehensive tracking, and intuitive visualization tools enables organizations to continuously improve their outreach effectiveness.