import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { generateCallSummary, generateQuickSummary } from '@/lib/gemini';
import { testVapiConnection, getVapiAssistants } from '@/lib/vapi';
import { CheckCircle, XCircle, Loader2, Zap, MessageSquare, Phone } from 'lucide-react';

const IntegrationTest: React.FC = () => {
  const { toast } = useToast();
  const [testing, setTesting] = useState(false);
  const [results, setResults] = useState<{
    gemini: boolean | null;
    vapi: boolean | null;
    vapiAssistants: any[] | null;
  }>({
    gemini: null,
    vapi: null,
    vapiAssistants: null
  });

  const testGeminiIntegration = async () => {
    try {
      const testTranscript = "Hello, this is a test call. The customer asked about our pricing and we discussed the basic plan which costs $29 per month. They seemed interested and asked about the features included.";
      
      const summary = await generateQuickSummary(testTranscript);
      
      if (summary && summary.length > 0) {
        toast({
          title: "Gemini Test Successful",
          description: `Generated summary: ${summary.substring(0, 100)}...`,
        });
        return true;
      } else {
        throw new Error('Empty summary returned');
      }
    } catch (error) {
      console.error('Gemini test failed:', error);
      toast({
        title: "Gemini Test Failed",
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: "destructive"
      });
      return false;
    }
  };

  const testVapiIntegration = async () => {
    try {
      const isConnected = await testVapiConnection();
      
      if (isConnected) {
        toast({
          title: "Vapi Test Successful",
          description: "Successfully connected to Vapi API",
        });
        return true;
      } else {
        throw new Error('Connection test failed');
      }
    } catch (error) {
      console.error('Vapi test failed:', error);
      toast({
        title: "Vapi Test Failed",
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: "destructive"
      });
      return false;
    }
  };

  const testVapiAssistants = async () => {
    try {
      const assistants = await getVapiAssistants();
      
      toast({
        title: "Vapi Assistants Test Successful",
        description: `Found ${assistants.length} assistants`,
      });
      return assistants;
    } catch (error) {
      console.error('Vapi assistants test failed:', error);
      toast({
        title: "Vapi Assistants Test Failed",
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: "destructive"
      });
      return null;
    }
  };

  const runAllTests = async () => {
    setTesting(true);
    setResults({
      gemini: null,
      vapi: null,
      vapiAssistants: null
    });

    try {
      // Test Gemini
      const geminiResult = await testGeminiIntegration();
      
      // Test Vapi connection
      const vapiResult = await testVapiIntegration();
      
      // Test Vapi assistants
      const vapiAssistants = await testVapiAssistants();

      setResults({
        gemini: geminiResult,
        vapi: vapiResult,
        vapiAssistants: vapiAssistants
      });

      toast({
        title: "Integration Tests Complete",
        description: "All tests have been completed. Check the results below.",
      });
    } catch (error) {
      console.error('Integration tests failed:', error);
      toast({
        title: "Integration Tests Failed",
        description: "Some tests failed. Check the console for details.",
        variant: "destructive"
      });
    } finally {
      setTesting(false);
    }
  };

  const getStatusIcon = (status: boolean | null) => {
    if (status === null) return <Loader2 className="h-4 w-4 animate-spin" />;
    return status ? <CheckCircle className="h-4 w-4 text-green-600" /> : <XCircle className="h-4 w-4 text-red-600" />;
  };

  const getStatusBadge = (status: boolean | null) => {
    if (status === null) return <Badge variant="secondary">Testing...</Badge>;
    return status ? <Badge variant="default" className="bg-green-100 text-green-800">Success</Badge> : <Badge variant="destructive">Failed</Badge>;
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5" />
          Integration Tests
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Run all integration tests</span>
          <Button 
            onClick={runAllTests} 
            disabled={testing}
            className="flex items-center gap-2"
          >
            {testing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4" />
                Run Tests
              </>
            )}
          </Button>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center gap-3">
              {getStatusIcon(results.gemini)}
              <div>
                <div className="font-medium flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Gemini AI Integration
                </div>
                <div className="text-sm text-muted-foreground">
                  Test conversation summary generation
                </div>
              </div>
            </div>
            {getStatusBadge(results.gemini)}
          </div>

          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center gap-3">
              {getStatusIcon(results.vapi)}
              <div>
                <div className="font-medium flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Vapi API Connection
                </div>
                <div className="text-sm text-muted-foreground">
                  Test API connectivity and authentication
                </div>
              </div>
            </div>
            {getStatusBadge(results.vapi)}
          </div>

          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center gap-3">
              {getStatusIcon(results.vapiAssistants !== null)}
              <div>
                <div className="font-medium flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Vapi Assistants
                </div>
                <div className="text-sm text-muted-foreground">
                  {results.vapiAssistants !== null 
                    ? `Found ${results.vapiAssistants.length} assistants`
                    : 'Test assistant retrieval'
                  }
                </div>
              </div>
            </div>
            {getStatusBadge(results.vapiAssistants !== null)}
          </div>
        </div>

        {results.vapiAssistants && results.vapiAssistants.length > 0 && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-2">Available Vapi Assistants:</h4>
            <div className="space-y-1">
              {results.vapiAssistants.slice(0, 5).map((assistant: any) => (
                <div key={assistant.id} className="text-sm">
                  <span className="font-medium">{assistant.name}</span>
                  <span className="text-muted-foreground ml-2">({assistant.status})</span>
                </div>
              ))}
              {results.vapiAssistants.length > 5 && (
                <div className="text-sm text-muted-foreground">
                  ... and {results.vapiAssistants.length - 5} more
                </div>
              )}
            </div>
          </div>
        )}

        <div className="text-xs text-muted-foreground mt-4">
          <p>These tests verify that your API keys are properly configured and the integrations are working correctly.</p>
          <p>If any test fails, check your environment variables and API key permissions.</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default IntegrationTest;
