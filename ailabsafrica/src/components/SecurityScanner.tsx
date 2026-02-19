import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info,
  Shield,
  Eye,
  Download,
  RefreshCw,
  Settings,
  Zap,
  Lock,
  Unlock,
  AlertCircle,
  Clock,
  TrendingUp,
  TrendingDown
} from 'lucide-react';

interface SecurityVulnerability {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  status: 'open' | 'fixed' | 'ignored';
  discoveredAt: string;
  fixedAt?: string;
  cveId?: string;
  cvssScore?: number;
  remediation: string;
  affectedComponents: string[];
}

interface SecurityScan {
  id: string;
  type: 'full' | 'quick' | 'custom';
  status: 'running' | 'completed' | 'failed';
  startedAt: string;
  completedAt?: string;
  vulnerabilitiesFound: number;
  criticalCount: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
  infoCount: number;
  progress: number;
}

interface SecurityMetrics {
  totalVulnerabilities: number;
  criticalVulnerabilities: number;
  highVulnerabilities: number;
  mediumVulnerabilities: number;
  lowVulnerabilities: number;
  fixedThisMonth: number;
  averageFixTime: number;
  securityScore: number;
  lastScanDate: string;
  nextScanDate: string;
}

const severityColors = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-blue-500',
  info: 'bg-gray-500',
};

const severityIcons = {
  critical: AlertTriangle,
  high: AlertTriangle,
  medium: AlertCircle,
  low: Info,
  info: Info,
};

