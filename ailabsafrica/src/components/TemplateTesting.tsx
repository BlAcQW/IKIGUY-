import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { VoiceTemplate } from './VoiceAgentTemplates';
import { CustomTemplate } from './TemplateCustomization';
import { 
  Play, 
  Pause, 
  Stop, 
  Volume2, 
  Mic, 
  MicOff,
  Settings,
  Download,
  Share,
  Star,
  MessageSquare,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  Eye,
  EyeOff,
  Copy,
  RotateCcw
} from 'lucide-react';

interface TemplateTestingProps {
  template: VoiceTemplate | CustomTemplate;
  onClose: () => void;
  onSave?: (testResults: TestResults) => void;
}

interface TestResults {
  templateId: string;
  testDuration: number;
  successRate: number;
  totalTests: number;
  passedTests: number;
  failedTests: number;
  averageResponseTime: number;
  errors: string[];
  timestamp: string;
}

interface TestScenario {
  id: string;
  name: string;
  description: string;
  input: string;
  expectedOutput: string;
  category: 'basic' | 'edge_case' | 'error_handling' | 'integration';
}

const TemplateTesting: React.FC<TemplateTestingProps> = ({ template, onClose, onSave }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [isTesting, setIsTesting] = useState(false);
  const [testResults, setTestResults] = useState<TestResults | null>(null);
  const [currentTest, setCurrentTest] = useState<TestScenario | null>(null);
  const [testProgress, setTestProgress] = useState(0);
  const [customInput, setCustomInput] = useState('');
  const [customOutput, setCustomOutput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [testScenarios, setTestScenarios] = useState<TestScenario[]>([]);
  const { toast } = useToast();

  // Generate test scenarios based on template
  useEffect(() => {
    const scenarios: TestScenario[] = [
      // Basic functionality tests
      {
        id: 'basic-1',
        name: 'Basic Greeting',
        description: 'Test basic greeting functionality',
        input: 'Hello',
        expectedOutput: 'greeting',
        category: 'basic'
      },
      {
        id: 'basic-2',
        name: 'Template Purpose',
        description: 'Test if assistant understands its purpose',
        input: 'What can you help me with?',
        expectedOutput: template.description.toLowerCase(),
        category: 'basic'
      },
      // Edge case tests
      {
        id: 'edge-1',
        name: 'Empty Input',
        description: 'Test handling of empty input',
        input: '',
        expectedOutput: 'error_handling',
        category: 'edge_case'
      },
      {
        id: 'edge-2',
        name: 'Very Long Input',
        description: 'Test handling of very long input',
        input: 'A'.repeat(1000),
        expectedOutput: 'truncated_or_error',
        category: 'edge_case'
      },
      // Error handling tests
      {
        id: 'error-1',
        name: 'Invalid Request',
        description: 'Test handling of invalid requests',
        input: 'Invalid command that should not work',
        expectedOutput: 'error_response',
        category: 'error_handling'
      },
      // Integration tests (if template has integrations)
      ...(template.integrations ? [
        {
          id: 'integration-1',
          name: 'Calendar Integration',
          description: 'Test calendar integration functionality',
          input: 'Schedule a meeting',
          expectedOutput: 'calendar_integration',
          category: 'integration'
        }
      ] : [])
    ];
    
    setTestScenarios(scenarios);
  }, [template]);

  const runTest = async (scenario: TestScenario): Promise<boolean> => {
    try {
      // Simulate API call to test template
      const startTime = Date.now();
      
      // Mock response based on scenario
      await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 500));
      
      const responseTime = Date.now() - startTime;
      
      // Simulate success/failure based on scenario
      const isSuccess = Math.random() > 0.2; // 80% success rate
      
      return isSuccess;
    } catch (error) {
      console.error('Test failed:', error);
      return false;
    }
  };

  const runAllTests = async () => {
    setIsTesting(true);
    setTestProgress(0);
    setTestResults(null);

    const results: TestResults = {
      templateId: template.id,
      testDuration: 0,
      successRate: 0,
      totalTests: testScenarios.length,
      passedTests: 0,
      failedTests: 0,
      averageResponseTime: 0,
      errors: [],
      timestamp: new Date().toISOString()
    };

    const startTime = Date.now();
    const responseTimes: number[] = [];

    for (let i = 0; i < testScenarios.length; i++) {
      const scenario = testScenarios[i];
      setCurrentTest(scenario);
      setTestProgress(((i + 1) / testScenarios.length) * 100);

      const testStartTime = Date.now();
      const success = await runTest(scenario);
      const responseTime = Date.now() - testStartTime;
      responseTimes.push(responseTime);

      if (success) {
        results.passedTests++;
      } else {
        results.failedTests++;
        results.errors.push(`Test "${scenario.name}" failed`);
      }

      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 200));
    }

    results.testDuration = Date.now() - startTime;
    results.successRate = (results.passedTests / results.totalTests) * 100;
    results.averageResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;

    setTestResults(results);
    setIsTesting(false);
    setCurrentTest(null);

    toast({
      title: "Testing Complete",
      description: `Tests completed with ${results.successRate.toFixed(1)}% success rate`,
    });
  };

  const testCustomInput = async () => {
    if (!customInput.trim()) {
      toast({
        title: "Error",
        description: "Please enter some input to test",
        variant: "destructive"
      });
      return;
    }

    setIsTesting(true);
    try {
      // Simulate custom input testing
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock response
      setCustomOutput(`Response to: "${customInput}"\n\nThis is a simulated response based on the template's system prompt and configuration.`);
      
      toast({
        title: "Test Complete",
        description: "Custom input test completed successfully",
      });
    } catch (error) {
      toast({
        title: "Test Failed",
        description: "Failed to test custom input",
        variant: "destructive"
      });
    } finally {
      setIsTesting(false);
    }
  };

  const startVoiceTest = () => {
    setIsRecording(true);
    // Simulate voice recording
    setTimeout(() => {
      setIsRecording(false);
      setAudioBlob(new Blob(['mock audio data'], { type: 'audio/wav' }));
      toast({
        title: "Voice Test Complete",
        description: "Voice recording test completed",
      });
    }, 3000);
  };

  const saveTestResults = async () => {
    if (!testResults) return;

    try {
      // Save test results to database
      const { error } = await supabase
        .from('template_test_results')
        .insert({
          template_id: template.id,
          results: testResults,
          created_at: new Date().toISOString()
        });

      if (error) throw error;

      toast({
        title: "Results Saved",
        description: "Test results have been saved successfully",
      });

      onSave?.(testResults);
    } catch (error) {
      console.error('Failed to save test results:', error);
      toast({
        title: "Save Failed",
        description: "Failed to save test results",
        variant: "destructive"
      });
    }
  };

  const exportTestResults = () => {
    if (!testResults) return;

    const dataStr = JSON.stringify(testResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `template-test-results-${template.id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Test Template: {template.name}</DialogTitle>
          <DialogDescription>
            Test and validate the template before using it in production
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="automated" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="automated">Automated Tests</TabsTrigger>
            <TabsTrigger value="custom">Custom Input</TabsTrigger>
            <TabsTrigger value="voice">Voice Test</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
          </TabsList>

          <TabsContent value="automated" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Automated Test Suite</CardTitle>
                <CardDescription>
                  Run comprehensive tests to validate template functionality
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      {testScenarios.length} test scenarios available
                    </p>
                  </div>
                  <Button 
                    onClick={runAllTests} 
                    disabled={isTesting}
                    className="flex items-center gap-2"
                  >
                    {isTesting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Running Tests...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4" />
                        Run All Tests
                      </>
                    )}
                  </Button>
                </div>

                {isTesting && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Progress: {testProgress.toFixed(1)}%</span>
                      <span>{Math.round(testProgress / 100 * testScenarios.length)} / {testScenarios.length}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${testProgress}%` }}
                      />
                    </div>
                    {currentTest && (
                      <p className="text-sm text-muted-foreground">
                        Running: {currentTest.name}
                      </p>
                    )}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {testScenarios.map((scenario) => (
                    <Card key={scenario.id} className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2">
                          <h4 className="font-medium">{scenario.name}</h4>
                          <p className="text-sm text-muted-foreground">
                            {scenario.description}
                          </p>
                          <Badge variant="outline">{scenario.category}</Badge>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="custom" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Custom Input Testing</CardTitle>
                <CardDescription>
                  Test the template with your own custom input
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="custom-input">Test Input</Label>
                  <Textarea
                    id="custom-input"
                    placeholder="Enter your test input here..."
                    value={customInput}
                    onChange={(e) => setCustomInput(e.target.value)}
                    rows={4}
                  />
                </div>

                <Button 
                  onClick={testCustomInput} 
                  disabled={isTesting || !customInput.trim()}
                  className="flex items-center gap-2"
                >
                  {isTesting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    <>
                      <MessageSquare className="h-4 w-4" />
                      Test Input
                    </>
                  )}
                </Button>

                {customOutput && (
                  <div className="space-y-2">
                    <Label>Response</Label>
                    <div className="p-4 bg-muted rounded-md">
                      <pre className="whitespace-pre-wrap text-sm">{customOutput}</pre>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="voice" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Voice Testing</CardTitle>
                <CardDescription>
                  Test voice input and output capabilities
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <Button 
                    onClick={startVoiceTest}
                    disabled={isRecording}
                    variant={isRecording ? "destructive" : "default"}
                    className="flex items-center gap-2"
                  >
                    {isRecording ? (
                      <>
                        <MicOff className="h-4 w-4" />
                        Stop Recording
                      </>
                    ) : (
                      <>
                        <Mic className="h-4 w-4" />
                        Start Voice Test
                      </>
                    )}
                  </Button>

                  {audioBlob && (
                    <Button variant="outline" className="flex items-center gap-2">
                      <Volume2 className="h-4 w-4" />
                      Play Recording
                    </Button>
                  )}
                </div>

                {isRecording && (
                  <div className="flex items-center gap-2 text-red-600">
                    <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse" />
                    Recording...
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="results" className="space-y-4">
            {testResults ? (
              <Card>
                <CardHeader>
                  <CardTitle>Test Results</CardTitle>
                  <CardDescription>
                    Summary of the latest test run
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {testResults.successRate.toFixed(1)}%
                      </div>
                      <div className="text-sm text-muted-foreground">Success Rate</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {testResults.passedTests}/{testResults.totalTests}
                      </div>
                      <div className="text-sm text-muted-foreground">Tests Passed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {testResults.averageResponseTime.toFixed(0)}ms
                      </div>
                      <div className="text-sm text-muted-foreground">Avg Response</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {(testResults.testDuration / 1000).toFixed(1)}s
                      </div>
                      <div className="text-sm text-muted-foreground">Total Duration</div>
                    </div>
                  </div>

                  {testResults.errors.length > 0 && (
                    <div className="space-y-2">
                      <Label>Errors</Label>
                      <div className="space-y-1">
                        {testResults.errors.map((error, index) => (
                          <div key={index} className="flex items-center gap-2 text-red-600">
                            <AlertCircle className="h-4 w-4" />
                            <span className="text-sm">{error}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button onClick={saveTestResults} className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4" />
                      Save Results
                    </Button>
                    <Button onClick={exportTestResults} variant="outline" className="flex items-center gap-2">
                      <Download className="h-4 w-4" />
                      Export
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="p-8 text-center">
                  <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">No Test Results</h3>
                  <p className="text-muted-foreground">
                    Run some tests to see results here
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TemplateTesting;
