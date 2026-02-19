import React, { useState, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Shield,
  FileText,
  TrendingUp,
  Users,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  Activity,
  BarChart3,
  Settings,
  Zap,
  ChevronRight
} from 'lucide-react';
import { insuranceApi, InsuranceAnalytics, InsuranceCapability } from '@/lib/insurance-api';
import { toast } from 'sonner';

const Insurance: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [capabilities, setCapabilities] = useState<InsuranceCapability[]>([]);
  const [analytics, setAnalytics] = useState<InsuranceAnalytics | null>(null);
  const [moduleInitialized, setModuleInitialized] = useState(false);

  // Test data for demonstration
  const [testClaimData, setTestClaimData] = useState({
    policy_id: 'P001',
    customer_id: 'C001',
    claim_type: 'Auto Accident',
    claim_amount: 5000,
    incident_date: '2024-01-15'
  });

  const [testPolicyData, setTestPolicyData] = useState({
    customer_id: 'C001',
    policy_type: 'Auto Insurance',
    coverage_amount: 50000,
    premium_amount: 1200,
    start_date: '2024-01-01',
    end_date: '2024-12-31'
  });

  useEffect(() => {
    loadInsuranceData();
  }, []);

  const loadInsuranceData = async () => {
    setLoading(true);
    try {
      // Initialize module if not already done
      await insuranceApi.initializeModule({
        claims_processing: { automation_enabled: true },
        policy_management: { automation_enabled: true },
        fraud_detection: { automation_enabled: true }
      });
      setModuleInitialized(true);

      // Load capabilities and analytics
      const [capabilitiesResponse, analyticsResponse] = await Promise.all([
        insuranceApi.getCapabilities(),
        insuranceApi.getAnalytics()
      ]);

      if (capabilitiesResponse.success) {
        setCapabilities(capabilitiesResponse.data || []);
      }

      if (analyticsResponse.success) {
        setAnalytics(analyticsResponse.data || null);
      }
    } catch (error) {
      console.error('Failed to load insurance data:', error);
      toast.error('Failed to load insurance data');
    } finally {
      setLoading(false);
    }
  };

  const handleProcessClaim = async () => {
    setLoading(true);
    try {
      const response = await insuranceApi.processClaim(testClaimData);
      if (response.success) {
        toast.success('Claim processed successfully');
        loadInsuranceData(); // Refresh analytics
      } else {
        toast.error('Failed to process claim');
      }
    } catch (error) {
      console.error('Failed to process claim:', error);
      toast.error('Failed to process claim');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePolicy = async () => {
    setLoading(true);
    try {
      const response = await insuranceApi.createPolicy(testPolicyData);
      if (response.success) {
        toast.success('Policy created successfully');
        loadInsuranceData(); // Refresh analytics
      } else {
        toast.error('Failed to create policy');
      }
    } catch (error) {
      console.error('Failed to create policy:', error);
      toast.error('Failed to create policy');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeFraud = async () => {
    setLoading(true);
    try {
      const response = await insuranceApi.analyzeFraud('CL001');
      if (response.success) {
        toast.success('Fraud analysis completed');
      } else {
        toast.error('Failed to analyze fraud');
      }
    } catch (error) {
      console.error('Failed to analyze fraud:', error);
      toast.error('Failed to analyze fraud');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateQuote = async () => {
    setLoading(true);
    try {
      const response = await insuranceApi.generateQuote('C001', {
        coverage_type: 'Life Insurance',
        coverage_amount: 100000,
        term: '20 years'
      });
      if (response.success) {
        toast.success('Quote generated successfully');
      } else {
        toast.error('Failed to generate quote');
      }
    } catch (error) {
      console.error('Failed to generate quote:', error);
      toast.error('Failed to generate quote');
    } finally {
      setLoading(false);
    }
  };

  const handleTestDocumentManagement = async () => {
    setLoading(true);
    try {
      const response = await insuranceApi.processDocument('DOC001', {
        document_type: 'Medical Records',
        content: 'Sample medical document content',
        metadata: { patient_id: 'C001', exam_date: '2024-01-15' }
      });
      if (response.success) {
        toast.success('Document processed successfully');
      } else {
        toast.error('Failed to process document');
      }
    } catch (error) {
      console.error('Failed to process document:', error);
      toast.error('Failed to process document');
    } finally {
      setLoading(false);
    }
  };

  const handleTestCommunicationHub = async () => {
    setLoading(true);
    try {
      const response = await insuranceApi.setupCommunicationProfile('C001', {
        preferred_channels: ['email', 'sms'],
        communication_frequency: 'weekly',
        opt_out_types: ['marketing'],
        language: 'en'
      });
      if (response.success) {
        toast.success('Communication profile setup successfully');
      } else {
        toast.error('Failed to setup communication profile');
      }
    } catch (error) {
      console.error('Failed to setup communication profile:', error);
      toast.error('Failed to setup communication profile');
    } finally {
      setLoading(false);
    }
  };

  const getCapabilityIcon = (category: string) => {
    switch (category) {
      case 'processing': return <FileText className="h-4 w-4" />;
      case 'assessment': return <TrendingUp className="h-4 w-4" />;
      case 'management': return <Settings className="h-4 w-4" />;
      case 'security': return <Shield className="h-4 w-4" />;
      case 'service': return <Users className="h-4 w-4" />;
      case 'compliance': return <CheckCircle className="h-4 w-4" />;
      case 'communication': return <Activity className="h-4 w-4" />;
      case 'billing': return <DollarSign className="h-4 w-4" />;
      default: return <Zap className="h-4 w-4" />;
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />

      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 space-y-8">
          {/* Header */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Shield className="h-6 w-6 text-indigo-600" />
              </div>
              <div>
                <h1 className="text-3xl font-bold">Insurance Automation</h1>
                <p className="text-gray-600">
                  Comprehensive insurance automation capabilities from claims to compliance
                </p>
              </div>
            </div>

            {!moduleInitialized && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  <span className="text-sm text-yellow-800">
                    Insurance module not initialized. Click "Refresh Data" to initialize.
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Analytics Overview */}
          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Policies</CardTitle>
                  <FileText className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{analytics.policy_analytics.total_policies}</div>
                  <p className="text-xs text-gray-600">
                    {analytics.policy_analytics.active_policies} active
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Claims</CardTitle>
                  <AlertTriangle className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{analytics.claims_analytics.total_claims}</div>
                  <p className="text-xs text-gray-600">
                    {analytics.claims_analytics.pending_claims} pending
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Customers</CardTitle>
                  <Users className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{analytics.customer_analytics.total_customers}</div>
                  <p className="text-xs text-gray-600">
                    {analytics.customer_analytics.average_policies_per_customer.toFixed(1)} avg policies
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Fraud Detection</CardTitle>
                  <Shield className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{(analytics.risk_analytics.fraud_detection_rate * 100).toFixed(0)}%</div>
                  <p className="text-xs text-gray-600">
                    Detection rate
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          <Tabs defaultValue="capabilities" className="space-y-6">
            <TabsList>
              <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
              <TabsTrigger value="testing">Testing</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
            </TabsList>

            {/* Capabilities Tab */}
            <TabsContent value="capabilities" className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Available Capabilities</h2>
                <Button onClick={loadInsuranceData} disabled={loading}>
                  {loading ? <Clock className="h-4 w-4 mr-2 animate-spin" /> : <Activity className="h-4 w-4 mr-2" />}
                  Refresh Data
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {capabilities.map((capability, index) => (
                  <Card key={index} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getCapabilityIcon(capability.settings.category)}
                          <Badge variant={capability.enabled ? "default" : "secondary"}>
                            {capability.enabled ? "Enabled" : "Disabled"}
                          </Badge>
                        </div>
                      </div>
                      <CardTitle className="text-lg">{capability.name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="mb-3">
                        {capability.description}
                      </CardDescription>
                      <div className="text-sm text-gray-600">
                        <div className="flex items-center gap-1 mb-1">
                          <span className="font-medium">Category:</span>
                          <span className="capitalize">{capability.settings.category}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="font-medium">Auth Required:</span>
                          <span>{capability.settings.requires_auth ? "Yes" : "No"}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* Testing Tab */}
            <TabsContent value="testing" className="space-y-6">
              <h2 className="text-xl font-semibold">Test Insurance Operations</h2>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Claims Processing Test */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Process Claim
                    </CardTitle>
                    <CardDescription>
                      Test the claims processing automation
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="policy_id">Policy ID</Label>
                        <Input
                          id="policy_id"
                          value={testClaimData.policy_id}
                          onChange={(e) => setTestClaimData({...testClaimData, policy_id: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="customer_id">Customer ID</Label>
                        <Input
                          id="customer_id"
                          value={testClaimData.customer_id}
                          onChange={(e) => setTestClaimData({...testClaimData, customer_id: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="claim_type">Claim Type</Label>
                        <Input
                          id="claim_type"
                          value={testClaimData.claim_type}
                          onChange={(e) => setTestClaimData({...testClaimData, claim_type: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="claim_amount">Claim Amount</Label>
                        <Input
                          id="claim_amount"
                          type="number"
                          value={testClaimData.claim_amount}
                          onChange={(e) => setTestClaimData({...testClaimData, claim_amount: Number(e.target.value)})}
                        />
                      </div>
                    </div>
                    <Button onClick={handleProcessClaim} disabled={loading} className="w-full">
                      {loading ? <Clock className="h-4 w-4 mr-2 animate-spin" /> : null}
                      Process Claim
                    </Button>
                  </CardContent>
                </Card>

                {/* Policy Creation Test */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      Create Policy
                    </CardTitle>
                    <CardDescription>
                      Test the policy creation automation
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="policy_customer_id">Customer ID</Label>
                        <Input
                          id="policy_customer_id"
                          value={testPolicyData.customer_id}
                          onChange={(e) => setTestPolicyData({...testPolicyData, customer_id: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="policy_type">Policy Type</Label>
                        <Input
                          id="policy_type"
                          value={testPolicyData.policy_type}
                          onChange={(e) => setTestPolicyData({...testPolicyData, policy_type: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="coverage_amount">Coverage Amount</Label>
                        <Input
                          id="coverage_amount"
                          type="number"
                          value={testPolicyData.coverage_amount}
                          onChange={(e) => setTestPolicyData({...testPolicyData, coverage_amount: Number(e.target.value)})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="premium_amount">Premium Amount</Label>
                        <Input
                          id="premium_amount"
                          type="number"
                          value={testPolicyData.premium_amount}
                          onChange={(e) => setTestPolicyData({...testPolicyData, premium_amount: Number(e.target.value)})}
                        />
                      </div>
                    </div>
                    <Button onClick={handleCreatePolicy} disabled={loading} className="w-full">
                      {loading ? <Clock className="h-4 w-4 mr-2 animate-spin" /> : null}
                      Create Policy
                    </Button>
                  </CardContent>
                </Card>

                {/* Quick Actions */}
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>Quick Actions</CardTitle>
                    <CardDescription>
                      Test other insurance automation capabilities
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <Button variant="outline" onClick={handleAnalyzeFraud} disabled={loading}>
                        <AlertTriangle className="h-4 w-4 mr-2" />
                        Analyze Fraud
                      </Button>
                      <Button variant="outline" onClick={handleGenerateQuote} disabled={loading}>
                        <DollarSign className="h-4 w-4 mr-2" />
                        Generate Quote
                      </Button>
                      <Button variant="outline" onClick={handleTestDocumentManagement} disabled={loading}>
                        <FileText className="h-4 w-4 mr-2" />
                        Process Document
                      </Button>
                      <Button variant="outline" onClick={handleTestCommunicationHub} disabled={loading}>
                        <Activity className="h-4 w-4 mr-2" />
                        Communication Hub
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Analytics Tab */}
            <TabsContent value="analytics" className="space-y-6">
              <h2 className="text-xl font-semibold">Insurance Analytics</h2>

              {analytics ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="h-5 w-5" />
                        Policy Analytics
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex justify-between">
                        <span>Total Policies:</span>
                        <span className="font-semibold">{analytics.policy_analytics.total_policies}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Active Policies:</span>
                        <span className="font-semibold">{analytics.policy_analytics.active_policies}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Renewal Rate:</span>
                        <span className="font-semibold">{(analytics.policy_analytics.renewal_rate * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Average Premium:</span>
                        <span className="font-semibold">${analytics.policy_analytics.average_premium.toFixed(2)}</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5" />
                        Claims Analytics
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex justify-between">
                        <span>Total Claims:</span>
                        <span className="font-semibold">{analytics.claims_analytics.total_claims}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Pending Claims:</span>
                        <span className="font-semibold">{analytics.claims_analytics.pending_claims}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Avg Processing Time:</span>
                        <span className="font-semibold">{analytics.claims_analytics.average_processing_time} days</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Approval Rate:</span>
                        <span className="font-semibold">{(analytics.claims_analytics.approval_rate * 100).toFixed(1)}%</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Users className="h-5 w-5" />
                        Customer Analytics
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex justify-between">
                        <span>Total Customers:</span>
                        <span className="font-semibold">{analytics.customer_analytics.total_customers}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Avg Policies/Customer:</span>
                        <span className="font-semibold">{analytics.customer_analytics.average_policies_per_customer.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Satisfaction Score:</span>
                        <span className="font-semibold">{analytics.customer_analytics.customer_satisfaction_score.toFixed(1)}/5</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        Risk Analytics
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex justify-between">
                        <span>Avg Risk Score:</span>
                        <span className="font-semibold">{analytics.risk_analytics.average_risk_score.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Fraud Detection Rate:</span>
                        <span className="font-semibold">{(analytics.risk_analytics.fraud_detection_rate * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Loss Ratio:</span>
                        <span className="font-semibold">{(analytics.risk_analytics.loss_ratio * 100).toFixed(1)}%</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <Card>
                  <CardContent className="text-center py-8">
                    <TrendingUp className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Analytics Data</h3>
                    <p className="text-gray-600 mb-4">
                      Initialize the insurance module to view analytics data.
                    </p>
                    <Button onClick={loadInsuranceData} disabled={loading}>
                      Load Analytics
                    </Button>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default Insurance;