export default function SecurityScanner() {
  const [currentScan, setCurrentScan] = useState<SecurityScan | null>(null);
  const [vulnerabilities, setVulnerabilities] = useState<SecurityVulnerability[]>([
    {
      id: '1',
      title: 'SQL Injection Vulnerability',
      description: 'User input is not properly sanitized before being used in database queries',
      severity: 'critical',
      category: 'Injection',
      status: 'open',
      discoveredAt: '2024-01-15T10:30:00Z',
      cveId: 'CVE-2024-1234',
      cvssScore: 9.8,
      remediation: 'Use parameterized queries and input validation',
      affectedComponents: ['User Authentication', 'Search Function'],
    },
    {
      id: '2',
      title: 'XSS in User Comments',
      description: 'User comments are not properly escaped, allowing script injection',
      severity: 'high',
      category: 'Cross-Site Scripting',
      status: 'open',
      discoveredAt: '2024-01-14T15:45:00Z',
      cveId: 'CVE-2024-5678',
      cvssScore: 7.2,
      remediation: 'Implement proper output encoding and CSP headers',
      affectedComponents: ['Comment System', 'User Profile'],
    },
    {
      id: '3',
      title: 'Weak Password Policy',
      description: 'Password requirements are not strong enough',
      severity: 'medium',
      category: 'Authentication',
      status: 'open',
      discoveredAt: '2024-01-13T09:15:00Z',
      remediation: 'Enforce stronger password requirements and implement rate limiting',
      affectedComponents: ['User Registration', 'Password Reset'],
    },
  ]);

  const [metrics, setMetrics] = useState<SecurityMetrics>({
    totalVulnerabilities: 3,
    criticalVulnerabilities: 1,
    highVulnerabilities: 1,
    mediumVulnerabilities: 1,
    lowVulnerabilities: 0,
    fixedThisMonth: 5,
    averageFixTime: 3.2,
    securityScore: 75,
    lastScanDate: '2024-01-15T10:30:00Z',
    nextScanDate: '2024-01-22T10:30:00Z',
  });

  const [isScanning, setIsScanning] = useState(false);

  const startScan = async (type: 'full' | 'quick' | 'custom') => {
    setIsScanning(true);
    const scan: SecurityScan = {
      id: `scan-${Date.now()}`,
      type,
      status: 'running',
      startedAt: new Date().toISOString(),
      vulnerabilitiesFound: 0,
      criticalCount: 0,
      highCount: 0,
      mediumCount: 0,
      lowCount: 0,
      infoCount: 0,
      progress: 0,
    };
    setCurrentScan(scan);

    // Simulate scan progress
    const interval = setInterval(() => {
      setCurrentScan(prev => {
        if (!prev) return prev;
        const newProgress = Math.min(prev.progress + Math.random() * 20, 100);
        
        if (newProgress >= 100) {
          clearInterval(interval);
          setIsScanning(false);
          return {
            ...prev,
            status: 'completed',
            completedAt: new Date().toISOString(),
            progress: 100,
            vulnerabilitiesFound: Math.floor(Math.random() * 5) + 1,
          };
        }
        
        return { ...prev, progress: newProgress };
      });
    }, 1000);
  };

  const getSeverityIcon = (severity: string) => {
    const IconComponent = severityIcons[severity as keyof typeof severityIcons];
    return <IconComponent className="h-4 w-4" />;
  };

  const getSecurityScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const renderVulnerabilityCard = (vuln: SecurityVulnerability) => (
    <Card key={vuln.id} className="border-l-4 border-l-red-500">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getSeverityIcon(vuln.severity)}
            <CardTitle className="text-lg">{vuln.title}</CardTitle>
            <Badge variant="outline" className="capitalize">{vuln.severity}</Badge>
          </div>
          <div className="flex items-center gap-2">
            {vuln.cvssScore && (
              <Badge variant="secondary">CVSS: {vuln.cvssScore}</Badge>
            )}
            <Badge variant={vuln.status === 'open' ? 'destructive' : 'default'}>
              {vuln.status}
            </Badge>
          </div>
        </div>
        <CardDescription>{vuln.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">Affected Components:</h4>
            <div className="flex flex-wrap gap-2">
              {vuln.affectedComponents.map((component, index) => (
                <Badge key={index} variant="outline">{component}</Badge>
              ))}
            </div>
          </div>
          
          <div>
            <h4 className="font-medium mb-2">Remediation:</h4>
            <p className="text-sm text-muted-foreground">{vuln.remediation}</p>
          </div>
          
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Discovered: {new Date(vuln.discoveredAt).toLocaleDateString()}</span>
            {vuln.cveId && <span>CVE: {vuln.cveId}</span>}
          </div>
          
          <div className="flex gap-2">
            <Button size="sm" variant="outline">
              <Eye className="h-4 w-4 mr-1" />
              View Details
            </Button>
            <Button size="sm" variant="outline">
              <CheckCircle className="h-4 w-4 mr-1" />
              Mark Fixed
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Security Scanner</h2>
          <p className="text-muted-foreground">Automated vulnerability detection and security monitoring</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export Report
          </Button>
          <Button 
            onClick={() => startScan('quick')} 
            disabled={isScanning}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isScanning ? 'animate-spin' : ''}`} />
            {isScanning ? 'Scanning...' : 'Quick Scan'}
          </Button>
          <Button 
            onClick={() => startScan('full')} 
            disabled={isScanning}
            variant="default"
            className="flex items-center gap-2"
          >
            <Shield className="h-4 w-4" />
            Full Scan
          </Button>
        </div>
      </div>

      {/* Security Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Security Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className={`text-4xl font-bold ${getSecurityScoreColor(metrics.securityScore)}`}>
              {metrics.securityScore}/100
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between text-sm mb-2">
                <span>Overall Security</span>
                <span>{metrics.securityScore}%</span>
              </div>
              <Progress value={metrics.securityScore} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Scan Progress */}
      {currentScan && currentScan.status === 'running' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="h-5 w-5 animate-spin" />
              Security Scan in Progress
            </CardTitle>
            <CardDescription>
              {currentScan.type.charAt(0).toUpperCase() + currentScan.type.slice(1)} scan started at{' '}
              {new Date(currentScan.startedAt).toLocaleTimeString()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span>Progress</span>
                <span>{Math.round(currentScan.progress)}%</span>
              </div>
              <Progress value={currentScan.progress} className="h-2" />
              <div className="text-sm text-muted-foreground">
                Scanning components and checking for vulnerabilities...
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Security Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <div>
                <p className="text-xs text-muted-foreground">Critical</p>
                <p className="text-lg font-bold">{metrics.criticalVulnerabilities}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-orange-500" />
              <div>
                <p className="text-xs text-muted-foreground">High</p>
                <p className="text-lg font-bold">{metrics.highVulnerabilities}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-yellow-500" />
              <div>
                <p className="text-xs text-muted-foreground">Medium</p>
                <p className="text-lg font-bold">{metrics.mediumVulnerabilities}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-xs text-muted-foreground">Fixed This Month</p>
                <p className="text-lg font-bold">{metrics.fixedThisMonth}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Vulnerabilities */}
      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all">All ({vulnerabilities.length})</TabsTrigger>
          <TabsTrigger value="critical">Critical ({vulnerabilities.filter(v => v.severity === 'critical').length})</TabsTrigger>
          <TabsTrigger value="high">High ({vulnerabilities.filter(v => v.severity === 'high').length})</TabsTrigger>
          <TabsTrigger value="medium">Medium ({vulnerabilities.filter(v => v.severity === 'medium').length})</TabsTrigger>
          <TabsTrigger value="fixed">Fixed ({vulnerabilities.filter(v => v.status === 'fixed').length})</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          {vulnerabilities.map(renderVulnerabilityCard)}
        </TabsContent>

        <TabsContent value="critical" className="space-y-4">
          {vulnerabilities.filter(v => v.severity === 'critical').map(renderVulnerabilityCard)}
        </TabsContent>

        <TabsContent value="high" className="space-y-4">
          {vulnerabilities.filter(v => v.severity === 'high').map(renderVulnerabilityCard)}
        </TabsContent>

        <TabsContent value="medium" className="space-y-4">
          {vulnerabilities.filter(v => v.severity === 'medium').map(renderVulnerabilityCard)}
        </TabsContent>

        <TabsContent value="fixed" className="space-y-4">
          {vulnerabilities.filter(v => v.status === 'fixed').map(renderVulnerabilityCard)}
        </TabsContent>
      </Tabs>

      {/* Security Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Security Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 bg-yellow-50 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-yellow-800">Fix Critical Vulnerabilities First</h4>
                <p className="text-sm text-yellow-700 mt-1">
                  Address the SQL injection vulnerability immediately as it poses the highest risk.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg">
              <Info className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-800">Implement Security Headers</h4>
                <p className="text-sm text-blue-700 mt-1">
                  Add Content Security Policy (CSP) headers to prevent XSS attacks.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-green-800">Regular Security Scans</h4>
                <p className="text-sm text-green-700 mt-1">
                  Schedule automated security scans weekly to catch new vulnerabilities early.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
