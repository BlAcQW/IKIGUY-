import React, { useState } from 'react';
import { Upload, Globe, Wand2, Plus, Minus, CheckCircle, Loader2, AlertCircle, FileText, Trash2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { getAuthHeaders } from '@/lib/auth-utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

interface WebsiteUrl {
  id: string;
  url: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
}

interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  type: string;
  content?: string;
  uploadStatus: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
}

interface SystemPromptGeneratorProps {
  // Current values
  primaryUrl: string;
  onUrlChange?: (url: string) => void;
  onPromptGenerated?: (prompt: string, extractedInfo?: any) => void;
  initialPrompt?: string;

  // Generation options
  additionalContext?: {
    agentType?: string;
    language?: string;
    companyName?: string;
  };

  // API configuration
  apiBaseUrl: string;

  // UI configuration
  title?: string;
  description?: string;
  showDocumentUpload?: boolean;
  showMultipleUrls?: boolean;
  placeholder?: string;
}

type ExtractionStep = 'none' | 'extracted' | 'confirmed';

export const SystemPromptGenerator: React.FC<SystemPromptGeneratorProps> = ({
  primaryUrl,
  onUrlChange,
  onPromptGenerated,
  initialPrompt = '',
  additionalContext,
  apiBaseUrl,
  title = "Website Content Extraction",
  description = "Extract content from websites and documents to generate AI system prompts",
  showDocumentUpload = true,
  showMultipleUrls = true,
  placeholder = "You are a helpful AI assistant. Your role is to..."
}) => {
  const { toast } = useToast();
  const [isExtractingContent, setIsExtractingContent] = useState(false);
  const [isGeneratingPrompt, setIsGeneratingPrompt] = useState(false);
  const [contentExtractionStep, setContentExtractionStep] = useState<ExtractionStep>('none');

  // Internal state for URLs and documents
  const [additionalUrls, setAdditionalUrls] = useState<WebsiteUrl[]>([]);
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [extractedContent, setExtractedContent] = useState('');
  const [systemPrompt, setSystemPrompt] = useState(initialPrompt);

  const addWebsiteUrl = () => {
    const newUrl: WebsiteUrl = {
      id: crypto.randomUUID(),
      url: '',
      status: 'pending'
    };
    setAdditionalUrls([...additionalUrls, newUrl]);
  };

  const updateWebsiteUrl = (id: string, url: string) => {
    const updatedUrls = additionalUrls.map(item =>
      item.id === id ? { ...item, url, status: 'pending' as const } : item
    );
    setAdditionalUrls(updatedUrls);
  };

  const removeWebsiteUrl = (id: string) => {
    const filteredUrls = additionalUrls.filter(item => item.id !== id);
    setAdditionalUrls(filteredUrls);
  };

  const handleDocumentUpload = async (files: FileList) => {
    const supportedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];

    for (const file of Array.from(files)) {
      if (!supportedTypes.includes(file.type)) {
        toast({
          title: "Unsupported file type",
          description: `${file.name} is not supported. Supported: PDF, Word, TXT files`,
          variant: "destructive"
        });
        continue;
      }

      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        toast({
          title: "File too large",
          description: `${file.name} exceeds the 5MB limit. Please use a smaller file.`,
          variant: "destructive"
        });
        continue;
      }

      const fileId = crypto.randomUUID();
      const newDoc: UploadedDocument = {
        id: fileId,
        name: file.name,
        size: file.size,
        type: file.type,
        uploadStatus: 'uploading'
      };

      // Add document to the list
      setUploadedDocuments([...uploadedDocuments, newDoc]);

      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${apiBaseUrl}/ai/upload-document`, {
          method: 'POST',
          headers: {
            'Authorization': (await getAuthHeaders())['Authorization']
          },
          body: formData
        });

        if (!response.ok) {
          throw new Error('Upload failed');
        }

        const result = await response.json();

        // Update document status to completed
        const updatedDocuments = uploadedDocuments.map(doc =>
          doc.id === fileId
            ? { ...doc, uploadStatus: 'completed' as const, content: result.content }
            : doc
        );
        setUploadedDocuments(updatedDocuments);

        toast({
          title: "Document uploaded",
          description: `${file.name} uploaded and processed successfully.`
        });

      } catch (error) {
        // Update document status to failed
        const updatedDocuments = uploadedDocuments.map(doc =>
          doc.id === fileId
            ? { ...doc, uploadStatus: 'failed' as const }
            : doc
        );
        setUploadedDocuments(updatedDocuments);

        toast({
          title: "Upload failed",
          description: `Failed to upload ${file.name}. Please try again.`,
          variant: "destructive"
        });
      }
    }
  };

  const removeDocument = (fileId: string) => {
    const filteredDocs = uploadedDocuments.filter(doc => doc.id !== fileId);
    setUploadedDocuments(filteredDocs);
  };

  const extractContent = async () => {
    // Check if we have URLs or documents
    const hasUrls = additionalUrls.length > 0 || primaryUrl.trim() !== '';
    const hasDocuments = uploadedDocuments.length > 0;

    if (!hasUrls && !hasDocuments) {
      toast({
        title: "Missing information",
        description: "Please add at least one website URL or upload documents to extract content from",
        variant: "destructive"
      });
      return;
    }

    setIsExtractingContent(true);

    try {
      // Prepare URLs list
      const allUrls = [];
      if (primaryUrl.trim()) {
        allUrls.push(primaryUrl.trim());
      }
      additionalUrls.forEach(item => {
        if (item.url.trim()) {
          allUrls.push(item.url.trim());
        }
      });

      // Prepare documents content
      const documentsContent = uploadedDocuments
        .filter(doc => doc.uploadStatus === 'completed' && doc.content)
        .map(doc => ({
          name: doc.name,
          content: doc.content
        }));

      const response = await fetch(`${apiBaseUrl}/ai/extract-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': (await getAuthHeaders())['Authorization']
        },
        body: JSON.stringify({
          website_urls: allUrls,
          documents: documentsContent
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || 'Failed to extract content');
      }

      const result = await response.json();

      if (result.success) {
        setExtractedContent(result.extracted_content);
        setContentExtractionStep('extracted');

        toast({
          title: "Content extracted successfully",
          description: `Extracted content from ${result.sources_analyzed.websites} websites and ${result.sources_analyzed.documents} documents. Please review and confirm.`
        });
      } else {
        throw new Error(result.error || 'Content extraction failed');
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';

      toast({
        title: "Content extraction failed",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setIsExtractingContent(false);
    }
  };

  const generateSystemPrompt = async () => {
    if (contentExtractionStep !== 'confirmed') {
      toast({
        title: "Please extract and confirm content first",
        description: "Use the 'Extract Content' button to see what information will be used for prompt generation",
        variant: "destructive"
      });
      return;
    }

    if (additionalContext?.agentType && !additionalContext.agentType) {
      toast({
        title: "Missing information",
        description: "Please select an agent type first",
        variant: "destructive"
      });
      return;
    }

    setIsGeneratingPrompt(true);

    try {
      const response = await fetch(`${apiBaseUrl}/ai/generate-system-prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': (await getAuthHeaders())['Authorization']
        },
        body: JSON.stringify({
          extracted_content: extractedContent,
          agent_type: additionalContext?.agentType || 'general',
          language: additionalContext?.language || 'en',
          company_name: additionalContext?.companyName || undefined,
          additional_context: undefined
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to generate system prompt');
      }

      const data = await response.json();
      setSystemPrompt(data.system_prompt);

      // Call the callback with the generated prompt and any extracted info
      if (onPromptGenerated) {
        onPromptGenerated(data.system_prompt, data.extracted_info);
      }

      toast({
        title: "System prompt generated",
        description: "AI has generated a custom system prompt based on the extracted content."
      });
    } catch (error) {
      console.error('Error generating system prompt:', error);
      toast({
        title: "Failed to generate prompt",
        description: error instanceof Error ? error.message : "Please try again or create a manual prompt.",
        variant: "destructive"
      });
    } finally {
      setIsGeneratingPrompt(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-medium mb-2">{title}</h3>
        <p className="text-sm text-gray-600">{description}</p>
      </div>

      {/* Primary Website URL */}
      <div>
        <Label htmlFor="primary-url" className="text-sm font-medium">
          Primary Website URL
        </Label>
        <Input
          id="primary-url"
          value={primaryUrl}
          onChange={(e) => onUrlChange?.(e.target.value)}
          placeholder="https://your-company.com"
          className="mt-2"
        />
        <p className="text-xs text-gray-600 mt-1">
          Main company website to analyze
        </p>
      </div>

      {/* Additional Website URLs */}
      {showMultipleUrls && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <Label className="text-sm font-medium">
              Additional Websites (Optional)
            </Label>
            <Button variant="outline" size="sm" onClick={addWebsiteUrl}>
              <Plus className="h-4 w-4 mr-2" />
              Add URL
            </Button>
          </div>

          {additionalUrls.length > 0 && (
            <div className="space-y-2">
              {additionalUrls.map((urlItem, index) => (
                <div key={urlItem.id} className="flex gap-2">
                  <Input
                    value={urlItem.url}
                    onChange={(e) => updateWebsiteUrl(urlItem.id, e.target.value)}
                    placeholder={`https://additional-site-${index + 1}.com`}
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => removeWebsiteUrl(urlItem.id)}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
          <p className="text-xs text-gray-600 mt-1">
            Add more websites to gather comprehensive information about your business
          </p>
        </div>
      )}

      {/* Document Upload */}
      {showDocumentUpload && (
        <div>
          <Label className="text-sm font-medium mb-3 block">
            Upload Documents (Optional)
          </Label>
          <div className="border-2 border-dashed border-muted-foreground rounded-lg p-4 text-center">
            <Upload className="h-6 w-6 text-gray-600 mx-auto mb-2" />
            <p className="text-sm font-medium mb-1">Drop documents here or click to browse</p>
            <p className="text-xs text-gray-600 mb-3">
              PDF, Word, or Text files. Max 5MB per file.
            </p>
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt"
              onChange={(e) => e.target.files && handleDocumentUpload(e.target.files)}
              className="hidden"
              id="document-upload"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => document.getElementById('document-upload')?.click()}
            >
              <Upload className="h-4 w-4 mr-2" />
              Browse Files
            </Button>
          </div>

          {uploadedDocuments.length > 0 && (
            <div className="space-y-2 mt-3">
              <Label className="text-xs font-medium">Uploaded Documents</Label>
              {uploadedDocuments.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-2 bg-muted rounded-lg">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-gray-600" />
                    <div>
                      <p className="text-sm font-medium">{doc.name}</p>
                      <p className="text-xs text-gray-600">
                        {(doc.size / 1024).toFixed(1)}KB • {doc.uploadStatus}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.uploadStatus === 'uploading' && (
                      <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                    )}
                    {doc.uploadStatus === 'completed' && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {doc.uploadStatus === 'failed' && (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeDocument(doc.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Two-Step Process */}
      <div className="space-y-4">
        {/* Process Flow Indicator */}
        <div className="flex items-center justify-center space-x-4 py-4">
          <div className={`flex items-center space-x-2 ${
            contentExtractionStep !== 'none' ? 'text-green-600' : 'text-gray-400'
          }`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
              contentExtractionStep !== 'none'
                ? 'bg-green-100 border-green-500'
                : 'bg-gray-100 border-gray-300'
            }`}>
              {contentExtractionStep !== 'none' ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <span className="text-xs font-bold">1</span>
              )}
            </div>
            <span className="text-sm font-medium">Extract</span>
          </div>
          <div className={`w-8 h-0.5 ${
            contentExtractionStep === 'extracted' || contentExtractionStep === 'confirmed'
              ? 'bg-green-500'
              : 'bg-gray-300'
          }`}></div>
          <div className={`flex items-center space-x-2 ${
            contentExtractionStep === 'confirmed' ? 'text-green-600' : 'text-gray-400'
          }`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
              contentExtractionStep === 'confirmed'
                ? 'bg-green-100 border-green-500'
                : 'bg-gray-100 border-gray-300'
            }`}>
              {contentExtractionStep === 'confirmed' ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <span className="text-xs font-bold">2</span>
              )}
            </div>
            <span className="text-sm font-medium">Generate</span>
          </div>
        </div>

        {/* Step 1: Extract Content */}
        {contentExtractionStep === 'none' && (
          <div className="flex justify-center">
            <Button
              onClick={extractContent}
              disabled={isExtractingContent}
              size="lg"
              className="w-full"
              variant="outline"
            >
              {isExtractingContent ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Extracting Content...
                </>
              ) : (
                <>
                  <Globe className="h-4 w-4 mr-2" />
                  Step 1: Extract Content
                </>
              )}
            </Button>
          </div>
        )}

        {/* Step 2: Review and Confirm */}
        {contentExtractionStep === 'extracted' && (
          <div className="space-y-4">
            <div className="border-2 border-dashed border-primary/50 rounded-lg p-4 bg-primary/5">
              <div className="flex items-center justify-between mb-2">
                <Label className="text-sm font-medium text-indigo-600">✅ Content Successfully Extracted</Label>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setContentExtractionStep('none');
                      setExtractedContent('');
                    }}
                  >
                    Re-extract
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => setContentExtractionStep('confirmed')}
                    className="bg-indigo-600 hover:bg-primary/90"
                  >
                    ✓ Confirm & Continue
                  </Button>
                </div>
              </div>
              <Textarea
                value={extractedContent}
                onChange={(e) => setExtractedContent(e.target.value)}
                rows={8}
                className="text-sm"
                placeholder="Extracted content will appear here..."
              />
              <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-medium text-blue-800 mb-1">
                  📝 Review the extracted content above
                </p>
                <p className="text-xs text-blue-600">
                  You can edit the content if needed, then click "✓ Confirm & Continue" to proceed to system prompt generation.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Generate Prompt */}
        {contentExtractionStep === 'confirmed' && (
          <div className="border-2 border-dashed border-green-300 rounded-lg p-4 bg-green-50">
            <div className="flex items-center justify-center mb-3">
              <div className="flex items-center gap-2 text-green-700 font-medium">
                <CheckCircle className="h-5 w-5" />
                <span>Content Confirmed - Ready for AI Generation!</span>
              </div>
            </div>
            <div className="flex justify-center">
              <Button
                onClick={generateSystemPrompt}
                disabled={isGeneratingPrompt}
                size="lg"
                className="w-full bg-green-600 hover:bg-green-700 text-white"
              >
                {isGeneratingPrompt ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Generating AI System Prompt...
                  </>
                ) : (
                  <>
                    <Wand2 className="h-4 w-4 mr-2" />
                    🪄 Generate AI System Prompt
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Generated System Prompt */}
      {systemPrompt && (
        <div>
          <Label htmlFor="generated-prompt" className="text-sm font-medium">
            Generated System Prompt
          </Label>
          <Textarea
            id="generated-prompt"
            value={systemPrompt}
            onChange={(e) => {
              setSystemPrompt(e.target.value);
              onPromptGenerated?.(e.target.value);
            }}
            rows={8}
            className="mt-2"
            placeholder={placeholder}
          />
          <p className="text-xs text-gray-600 mt-1">
            Review and customize the generated prompt as needed
          </p>
        </div>
      )}
    </div>
  );
};