import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, TrendingDown, Users, MessageSquare, Target, Clock } from 'lucide-react';

const ABTestDashboard = () => {
  const [activeTests, setActiveTests] = useState([]);
  const [testResults, setTestResults] = useState({});
  const [selectedTest, setSelectedTest] = useState(null);
  const [loading, setLoading] = useState(true);

  // Mock data - in production, fetch from API
  const mockTests = [
    {
      id: 'test-001',
      name: 'Youth Mentorship Campaign 2025',
      status: 'active',
      startDate: '2025-01-15',
      endDate: '2025-02-15',
      participants: 850,
      variants: [
        { id: 'control', name: 'Standard Message', participants: 425 },
        { id: 'urgent', name: 'Urgent Appeal', participants: 425 }
      ]
    },
    {
      id: 'test-002', 
      name: 'Weekend Event Promotion',
      status: 'completed',
      startDate: '2025-01-01',
      endDate: '2025-01-31',
      participants: 1200,
      variants: [
        { id: 'control', name: 'Morning Send', participants: 400 },
        { id: 'evening', name: 'Evening Send', participants: 400 },
        { id: 'personal', name: 'Personalized', participants: 400 }
      ]
    }
  ];

  const mockResults = {
    'test-001': {
      variants: [
        {
          id: 'control',
          name: 'Standard Message',
          participants: 425,
          messagesSent: 425,
          messagesOpened: 297,
          clicked: 127,
          registered: 85,
          attended: 68,
          turnoutRate: 16.0,
          engagementRate: 69.9,
          conversionRate: 20.0,
          confidenceInterval: [14.2, 17.8],
          pValue: 0.032,
          isSignificant: true
        },
        {
          id: 'urgent',
          name: 'Urgent Appeal',
          participants: 425,
          messagesSent: 425,
          messagesOpened: 340,
          clicked: 178,
          registered: 95,
          attended: 82,
          turnoutRate: 19.3,
          engagementRate: 80.0,
          conversionRate: 22.4,
          confidenceInterval: [17.1, 21.5],
          pValue: 0.032,
          isSignificant: true
        }
      ],
      timeline: [
        { date: '2025-01-15', control: 0, urgent: 0 },
        { date: '2025-01-18', control: 12, urgent: 15 },
        { date: '2025-01-21', control: 28, urgent: 34 },
        { date: '2025-01-24', control: 45, urgent: 58 },
        { date: '2025-01-27', control: 58, urgent: 71 },
        { date: '2025-01-30', control: 68, urgent: 82 }
      ],
      bayesian: {
        probabilityVariantBetter: 0.87,
        expectedLift: 20.6,
        riskOfLoss: 0.13
      }
    }
  };

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setActiveTests(mockTests);
      setTestResults(mockResults);
      setSelectedTest('test-001');
      setLoading(false);
    }, 1000);
  }, []);

  const StatCard = ({ title, value, change, icon: Icon, color = 'blue' }) => (
    <Card className="p-4">
      <CardContent className="flex items-center justify-between p-0">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold">{value}</span>
            {change && (
              <span className={`flex items-center text-sm ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {change > 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                {Math.abs(change)}%
              </span>
            )}
          </div>
        </div>
        <Icon className={`h-8 w-8 text-${color}-500`} />
      </CardContent>
    </Card>
  );

  const VariantCard = ({ variant, isWinner = false }) => (
    <Card className={`p-4 ${isWinner ? 'ring-2 ring-green-500' : ''}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          {variant.name}
          {isWinner && <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded">Winner</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Turnout Rate</span>
            <span className="font-semibold">{variant.turnoutRate}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Engagement Rate</span>
            <span className="font-semibold">{variant.engagementRate}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Conversion Rate</span>
            <span className="font-semibold">{variant.conversionRate}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Attended</span>
            <span className="font-semibold">{variant.attended}/{variant.participants}</span>
          </div>
          <div className="text-xs text-gray-500 mt-2">
            95% CI: {variant.confidenceInterval[0]}% - {variant.confidenceInterval[1]}%
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const selectedTestData = selectedTest ? testResults[selectedTest] : null;
  const testInfo = activeTests.find(t => t.id === selectedTest);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">A/B Test Dashboard</h1>
          <p className="text-gray-600">Monitor campaign message impact on volunteer turnout</p>
        </div>
        <select 
          value={selectedTest || ''} 
          onChange={(e) => setSelectedTest(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          {activeTests.map(test => (
            <option key={test.id} value={test.id}>{test.name}</option>
          ))}
        </select>
      </div>

      {selectedTestData && testInfo && (
        <>
          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="Total Participants"
              value={testInfo.participants}
              icon={Users}
              color="blue"
            />
            <StatCard
              title="Messages Sent"
              value={selectedTestData.variants.reduce((sum, v) => sum + v.messagesSent, 0)}
              icon={MessageSquare}
              color="purple"
            />
            <StatCard
              title="Total Attended"
              value={selectedTestData.variants.reduce((sum, v) => sum + v.attended, 0)}
              change={20.6}
              icon={Target}
              color="green"
            />
            <StatCard
              title="Days Running"
              value={Math.floor((new Date() - new Date(testInfo.startDate)) / (1000 * 60 * 60 * 24))}
              icon={Clock}
              color="orange"
            />
          </div>

          {/* Variant Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {selectedTestData.variants.map((variant, index) => (
              <VariantCard 
                key={variant.id} 
                variant={variant} 
                isWinner={index === 1 && variant.turnoutRate > selectedTestData.variants[0].turnoutRate}
              />
            ))}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Turnout Timeline */}
            <Card>
              <CardHeader>
                <CardTitle>Turnout Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={selectedTestData.timeline}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="control" stroke="#8884d8" strokeWidth={2} />
                    <Line type="monotone" dataKey="urgent" stroke="#82ca9d" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Conversion Funnel */}
            <Card>
              <CardHeader>
                <CardTitle>Conversion Funnel</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={selectedTestData.variants} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={100} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="messagesOpened" fill="#8884d8" name="Opened" />
                    <Bar dataKey="clicked" fill="#82ca9d" name="Clicked" />
                    <Bar dataKey="registered" fill="#ffc658" name="Registered" />
                    <Bar dataKey="attended" fill="#ff7300" name="Attended" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Statistical Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Statistical Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">Frequentist Results</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>P-value:</span>
                      <span className="font-mono">{selectedTestData.variants[1].pValue}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Significant:</span>
                      <span className={selectedTestData.variants[1].isSignificant ? 'text-green-600' : 'text-red-600'}>
                        {selectedTestData.variants[1].isSignificant ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Lift:</span>
                      <span className="font-semibold">
                        +{((selectedTestData.variants[1].turnoutRate / selectedTestData.variants[0].turnoutRate - 1) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">Bayesian Results</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Prob. Better:</span>
                      <span className="font-semibold">{(selectedTestData.bayesian.probabilityVariantBetter * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Expected Lift:</span>
                      <span className="font-semibold">+{selectedTestData.bayesian.expectedLift.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Risk of Loss:</span>
                      <span className="font-semibold">{(selectedTestData.bayesian.riskOfLoss * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">Recommendation</h3>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-green-800 font-semibold">Implement Urgent Appeal</p>
                    <p className="text-green-700 text-sm mt-1">
                      Strong evidence shows 20.6% improvement in turnout with 87% confidence.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Test Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Test Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold mb-3">Test Details</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Test ID:</span>
                      <span className="font-mono">{selectedTest}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Start Date:</span>
                      <span>{testInfo.startDate}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>End Date:</span>
                      <span>{testInfo.endDate}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <span className={`px-2 py-1 rounded text-xs ${testInfo.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {testInfo.status}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">Message Variants</h3>
                  <div className="space-y-3">
                    {selectedTestData.variants.map(variant => (
                      <div key={variant.id} className="p-3 border rounded-lg">
                        <div className="font-medium">{variant.name}</div>
                        <div className="text-sm text-gray-600 mt-1">
                          {variant.id === 'control' ? 
                            'Standard professional invitation to volunteer' :
                            'Urgent appeal emphasizing community need'
                          }
                        </div>
                        <div className="text-xs text-gray-500 mt-2">
                          Sample size: {variant.participants}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default ABTestDashboard;