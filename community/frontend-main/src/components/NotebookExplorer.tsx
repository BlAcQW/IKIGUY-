import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient, Language, Notebook, ModelType } from "@/lib/api";
import { ExternalLink, Download, Book, Cpu, Mic, Volume2, MessageSquare } from "lucide-react";

const NotebookExplorer = () => {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [modelTypes, setModelTypes] = useState<ModelType[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("all");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedLanguage !== "all" || selectedType !== "all") {
      loadNotebooks();
    }
  }, [selectedLanguage, selectedType]);

  const loadInitialData = async () => {
    try {
      const [languagesData, modelTypesData, notebooksData] = await Promise.all([
        apiClient.getLanguages(),
        apiClient.getModelTypes(),
        apiClient.getNotebooks()
      ]);
      
      setLanguages(languagesData);
      setModelTypes(modelTypesData);
      setNotebooks(notebooksData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadNotebooks = async () => {
    try {
      const notebooksData = await apiClient.getNotebooks(
        selectedLanguage === "all" ? undefined : selectedLanguage,
        selectedType === "all" ? undefined : selectedType
      );
      setNotebooks(notebooksData);
    } catch (error) {
      console.error('Failed to load notebooks:', error);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'data_acquisition': return <Download className="h-4 w-4" />;
      case 'data_processing': return <Cpu className="h-4 w-4" />;
      case 'training': return <Book className="h-4 w-4" />;
      case 'inference': return <MessageSquare className="h-4 w-4" />;
      default: return <Book className="h-4 w-4" />;
    }
  };

  const getModelIcon = (category: string) => {
    switch (category) {
      case 'asr': return <Mic className="h-4 w-4" />;
      case 'tts': return <Volume2 className="h-4 w-4" />;
      case 'llm': return <MessageSquare className="h-4 w-4" />;
      default: return <Cpu className="h-4 w-4" />;
    }
  };

  const groupedNotebooks = notebooks.reduce((acc, notebook) => {
    const key = `${notebook.language_code}_${notebook.model_type || 'general'}`;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(notebook);
    return acc;
  }, {} as Record<string, Notebook[]>);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-muted animate-pulse rounded" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-muted animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4">
        <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Select Language" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Languages</SelectItem>
            {languages.map((language) => (
              <SelectItem key={language.code} value={language.code}>
                {language.name} ({language.code})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedType} onValueChange={setSelectedType}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Notebook Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="data_acquisition">Data Acquisition</SelectItem>
            <SelectItem value="data_processing">Data Processing</SelectItem>
            <SelectItem value="training">Training</SelectItem>
            <SelectItem value="inference">Inference</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="notebooks" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="notebooks">Notebooks</TabsTrigger>
          <TabsTrigger value="models">Model Types</TabsTrigger>
        </TabsList>

        <TabsContent value="notebooks" className="space-y-4">
          {Object.entries(groupedNotebooks).map(([key, notebookGroup]) => {
            const [langCode, modelType] = key.split('_');
            const language = languages.find(l => l.code === langCode);
            
            return (
              <Card key={key} className="border-l-4 border-l-accent">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      {language?.name || langCode}
                      {modelType !== 'general' && (
                        <Badge variant="secondary">{modelType}</Badge>
                      )}
                    </CardTitle>
                    <Badge variant="outline">
                      {notebookGroup.length} notebook{notebookGroup.length !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                  <CardDescription>
                    Available notebooks for {language?.name || langCode}
                    {modelType !== 'general' && ` with ${modelType} models`}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3">
                    {notebookGroup.map((notebook) => (
                      <div key={notebook.id} className="flex items-center justify-between p-3 rounded-lg border bg-card/50">
                        <div className="flex items-center gap-3">
                          {getTypeIcon(notebook.type)}
                          <div>
                            <h4 className="font-medium">{notebook.name}</h4>
                            <p className="text-sm text-muted-foreground">
                              v{notebook.version} • {notebook.description}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {notebook.type.replace('_', ' ')}
                          </Badge>
                          <Button size="sm" variant="ghost" asChild>
                            <a href={notebook.file_url} target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </TabsContent>

        <TabsContent value="models" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {modelTypes.map((modelType) => (
              <Card key={modelType.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {getModelIcon(modelType.category)}
                    {modelType.name}
                  </CardTitle>
                  <CardDescription>{modelType.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <Badge variant="secondary" className="capitalize">
                      {modelType.category}
                    </Badge>
                    <div>
                      <h5 className="text-sm font-medium mb-2">Supported Languages:</h5>
                      <div className="flex flex-wrap gap-1">
                        {modelType.supported_languages.slice(0, 3).map((lang) => (
                          <Badge key={lang} variant="outline" className="text-xs">
                            {lang}
                          </Badge>
                        ))}
                        {modelType.supported_languages.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{modelType.supported_languages.length - 3} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NotebookExplorer;