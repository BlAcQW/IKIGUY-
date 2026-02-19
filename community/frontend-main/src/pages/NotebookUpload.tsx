import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload, FileCode, AlertCircle, CheckCircle2, Loader2,
  X, Plus, ArrowLeft
} from 'lucide-react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { useBackendAuth } from '@/contexts/BackendAuthContext';

const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

const NotebookUpload: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useBackendAuth();

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [difficulty, setDifficulty] = useState('intermediate');
  const [languageCodes, setLanguageCodes] = useState<string[]>([]);
  const [languageInput, setLanguageInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  const [license, setLicense] = useState('MIT');
  const [file, setFile] = useState<File | null>(null);
  const [fileContent, setFileContent] = useState('');

  // UI state
  const [uploading, setUploading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [validationSuccess, setValidationSuccess] = useState(false);

  const categories = [
    { value: 'data_acquisition', label: 'Data Acquisition' },
    { value: 'data_processing', label: 'Data Processing' },
    { value: 'asr_training', label: 'ASR Training' },
    { value: 'tts_training', label: 'TTS Training' },
    { value: 'llm_training', label: 'LLM Training' },
    { value: 'evaluation', label: 'Evaluation' },
    { value: 'deployment', label: 'Deployment' },
    { value: 'research', label: 'Research' },
    { value: 'tutorial', label: 'Tutorial' },
    { value: 'other', label: 'Other' }
  ];

  const difficulties = [
    { value: 'beginner', label: 'Beginner' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'advanced', label: 'Advanced' },
    { value: 'expert', label: 'Expert' }
  ];

  const licenses = [
    { value: 'MIT', label: 'MIT License' },
    { value: 'Apache-2.0', label: 'Apache 2.0' },
    { value: 'GPL-3.0', label: 'GPL 3.0' },
    { value: 'BSD-3-Clause', label: 'BSD 3-Clause' },
    { value: 'CC-BY-4.0', label: 'Creative Commons BY 4.0' },
    { value: 'CC-BY-SA-4.0', label: 'Creative Commons BY-SA 4.0' }
  ];

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;

    // Validate file type
    if (!selectedFile.name.endsWith('.ipynb')) {
      setValidationError('Please upload a valid Jupyter notebook file (.ipynb)');
      setFile(null);
      return;
    }

    // Validate file size (max 10MB)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setValidationError('File size must be less than 10MB');
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setValidationError(null);
    setValidationSuccess(false);

    // Read and validate file content
    try {
      setValidating(true);
      const reader = new FileReader();

      reader.onload = async (e) => {
        try {
          const content = e.target?.result as string;

          // Validate JSON structure
          const notebookData = JSON.parse(content);

          if (!notebookData.cells || !Array.isArray(notebookData.cells)) {
            setValidationError('Invalid notebook structure: missing cells');
            setFile(null);
            return;
          }

          // Encode to base64
          const base64Content = btoa(unescape(encodeURIComponent(content)));
          setFileContent(base64Content);
          setValidationSuccess(true);

          // Auto-fill title if empty and notebook has a title
          if (!title && notebookData.metadata?.title) {
            setTitle(notebookData.metadata.title);
          }
        } catch (error) {
          setValidationError('Invalid JSON format');
          setFile(null);
        } finally {
          setValidating(false);
        }
      };

      reader.onerror = () => {
        setValidationError('Failed to read file');
        setFile(null);
        setValidating(false);
      };

      reader.readAsText(selectedFile);
    } catch (error) {
      setValidationError('Failed to process file');
      setFile(null);
      setValidating(false);
    }
  };

  const addLanguageCode = () => {
    const code = languageInput.trim().toLowerCase();
    if (code && !languageCodes.includes(code)) {
      setLanguageCodes([...languageCodes, code]);
      setLanguageInput('');
    }
  };

  const removeLanguageCode = (code: string) => {
    setLanguageCodes(languageCodes.filter(c => c !== code));
  };

  const addTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !tags.includes(tag) && tags.length < 20) {
      setTags([...tags, tag]);
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to upload notebooks',
        variant: 'destructive'
      });
      return;
    }

    if (!file || !fileContent) {
      setValidationError('Please select a notebook file');
      return;
    }

    if (!category) {
      setValidationError('Please select a category');
      return;
    }

    try {
      setUploading(true);

      const notebookData = {
        title,
        description,
        category,
        difficulty,
        language_codes: languageCodes,
        tags,
        is_public: isPublic,
        license,
        file_content: fileContent
      };

      const response = await fetch(`${API_BASE}/notebooks/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify(notebookData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to upload notebook');
      }

      const result = await response.json();

      toast({
        title: 'Success',
        description: 'Notebook uploaded successfully!'
      });

      // Navigate to the notebook detail page
      navigate(`/notebooks/${result.data.id}`);
    } catch (error: any) {
      console.error('Upload error:', error);
      toast({
        title: 'Upload Failed',
        description: error.message || 'Failed to upload notebook',
        variant: 'destructive'
      });
    } finally {
      setUploading(false);
    }
  };

  const isFormValid = () => {
    return (
      title.trim().length > 0 &&
      description.trim().length >= 10 &&
      category &&
      file &&
      fileContent &&
      validationSuccess
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate('/notebooks')}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Notebooks
          </Button>

          <h1 className="text-4xl font-bold mb-2">Upload Notebook</h1>
          <p className="text-lg text-muted-foreground">
            Share your Jupyter notebook with the community
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Upload */}
          <Card>
            <CardHeader>
              <CardTitle>Notebook File</CardTitle>
              <CardDescription>
                Upload a Jupyter notebook file (.ipynb, max 10MB)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="border-2 border-dashed rounded-lg p-8 text-center">
                  <input
                    type="file"
                    id="notebook-file"
                    accept=".ipynb"
                    onChange={handleFileSelect}
                    className="hidden"
                    disabled={uploading}
                  />
                  <label
                    htmlFor="notebook-file"
                    className="cursor-pointer flex flex-col items-center gap-4"
                  >
                    {validating ? (
                      <>
                        <Loader2 className="h-12 w-12 text-primary animate-spin" />
                        <p className="text-sm text-muted-foreground">Validating notebook...</p>
                      </>
                    ) : file ? (
                      <>
                        <FileCode className="h-12 w-12 text-primary" />
                        <div>
                          <p className="font-semibold">{file.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {(file.size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                        {validationSuccess && (
                          <Badge className="bg-green-100 text-green-800">
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                            Valid Notebook
                          </Badge>
                        )}
                      </>
                    ) : (
                      <>
                        <Upload className="h-12 w-12 text-muted-foreground" />
                        <div>
                          <p className="font-semibold">Choose a file or drag and drop</p>
                          <p className="text-sm text-muted-foreground">
                            Jupyter Notebook (.ipynb) up to 10MB
                          </p>
                        </div>
                      </>
                    )}
                  </label>
                </div>

                {validationError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{validationError}</AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
              <CardDescription>
                Provide details about your notebook
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Twi ASR Data Preprocessing Pipeline"
                  maxLength={200}
                  required
                  disabled={uploading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description *</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what your notebook does, what problems it solves, and any prerequisites..."
                  rows={4}
                  maxLength={2000}
                  required
                  disabled={uploading}
                />
                <p className="text-xs text-muted-foreground">
                  {description.length}/2000 characters (minimum 10)
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="category">Category *</Label>
                  <Select value={category} onValueChange={setCategory} disabled={uploading}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map(cat => (
                        <SelectItem key={cat.value} value={cat.value}>
                          {cat.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="difficulty">Difficulty Level</Label>
                  <Select value={difficulty} onValueChange={setDifficulty} disabled={uploading}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {difficulties.map(diff => (
                        <SelectItem key={diff.value} value={diff.value}>
                          {diff.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="license">License</Label>
                <Select value={license} onValueChange={setLicense} disabled={uploading}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {licenses.map(lic => (
                      <SelectItem key={lic.value} value={lic.value}>
                        {lic.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Languages and Tags */}
          <Card>
            <CardHeader>
              <CardTitle>Languages & Tags</CardTitle>
              <CardDescription>
                Specify which languages this notebook supports and add relevant tags
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="language-codes">Language Codes (e.g., tw, yo, ha)</Label>
                <div className="flex gap-2">
                  <Input
                    id="language-codes"
                    value={languageInput}
                    onChange={(e) => setLanguageInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addLanguageCode())}
                    placeholder="Enter language code"
                    disabled={uploading}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={addLanguageCode}
                    disabled={uploading}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                {languageCodes.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {languageCodes.map(code => (
                      <Badge key={code} variant="secondary">
                        {code}
                        <X
                          className="ml-1 h-3 w-3 cursor-pointer"
                          onClick={() => removeLanguageCode(code)}
                        />
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="tags">Tags (max 20)</Label>
                <div className="flex gap-2">
                  <Input
                    id="tags"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    placeholder="e.g., preprocessing, pytorch, transformers"
                    disabled={uploading || tags.length >= 20}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={addTag}
                    disabled={uploading || tags.length >= 20}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                {tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {tags.map(tag => (
                      <Badge key={tag} variant="outline">
                        {tag}
                        <X
                          className="ml-1 h-3 w-3 cursor-pointer"
                          onClick={() => removeTag(tag)}
                        />
                      </Badge>
                    ))}
                  </div>
                )}
                <p className="text-xs text-muted-foreground">
                  {tags.length}/20 tags
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Visibility Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Visibility</CardTitle>
              <CardDescription>
                Control who can see your notebook
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="is-public">Public Notebook</Label>
                  <p className="text-sm text-muted-foreground">
                    Allow anyone to view and download this notebook
                  </p>
                </div>
                <Switch
                  id="is-public"
                  checked={isPublic}
                  onCheckedChange={setIsPublic}
                  disabled={uploading}
                />
              </div>
            </CardContent>
          </Card>

          {/* Submit Buttons */}
          <div className="flex items-center justify-end gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/notebooks')}
              disabled={uploading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!isFormValid() || uploading}
            >
              {uploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Notebook
                </>
              )}
            </Button>
          </div>
        </form>
      </main>

      <Footer />
    </div>
  );
};

export default NotebookUpload;
