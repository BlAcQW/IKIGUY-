import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient, Notebook } from "@/lib/api";
import { ExternalLink, FileText, Play, GitBranch } from "lucide-react";

interface LanguageNotebooksProps {
  languageCode: string;
  languageName: string;
}

const LanguageNotebooks = ({ languageCode, languageName }: LanguageNotebooksProps) => {
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotebooks();
  }, [languageCode]);

  const loadNotebooks = async () => {
    try {
      const data = await apiClient.getNotebooks(languageCode);
      setNotebooks(data);
    } catch (error) {
      console.error('Failed to load notebooks:', error);
    } finally {
      setLoading(false);
    }
  };

  const modelCategories = {
    'wav2vec2': { name: 'Wav2Vec2', type: 'ASR', description: 'Self-supervised speech recognition' },
    'meta-mms': { name: 'Meta MMS', type: 'ASR/TTS', description: 'Massively Multilingual Speech' },
    'meta-voice': { name: 'Meta Voice', type: 'TTS', description: 'Meta voice synthesis' },
    'faster-whisper': { name: 'Faster Whisper', type: 'ASR', description: 'Optimized Whisper implementation' },
    'coqui-xtts-v2': { name: 'Coqui XTTS v2', type: 'TTS', description: 'Cross-lingual text-to-speech' },
  };

  const groupedNotebooks = notebooks.reduce((acc, notebook) => {
    const model = notebook.model_type || 'general';
    if (!acc[model]) {
      acc[model] = [];
    }
    acc[model].push(notebook);
    return acc;
  }, {} as Record<string, Notebook[]>);

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-32 bg-muted animate-pulse rounded" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">Notebooks for {languageName}</h2>
        <p className="text-muted-foreground">
          Explore AI model training and inference notebooks for the {languageName} language
        </p>
      </div>

      {Object.entries(groupedNotebooks).map(([modelType, modelNotebooks]) => {
        const modelInfo = modelCategories[modelType as keyof typeof modelCategories];
        
        return (
          <Card key={modelType} className="border-l-4 border-l-primary">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <GitBranch className="h-5 w-5" />
                    {modelInfo?.name || modelType}
                  </CardTitle>
                  <CardDescription>
                    {modelInfo?.description || `Notebooks for ${modelType} model`}
                  </CardDescription>
                </div>
                {modelInfo && (
                  <Badge variant="secondary">{modelInfo.type}</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3">
                {modelNotebooks.map((notebook) => (
                  <div key={notebook.id} className="group border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-md bg-primary/10">
                          <FileText className="h-4 w-4 text-primary" />
                        </div>
                        <div className="space-y-1">
                          <h4 className="font-medium group-hover:text-primary transition-colors">
                            {notebook.name}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            {notebook.description}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Badge variant="outline" className="text-xs">
                              v{notebook.version}
                            </Badge>
                            <span>•</span>
                            <span className="capitalize">
                              {notebook.type.replace('_', ' ')}
                            </span>
                            <span>•</span>
                            <span>
                              {new Date(notebook.updated_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="ghost" asChild>
                          <a href={notebook.file_url} target="_blank" rel="noopener noreferrer">
                            <Play className="h-4 w-4 mr-1" />
                            Run
                          </a>
                        </Button>
                        <Button size="sm" variant="outline" asChild>
                          <a href={notebook.file_url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        );
      })}

      {Object.keys(groupedNotebooks).length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No notebooks available</h3>
            <p className="text-muted-foreground">
              There are no notebooks available for {languageName} yet.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default LanguageNotebooks;