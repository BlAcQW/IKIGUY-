import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown,
  Users, 
  Target,
  Zap,
  Settings,
  Play,
  Pause,
  Stop,
  Eye,
  BarChart3,
  CheckCircle,
  AlertCircle,
  Plus,
  Edit,
  Trash2,
  Copy,
  Download
} from 'lucide-react';

interface ABTest {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'running' | 'paused' | 'completed';
  trafficSplit: number; // Percentage to variant B
  metric: string;
  hypothesis: string;
  startDate: string;
  endDate?: string;
  variants: {
    A: { name: string; description: string; config: any };
    B: { name: string; description: string; config: any };
  };
  results: {
    A: { users: number; conversions: number; conversionRate: number; avgValue: number };
    B: { users: number; conversions: number; conversionRate: number; avgValue: number };
  };
  significance: number;
  winner?: 'A' | 'B' | null;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export default function ABTestingFramework() {
  const [tests, setTests] = useState<ABTest[]>([
    {
      id: '1',
      name: 'Button Color Test',
      description: 'Testing red vs blue CTA button for better conversion',
      status: 'running',
      trafficSplit: 50,
      metric: 'conversion_rate',
      hypothesis: 'Red buttons will increase conversion rate by 15%',
      startDate: '2024-01-15',
      variants: {
        A: { name: 'Control (Blue)', description: 'Original blue button', config: { color: 'blue' } },
        B: { name: 'Variant (Red)', description: 'New red button', config: { color: 'red' } },
      },
      results: {
        A: { users: 1250, conversions: 125, conversionRate: 10.0, avgValue: 25.50 },
        B: { users: 1250, conversions: 145, conversionRate: 11.6, avgValue: 26.20 },
      },
      significance: 0.95,
      winner: 'B',
    },
    {
      id: '2',
      name: 'Form Layout Test',
      description: 'Testing single column vs two column form layout',
      status: 'draft',
      trafficSplit: 30,
      metric: 'completion_rate',
      hypothesis: 'Two column layout will improve form completion by 20%',
      startDate: '2024-01-20',
      variants: {
        A: { name: 'Control (Single)', description: 'Single column layout', config: { columns: 1 } },
        B: { name: 'Variant (Two)', description: 'Two column layout', config: { columns: 2 } },
      },
      results: {
        A: { users: 0, conversions: 0, conversionRate: 0, avgValue: 0 },
        B: { users: 0, conversions: 0, conversionRate: 0, avgValue: 0 },
      },
      significance: 0,
    },
  ]);

  const [selectedTest, setSelectedTest] = useState<ABTest | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const calculateStatisticalSignificance = (test: ABTest) => {
    // Simplified statistical significance calculation
    const { A, B } = test.results;
    const pooledRate = (A.conversions + B.conversions) / (A.users + B.users);
    const se = Math.sqrt(pooledRate * (1 - pooledRate) * (1/A.users + 1/B.users));
    const z = Math.abs(B.conversionRate - A.conversionRate) / se;
    return Math.min(0.99, 1 - Math.exp(-z * z / 2));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'paused': return 'bg-yellow-500';
      case 'completed': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const startTest = (testId: string) => {
    setTests(tests.map(test => 
      test.id === testId ? { ...test, status: 'running' } : test
    ));
  };

  const pauseTest = (testId: string) => {
    setTests(tests.map(test => 
      test.id === testId ? { ...test, status: 'paused' } : test
    ));
  };

  const stopTest = (testId: string) => {
    setTests(tests.map(test => 
      test.id === testId ? { ...test, status: 'completed', endDate: new Date().toISOString() } : test
    ));
  };

  const renderTestCard = (test: ABTest) => (
    <Card key={test.id} className="cursor-pointer hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{test.name}</CardTitle>
            <CardDescription>{test.description}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor(test.status)}`}></div>
            <Badge variant="outline" className="capitalize">{test.status}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Traffic Split:</span> {test.trafficSplit}% to B
          </div>
          <div>
            <span className="font-medium">Metric:</span> {test.metric.replace('_', ' ')}
          </div>
          <div>
            <span className="font-medium">Start Date:</span> {new Date(test.startDate).toLocaleDateString()}
          </div>
          <div>
            <span className="font-medium">Significance:</span> {(test.significance * 100).toFixed(1)}%
          </div>
        </div>
        
        {test.status === 'running' && (
          <div className="mt-4 flex gap-2">
            <Button size="sm" variant="outline" onClick={() => pauseTest(test.id)}>
              <Pause className="h-4 w-4 mr-1" />
              Pause
            </Button>
            <Button size="sm" variant="outline" onClick={() => stopTest(test.id)}>
              <Stop className="h-4 w-4 mr-1" />
              Stop
            </Button>
          </div>
        )}
        
        {test.status === 'draft' && (
          <div className="mt-4">
            <Button size="sm" onClick={() => startTest(test.id)}>
              <Play className="h-4 w-4 mr-1" />
              Start Test
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderResultsChart = (test: ABTest) => {
    const data = [
      { variant: 'Control (A)', users: test.results.A.users, conversions: test.results.A.conversions, rate: test.results.A.conversionRate },
      { variant: 'Variant (B)', users: test.results.B.users, conversions: test.results.B.conversions, rate: test.results.B.conversionRate },
    ];

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="variant" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="rate" fill="#0088FE" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderTrendChart = (test: ABTest) => {
    const data = [
      { day: 'Day 1', A: 8.5, B: 9.2 },
      { day: 'Day 2', A: 9.1, B: 10.1 },
      { day: 'Day 3', A: 9.8, B: 11.3 },
      { day: 'Day 4', A: 10.2, B: 11.8 },
      { day: 'Day 5', A: 10.0, B: 11.6 },
    ];

    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="day" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="A" stroke="#0088FE" strokeWidth={2} />
          <Line type="monotone" dataKey="B" stroke="#00C49F" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">A/B Testing Framework</h2>
          <p className="text-muted-foreground">Optimize features through experimentation</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export Results
          </Button>
          <Button onClick={() => setIsCreating(true)} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Create Test
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Play className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-xs text-muted-foreground">Active Tests</p>
                <p className="text-lg font-bold">{tests.filter(t => t.status === 'running').length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-500" />
              <div>
                <p className="text-xs text-muted-foreground">Total Participants</p>
                <p className="text-lg font-bold">{tests.reduce((sum, test) => sum + test.results.A.users + test.results.B.users, 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-purple-500" />
              <div>
                <p className="text-xs text-muted-foreground">Winning Tests</p>
                <p className="text-lg font-bold">{tests.filter(t => t.winner).length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-orange-500" />
              <div>
                <p className="text-xs text-muted-foreground">Avg Improvement</p>
                <p className="text-lg font-bold">+12.5%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tests List */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="create">Create Test</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {tests.map(renderTestCard)}
          </div>
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          {tests.filter(t => t.status !== 'draft').map(test => (
            <Card key={test.id}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {test.name}
                  {test.winner && (
                    <Badge variant={test.winner === 'B' ? 'default' : 'secondary'}>
                      {test.winner === 'B' ? 'Variant B Wins' : 'Control Wins'}
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>{test.hypothesis}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Results Summary */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Control (A)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Users:</span>
                          <span className="font-medium">{test.results.A.users.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Conversions:</span>
                          <span className="font-medium">{test.results.A.conversions.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Rate:</span>
                          <span className="font-medium">{test.results.A.conversionRate.toFixed(2)}%</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Variant (B)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Users:</span>
                          <span className="font-medium">{test.results.B.users.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Conversions:</span>
                          <span className="font-medium">{test.results.B.conversions.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Rate:</span>
                          <span className="font-medium">{test.results.B.conversionRate.toFixed(2)}%</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Conversion Rates</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {renderResultsChart(test)}
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Daily Trends</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {renderTrendChart(test)}
                    </CardContent>
                  </Card>
                </div>

                {/* Statistical Significance */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Statistical Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="font-medium">Confidence Level:</span>
                        <div className="text-2xl font-bold text-green-600">
                          {(test.significance * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">Improvement:</span>
                        <div className="text-2xl font-bold text-blue-600">
                          +{((test.results.B.conversionRate - test.results.A.conversionRate) / test.results.A.conversionRate * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="create" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Create New A/B Test</CardTitle>
              <CardDescription>Set up a new experiment to optimize your features</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="test-name">Test Name</Label>
                  <Input id="test-name" placeholder="e.g., Button Color Test" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="metric">Primary Metric</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select metric" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="conversion_rate">Conversion Rate</SelectItem>
                      <SelectItem value="click_rate">Click Rate</SelectItem>
                      <SelectItem value="completion_rate">Completion Rate</SelectItem>
                      <SelectItem value="revenue_per_user">Revenue per User</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="hypothesis">Hypothesis</Label>
                <Textarea 
                  id="hypothesis" 
                  placeholder="e.g., Red buttons will increase conversion rate by 15%"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="traffic-split">Traffic Split (%)</Label>
                  <Input id="traffic-split" type="number" min="1" max="50" defaultValue="50" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="duration">Duration (days)</Label>
                  <Input id="duration" type="number" min="1" defaultValue="14" />
                </div>
              </div>

              <div className="flex gap-2">
                <Button>Create Test</Button>
                <Button variant="outline">Save Draft</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
