import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Upload, FileText, Mic, Database, Gift, Smartphone, Loader2, CheckCircle, X, File, Edit, Trash2, Clock } from "lucide-react";
import MediaCapture from "@/components/MediaCapture";
import FileUpload from "@/components/FileUpload";
import { getDeviceCapabilities } from "@/utils/pwa";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/lib/api";
import { AuthModal } from "@/components/AuthModal";
import { SubmissionEditModal } from "@/components/SubmissionEditModal";

const Submit = () => {
  const { user, profile, loading: authLoading } = useAuth();
  const deviceCapabilities = getDeviceCapabilities();
  const [searchParams] = useSearchParams();

  // State management
  const [languages, setLanguages] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [savingDraft, setSavingDraft] = useState(false);
  const [recentSubmissions, setRecentSubmissions] = useState<any[]>([]);
  const [loadingRecent, setLoadingRecent] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState<any>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<any>({
    language_code: '',
    type: 'text',
    title: '',
    description: '',
    category: '',
    dialect: '',
    cultural_context: '',
    usage_context: '',
    text_content: '',
    external_url: ''
  });

  const contributionTypes = [
    {
      type: "Text Dataset",
      icon: <FileText className="h-6 w-6" />,
      description: "Written text in African languages for training language models",
      examples: ["News articles", "Literature", "Social media posts", "Government documents"],
      points: "10-50 points"
    },
    {
      type: "Audio Dataset",
      icon: <Mic className="h-6 w-6" />,
      description: "Audio recordings with transcriptions for speech recognition",
      examples: ["Voice recordings", "Radio broadcasts", "Interviews", "Pronunciation guides"],
      points: "20-100 points"
    },
    {
      type: "Translation Pairs",
      icon: <Database className="h-6 w-6" />,
      description: "Parallel text in multiple languages for translation models",
      examples: ["Document translations", "Subtitle translations", "Product descriptions"],
      points: "15-75 points"
    },
    {
      type: "Cultural Knowledge",
      icon: <Gift className="h-6 w-6" />,
      description: "Cultural context and linguistic knowledge for better AI understanding",
      examples: ["Idioms", "Cultural references", "Regional dialects", "Traditional stories"],
      points: "25-125 points"
    }
  ];

  // Load initial data
  useEffect(() => {
    loadData();

    // Check for language parameter from URL
    const languageParam = searchParams.get('language');
    if (languageParam) {
      setFormData(prev => ({ ...prev, language_code: languageParam }));
    }
  }, [searchParams]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [languagesData, statsData] = await Promise.all([
        apiClient.getLanguages(),
        apiClient.getSubmissionStats()
      ]);

      setLanguages(languagesData);

      // Load recent submissions if user is logged in
      if (user) {
        loadRecentSubmissions();
      }
      setStats(statsData);
    } catch (error) {
      console.error("Failed to load data:", error);
      // Fallback to mock data
      setLanguages([
        { code: 'yo', name: 'Yoruba', native_name: 'Yorùbá' },
        { code: 'ig', name: 'Igbo', native_name: 'Igbo' },
        { code: 'sw', name: 'Swahili', native_name: 'Kiswahili' },
        { code: 'am', name: 'Amharic', native_name: 'አማርኛ' },
        { code: 'zu', name: 'Zulu', native_name: 'isiZulu' }
      ]);
      setStats({ total_submissions: 0, by_type: { text: 0, audio: 0, link: 0 } });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const loadRecentSubmissions = async () => {
    try {
      setLoadingRecent(true);
      const submissions = await apiClient.getUserSubmissions(1, 5);
      setRecentSubmissions(Array.isArray(submissions) ? submissions : submissions?.items || []);
    } catch (error) {
      console.error("Failed to load recent submissions:", error);
      setRecentSubmissions([]);
    } finally {
      setLoadingRecent(false);
    }
  };

  const handleEditSubmission = (submission: any) => {
    setSelectedSubmission(submission);
    setEditModalOpen(true);
  };

  const handleDeleteSubmission = async (submissionId: string) => {
    if (!window.confirm('Are you sure you want to delete this submission?')) {
      return;
    }

    try {
      setDeletingId(submissionId);
      await apiClient.deleteSubmission(submissionId);
      await loadRecentSubmissions();
      alert('Submission deleted successfully');
    } catch (error) {
      console.error('Failed to delete submission:', error);
      alert('Failed to delete submission. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleSubmit = async (submissionType: 'text' | 'link' | 'audio') => {
    if (!user) {
      setIsAuthModalOpen(true);
      return;
    }

    try {
      setSubmitting(true);
      setSubmitSuccess(false);

      // Validate required fields
      if (!formData.language_code || !formData.title) {
        alert('Please fill in all required fields (Language and Title)');
        setSubmitting(false);
        return;
      }

      // Submit based on type
      if (submissionType === 'text') {
        await apiClient.submitText({
          language_code: formData.language_code,
          type: 'text',
          title: formData.title,
          description: formData.description,
          category: formData.category,
          dialect: formData.dialect,
          cultural_context: formData.cultural_context,
          usage_context: formData.usage_context,
          text_content: formData.text_content
        });
      } else if (submissionType === 'link') {
        await apiClient.submitLink({
          language_code: formData.language_code,
          type: 'link',
          title: formData.title,
          description: formData.description,
          external_url: formData.external_url
        });
      } else if (submissionType === 'audio') {
        // For audio, create FormData
        if (!selectedFile) {
          alert('Please select an audio file to upload');
          setSubmitting(false);
          return;
        }

        const formDataObj = new FormData();
        formDataObj.append('file', selectedFile);
        formDataObj.append('language_code', formData.language_code);
        formDataObj.append('title', formData.title);
        if (formData.description) formDataObj.append('description', formData.description);
        if (formData.category) formDataObj.append('category', formData.category);
        if (formData.dialect) formDataObj.append('dialect', formData.dialect);
        if (formData.cultural_context) formDataObj.append('cultural_context', formData.cultural_context);
        if (formData.usage_context) formDataObj.append('usage_context', formData.usage_context);

        setUploadProgress(50);
        await apiClient.submitAudio(formDataObj);
        setUploadProgress(100);
      }

      setSubmitSuccess(true);
      alert('Submission successful! Thank you for your contribution.');

      // Reset form
      setFormData({
        language_code: '',
        type: 'text',
        title: '',
        description: '',
        category: '',
        dialect: '',
        cultural_context: '',
        usage_context: '',
        text_content: '',
        external_url: ''
      });
      setSelectedFile(null);
      setUploadProgress(0);

      // Refresh stats
      const updatedStats = await apiClient.getSubmissionStats();
      setStats(updatedStats);

    } catch (error) {
      console.error("Submission failed:", error);
      alert(`Failed to submit: ${error.message || 'Please try again.'}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleContributionTypeClick = (type: string) => {
    const typeMap: Record<string, 'text' | 'audio' | 'link'> = {
      'Text Dataset': 'text',
      'Audio Dataset': 'audio',
      'Translation Pairs': 'text',
      'Cultural Knowledge': 'text'
    };

    const mappedType = typeMap[type] || 'text';
    setFormData(prev => ({ ...prev, type: mappedType }));
  };


  const handleRemoveFile = () => {
    setSelectedFile(null);
    setUploadProgress(0);
    // Clear form data related to file content
    setFormData(prev => ({
      ...prev,
      text_content: '',
      type: 'text'
    }));
  };

  const handleSaveAsDraft = async () => {
    if (!user) {
      setIsAuthModalOpen(true);
      return;
    }

    try {
      setSavingDraft(true);

      // Save to localStorage for now
      const existingDrafts = JSON.parse(localStorage.getItem('submission_drafts') || '[]');
      const draftId = Date.now().toString();
      const newDraft = {
        ...formData,
        id: draftId,
        file: selectedFile?.name || null,
        saved_at: new Date().toISOString()
      };

      existingDrafts.push(newDraft);
      localStorage.setItem('submission_drafts', JSON.stringify(existingDrafts));
      alert('Draft saved locally! You can continue editing later.');

    } catch (error) {
      console.error('Failed to save draft:', error);
      alert('Failed to save draft. Please try again.');
    } finally {
      setSavingDraft(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Contribute to AfriLang</h1>
          <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
            Help build the largest collection of African language datasets for AI development.
            Your contributions help preserve and digitize African languages for future generations.
          </p>

          {/* Statistics */}
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 max-w-2xl mx-auto">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{stats?.total_submissions || 0}</div>
                <div className="text-sm text-muted-foreground">Total Submissions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{stats?.by_type?.text || 0}</div>
                <div className="text-sm text-muted-foreground">Text Datasets</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{stats?.by_type?.audio || 0}</div>
                <div className="text-sm text-muted-foreground">Audio Recordings</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{stats?.by_status?.validated || 0}</div>
                <div className="text-sm text-muted-foreground">Validated</div>
              </div>
            </div>
          )}
        </div>

        {/* Contribution Types */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {contributionTypes.map((item, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    {item.icon}
                  </div>
                  <div>
                    <CardTitle className="text-lg">{item.type}</CardTitle>
                    <Badge variant="secondary" className="text-xs mt-1">
                      {item.points}
                    </Badge>
                  </div>
                </div>
                <CardDescription>{item.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <h4 className="font-medium text-sm">Examples:</h4>
                  <div className="flex flex-wrap gap-2">
                    {item.examples.map((example, exIndex) => (
                      <Badge key={exIndex} variant="outline" className="text-xs">
                        {example}
                      </Badge>
                    ))}
                  </div>
                  <Button
                    className="w-full mt-4"
                    onClick={() => handleContributionTypeClick(item.type)}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Submit {item.type}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Success Message */}
        {submitSuccess && (
          <div className="max-w-2xl mx-auto mb-8">
            <Card className="border-green-200 bg-green-50">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-green-700">
                  <CheckCircle className="h-5 w-5" />
                  <span className="font-medium">Submission successful!</span>
                </div>
                <p className="text-sm text-green-600 mt-1">
                  Your contribution has been submitted for review and will be validated by the community.
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Quick Submit Form */}
        <Card id="submission-form" className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>Quick Submit</CardTitle>
            <CardDescription>
              Submit your contribution quickly using the form below
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <Select
                  value={formData.language_code}
                  onValueChange={(value) => handleInputChange('language_code', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    {loading ? (
                      <SelectItem value="loading" disabled>Loading languages...</SelectItem>
                    ) : (
                      (languages || []).map((lang) => (
                        <SelectItem key={lang.code} value={lang.code}>
                          {lang.name} ({lang.code})
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="type">Contribution Type</Label>
                <Select
                  value={formData.type}
                  onValueChange={(value) => handleInputChange('type', value as 'text' | 'audio' | 'link')}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="text">Text Dataset</SelectItem>
                    <SelectItem value="audio">Audio Dataset</SelectItem>
                    <SelectItem value="link">Link/Resource</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                placeholder="Brief title for your contribution"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe your contribution, its source, and any relevant context..."
                className="min-h-[100px]"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
              />
            </div>

            {/* Conditional fields based on submission type */}
            {formData.type === 'text' && (
              <div className="space-y-2">
                <Label htmlFor="text_content">Text Content</Label>
                <Textarea
                  id="text_content"
                  placeholder="Enter the text content here..."
                  className="min-h-[120px]"
                  value={formData.text_content}
                  onChange={(e) => handleInputChange('text_content', e.target.value)}
                />
              </div>
            )}

            {formData.type === 'link' && (
              <div className="space-y-2">
                <Label htmlFor="external_url">Resource URL</Label>
                <Input
                  id="external_url"
                  placeholder="https://example.com/resource"
                  type="url"
                  value={formData.external_url}
                  onChange={(e) => handleInputChange('external_url', e.target.value)}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="file">Upload File (Optional)</Label>
              <FileUpload
                onFileSelect={(file) => {
                  setSelectedFile(file);
                  // Auto-detect content type based on file
                  const fileExtension = file.name.split('.').pop()?.toLowerCase();
                  if (file.type.startsWith('audio/') || ['mp3', 'wav', 'm4a', 'ogg', 'webm'].includes(fileExtension || '')) {
                    setFormData(prev => ({ ...prev, type: 'audio' }));
                  } else if (file.type === 'text/plain' || ['txt', 'csv'].includes(fileExtension || '')) {
                    setFormData(prev => ({ ...prev, type: 'text' }));

                    // For text files, read content and populate text_content
                    const reader = new FileReader();
                    reader.onload = (e) => {
                      const content = e.target?.result as string;
                      setFormData(prev => ({ ...prev, text_content: content }));
                    };
                    reader.readAsText(file);
                  }
                }}
                selectedFile={selectedFile}
                onFileRemove={handleRemoveFile}
                uploadProgress={uploadProgress}
                acceptedTypes={['.txt', '.pdf', '.mp3', '.wav', '.m4a', '.ogg', '.webm', '.csv', '.json']}
                maxSizeBytes={100 * 1024 * 1024}
                disabled={submitting}
              />
            </div>

            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1"
                disabled={submitting || savingDraft}
                onClick={handleSaveAsDraft}
              >
                {savingDraft ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving Draft...
                  </>
                ) : (
                  'Save as Draft'
                )}
              </Button>
              <Button
                className="flex-1"
                onClick={() => handleSubmit(formData.type as 'text' | 'link' | 'audio')}
                disabled={submitting || !formData.title || !formData.language_code || (formData.type === 'audio' && !selectedFile)}
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Submit for Review'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Recent Submissions */}
        {user && recentSubmissions.length > 0 && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle>Your Recent Submissions</CardTitle>
              <CardDescription>
                Manage your pending and recently submitted contributions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingRecent ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                </div>
              ) : (
                <div className="space-y-3">
                  {recentSubmissions.map((submission) => (
                    <div
                      key={submission.id || submission._id}
                      className="flex items-start justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium">{submission.title}</h4>
                          <Badge variant="outline" className="text-xs">
                            {submission.language_code}
                          </Badge>
                          <Badge
                            className={
                              submission.validation_status === 'approved' || submission.status === 'approved'
                                ? 'bg-green-100 text-green-800'
                                : submission.validation_status === 'rejected' || submission.status === 'rejected'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }
                          >
                            {submission.validation_status || submission.status || 'pending'}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">
                          Type: {submission.type} • Submitted: {new Date(submission.created_at).toLocaleDateString()}
                        </p>
                      </div>

                      {(submission.validation_status === 'pending' || submission.status === 'pending' ||
                        submission.validation_status === 'submitted' || submission.status === 'submitted') && (
                        <div className="flex gap-2 ml-4">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEditSubmission(submission)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeleteSubmission(submission.id || submission._id)}
                            disabled={deletingId === (submission.id || submission._id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            {deletingId === (submission.id || submission._id) ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Mobile Recording Interface */}
        {deviceCapabilities.isMobile && (deviceCapabilities.hasCamera || deviceCapabilities.hasMicrophone) && (
          <div className="mt-12 max-w-2xl mx-auto">
            <div className="flex items-center gap-2 mb-6">
              <Smartphone className="h-6 w-6" />
              <h2 className="text-2xl font-bold">Quick Mobile Recording</h2>
            </div>

            <div className="space-y-6">
              {deviceCapabilities.hasMicrophone && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Record Audio</h3>
                  <MediaCapture
                    type="audio"
                    language={formData.language_code || "Yoruba"}
                    maxDuration={180}
                    onCapture={async (blob, metadata) => {
                      console.log('Audio captured:', { blob, metadata });

                      // Convert blob to file
                      const audioFile = new File([blob], `recording_${Date.now()}.webm`, {
                        type: blob.type || 'audio/webm'
                      });

                      // Set the captured audio as selected file
                      setSelectedFile(audioFile);
                      setFormData(prev => ({
                        ...prev,
                        type: 'audio',
                        title: prev.title || `Audio Recording - ${new Date().toLocaleDateString()}`
                      }));

                      // Auto-scroll to submission form
                      document.getElementById('submission-form')?.scrollIntoView({
                        behavior: 'smooth'
                      });
                    }}
                  />
                </div>
              )}

              {deviceCapabilities.hasCamera && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Record Video</h3>
                  <MediaCapture
                    type="video"
                    language="Yoruba"
                    maxDuration={300}
                    onCapture={(blob, metadata) => {
                      console.log('Video captured:', { blob, metadata });
                      // Handle video submission
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Guidelines */}
        <div className="mt-12 max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-6">Contribution Guidelines</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quality Standards</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>• Content must be in an African language</p>
                <p>• Text should be properly formatted and clean</p>
                <p>• Audio must have clear speech quality</p>
                <p>• Include source attribution when possible</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Earning Points</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>• Points based on contribution size and quality</p>
                <p>• Bonus points for rare languages</p>
                <p>• Additional points for verified accuracy</p>
                <p>• Redeem points for recognition and rewards</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
      <Footer />

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        defaultTab="signup"
      />

      {selectedSubmission && (
        <SubmissionEditModal
          open={editModalOpen}
          onOpenChange={setEditModalOpen}
          submission={selectedSubmission}
          onSuccess={loadRecentSubmissions}
        />
      )}
    </div>
  );
};

export default Submit;