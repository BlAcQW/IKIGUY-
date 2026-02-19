import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Play, Settings, Eye, Code, MessageSquare, Users, Star, Download } from 'lucide-react';
import { VoiceTemplate } from './VoiceAgentTemplates';

interface TemplatePreviewProps {
  template: VoiceTemplate;
  onUseTemplate?: (template: VoiceTemplate) => void;
}

interface PreviewData {
  businessName: string;
  industry: string;
  customPrompt: string;
  sampleQuestions: string[];
}

export default function TemplatePreview({ template, onUseTemplate }: TemplatePreviewProps) {
  const [previewData, setPreviewData] = useState<PreviewData>({
    businessName: 'Your Business',
    industry: 'Technology',
    customPrompt: template.systemPrompt,
    sampleQuestions: template.sampleQuestions,
  });

  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  const handlePreviewDataChange = (field: keyof PreviewData, value: string | string[]) => {
    setPreviewData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const generatePreviewPrompt = () => {
    return previewData.customPrompt
      .replace('{business_name}', previewData.businessName)
      .replace('{industry}', previewData.industry);
  };

  const handleTestTemplate = async () => {
    setIsTesting(true);
    // Simulate template testing
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsTesting(false);
  };

  const handleUseTemplate = () => {
    onUseTemplate?.(template);
    setIsPreviewOpen(false);
  };

  return (
    <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="flex items-center gap-2">
          <Eye className="h-4 w-4" />
          Preview & Test
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Preview & Test: {template.name}
          </DialogTitle>
          <DialogDescription>
            Test this template with your business information and see how it performs
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Template Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {template.name}
                <Badge variant="secondary">{template.category}</Badge>
              </CardTitle>
              <CardDescription>{template.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Difficulty:</span> {template.difficulty}
                </div>
                <div>
                  <span className="font-medium">Estimated Time:</span> {template.estimatedTime}
                </div>
                <div>
                  <span className="font-medium">Popularity:</span> 
                  <div className="flex items-center gap-1 mt-1">
                    {Array.from({ length: 5 }, (_, i) => (
                      <Star
                        key={i}
                        className={`h-4 w-4 ${i < Math.floor(template.popularity / 20) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
                      />
                    ))}
                    <span className="ml-1 text-xs text-muted-foreground">({template.popularity}%)</span>
                  </div>
                </div>
                <div>
                  <span className="font-medium">Use Cases:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {template.useCases.slice(0, 3).map((useCase, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {useCase}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Preview Configuration */}
          <Tabs defaultValue="preview" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="preview" className="flex items-center gap-2">
                <Eye className="h-4 w-4" />
                Preview
              </TabsTrigger>
              <TabsTrigger value="test" className="flex items-center gap-2">
                <Play className="h-4 w-4" />
                Test
              </TabsTrigger>
              <TabsTrigger value="code" className="flex items-center gap-2">
                <Code className="h-4 w-4" />
                Code
              </TabsTrigger>
            </TabsList>

            <TabsContent value="preview" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Customize Preview</CardTitle>
                  <CardDescription>
                    Configure the template with your business information
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="businessName">Business Name</Label>
                      <Input
                        id="businessName"
                        value={previewData.businessName}
                        onChange={(e) => handlePreviewDataChange('businessName', e.target.value)}
                        placeholder="Enter your business name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="industry">Industry</Label>
                      <Select
                        value={previewData.industry}
                        onValueChange={(value) => handlePreviewDataChange('industry', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select industry" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Technology">Technology</SelectItem>
                          <SelectItem value="Healthcare">Healthcare</SelectItem>
                          <SelectItem value="Finance">Finance</SelectItem>
                          <SelectItem value="Education">Education</SelectItem>
                          <SelectItem value="Retail">Retail</SelectItem>
                          <SelectItem value="Real Estate">Real Estate</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="customPrompt">System Prompt</Label>
                    <Textarea
                      id="customPrompt"
                      value={previewData.customPrompt}
                      onChange={(e) => handlePreviewDataChange('customPrompt', e.target.value)}
                      rows={4}
                      placeholder="Customize the system prompt..."
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Sample Questions</Label>
                    <div className="space-y-2">
                      {previewData.sampleQuestions.map((question, index) => (
                        <div key={index} className="flex items-center gap-2">
                          <MessageSquare className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">{question}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Preview Output */}
              <Card>
                <CardHeader>
                  <CardTitle>Generated Prompt</CardTitle>
                  <CardDescription>
                    This is how your assistant will be configured
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted p-4 rounded-lg">
                    <pre className="text-sm whitespace-pre-wrap">{generatePreviewPrompt()}</pre>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="test" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Test Template Performance</CardTitle>
                  <CardDescription>
                    Test how this template performs with sample interactions
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-4">
                    <Button
                      onClick={handleTestTemplate}
                      disabled={isTesting}
                      className="flex items-center gap-2"
                    >
                      <Play className="h-4 w-4" />
                      {isTesting ? 'Testing...' : 'Run Test'}
                    </Button>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Users className="h-4 w-4" />
                      <span>Test with sample user interactions</span>
                    </div>
                  </div>

                  {isTesting && (
                    <div className="bg-muted p-4 rounded-lg">
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                        <span>Running template performance test...</span>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <div className="text-2xl font-bold text-primary">95%</div>
                      <div className="text-muted-foreground">Success Rate</div>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <div className="text-2xl font-bold text-primary">2.3s</div>
                      <div className="text-muted-foreground">Avg Response</div>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <div className="text-2xl font-bold text-primary">4.8/5</div>
                      <div className="text-muted-foreground">User Rating</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="code" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Integration Code</CardTitle>
                  <CardDescription>
                    Code snippets for integrating this template
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label className="text-sm font-medium">JavaScript/TypeScript</Label>
                      <div className="bg-muted p-4 rounded-lg mt-2">
                        <pre className="text-sm overflow-x-auto">
{`const template = {
  id: '${template.id}',
  name: '${template.name}',
  systemPrompt: \`${generatePreviewPrompt()}\`,
  sampleQuestions: ${JSON.stringify(previewData.sampleQuestions, null, 2)}
};`}
                        </pre>
                      </div>
                    </div>

                    <div>
                      <Label className="text-sm font-medium">API Call</Label>
                      <div className="bg-muted p-4 rounded-lg mt-2">
                        <pre className="text-sm overflow-x-auto">
{`POST /api/assistants
{
  "templateId": "${template.id}",
  "businessName": "${previewData.businessName}",
  "industry": "${previewData.industry}",
  "customPrompt": "${generatePreviewPrompt()}"
}`}
                        </pre>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Action Buttons */}
          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setIsPreviewOpen(false)}>
              Cancel
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" className="flex items-center gap-2">
                <Download className="h-4 w-4" />
                Export Template
              </Button>
              <Button onClick={handleUseTemplate} className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Use This Template
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
