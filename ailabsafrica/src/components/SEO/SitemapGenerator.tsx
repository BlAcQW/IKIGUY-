/**
 * Sitemap Generator Component
 * Handles dynamic sitemap generation and provides admin interface for SEO management
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import { Download, Upload, RefreshCw, Settings, Globe, FileText, Search } from 'lucide-react';
import {
  SitemapConfig,
  DEFAULT_SITEMAP_CONFIG,
  generateSitemapXML,
  generateSitemapIndexXML,
  generateRobotsTxt,
  validateSitemapConfig,
  mergeLanguageConfigs,
  LANGUAGE_PAGE_CONFIGS
} from '@/lib/sitemap';
import { PageSEOData } from '@/lib/seo';

interface SitemapGeneratorProps {
  isAdmin?: boolean;
}

const SitemapGenerator: React.FC<SitemapGeneratorProps> = ({ isAdmin = false }) => {
  const { toast } = useToast();
  const [config, setConfig] = useState<SitemapConfig>(DEFAULT_SITEMAP_CONFIG);
  const [generatedSitemap, setGeneratedSitemap] = useState<string>('');
  const [generatedRobots, setGeneratedRobots] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Generate sitemap on config change
  useEffect(() => {
    const validation = validateSitemapConfig(config);
    setValidationErrors(validation.errors);
    
    if (validation.isValid) {
      generateSitemap();
      generateRobotsFile();
    }
  }, [config]);

  const generateSitemap = () => {
    try {
      const mergedPages = mergeLanguageConfigs(config.pages, LANGUAGE_PAGE_CONFIGS);
      const updatedConfig = { ...config, pages: mergedPages };
      const sitemapXML = generateSitemapXML(updatedConfig);
      setGeneratedSitemap(sitemapXML);
    } catch (error) {
      console.error('Error generating sitemap:', error);
      toast({
        title: 'Error',
        description: 'Failed to generate sitemap',
        variant: 'destructive'
      });
    }
  };

  const generateRobotsFile = () => {
    try {
      const robotsTxt = generateRobotsTxt(config.baseUrl, `${config.baseUrl}/sitemap.xml`);
      setGeneratedRobots(robotsTxt);
    } catch (error) {
      console.error('Error generating robots.txt:', error);
    }
  };

  const downloadSitemap = () => {
    const blob = new Blob([generatedSitemap], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sitemap.xml';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast({
      title: 'Success',
      description: 'Sitemap downloaded successfully'
    });
  };

  const downloadRobots = () => {
    const blob = new Blob([generatedRobots], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'robots.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast({
      title: 'Success',
      description: 'Robots.txt downloaded successfully'
    });
  };

  const updatePage = (index: number, updates: Partial<PageSEOData>) => {
    const updatedPages = [...config.pages];
    updatedPages[index] = { ...updatedPages[index], ...updates };
    setConfig({ ...config, pages: updatedPages });
  };

  const addPage = () => {
    const newPage: PageSEOData = {
      path: '/new-page',
      title: 'New Page',
      description: 'Description for the new page',
      keywords: ['new', 'page'],
      lastModified: new Date().toISOString(),
      changeFrequency: 'weekly',
      priority: 0.5,
      language: 'en'
    };
    setConfig({ ...config, pages: [...config.pages, newPage] });
  };

  const removePage = (index: number) => {
    const updatedPages = config.pages.filter((_, i) => i !== index);
    setConfig({ ...config, pages: updatedPages });
  };

  const calculateCompletion = () => {
    const totalFields = config.pages.length * 7; // 7 fields per page
    let completedFields = 0;
    
    config.pages.forEach(page => {
      if (page.path) completedFields++;
      if (page.title) completedFields++;
      if (page.description) completedFields++;
      if (page.keywords.length > 0) completedFields++;
      if (page.lastModified) completedFields++;
      if (page.changeFrequency) completedFields++;
      if (page.priority >= 0) completedFields++;
    });
    
    return Math.round((completedFields / totalFields) * 100);
  };

  const completionPercentage = calculateCompletion();

  if (!isAdmin) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            SEO Status
          </CardTitle>
          <CardDescription>
            Current SEO configuration and sitemap status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Configuration Completion</span>
              <Badge variant={completionPercentage >= 80 ? 'default' : 'secondary'}>
                {completionPercentage}%
              </Badge>
            </div>
            <Progress value={completionPercentage} className="w-full" />
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Pages:</span> {config.pages.length}
              </div>
              <div>
                <span className="font-medium">Languages:</span> {config.languages.length}
              </div>
              <div>
                <span className="font-medium">Base URL:</span> {config.baseUrl}
              </div>
              <div>
                <span className="font-medium">Last Updated:</span> {new Date(config.lastModified).toLocaleDateString()}
              </div>
            </div>
            
            {validationErrors.length > 0 && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <h4 className="text-sm font-medium text-red-800 mb-2">Configuration Issues:</h4>
                <ul className="text-sm text-red-700 space-y-1">
                  {validationErrors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Configuration Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Sitemap Configuration
          </CardTitle>
          <CardDescription>
            Configure your sitemap settings and page information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Basic Configuration */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="baseUrl">Base URL</Label>
              <Input
                id="baseUrl"
                value={config.baseUrl}
                onChange={(e) => setConfig({ ...config, baseUrl: e.target.value })}
                placeholder="https://ailabsafrica.com"
              />
            </div>
            <div>
              <Label htmlFor="defaultLanguage">Default Language</Label>
              <Select
                value={config.defaultLanguage}
                onValueChange={(value) => setConfig({ ...config, defaultLanguage: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {config.languages.map(lang => (
                    <SelectItem key={lang} value={lang}>
                      {lang.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Languages */}
          <div>
            <Label>Supported Languages</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {config.languages.map(lang => (
                <Badge key={lang} variant="outline">
                  {lang.toUpperCase()}
                </Badge>
              ))}
            </div>
          </div>

          {/* Completion Status */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Configuration Completion</span>
            <Badge variant={completionPercentage >= 80 ? 'default' : 'secondary'}>
              {completionPercentage}%
            </Badge>
          </div>
          <Progress value={completionPercentage} className="w-full" />
        </CardContent>
      </Card>

      {/* Pages Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Pages Configuration
          </CardTitle>
          <CardDescription>
            Configure SEO settings for each page
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {config.pages.map((page, index) => (
            <div key={index} className="border rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Page {index + 1}</h4>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => removePage(index)}
                >
                  Remove
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Path</Label>
                  <Input
                    value={page.path}
                    onChange={(e) => updatePage(index, { path: e.target.value })}
                    placeholder="/page-path"
                  />
                </div>
                <div>
                  <Label>Title</Label>
                  <Input
                    value={page.title}
                    onChange={(e) => updatePage(index, { title: e.target.value })}
                    placeholder="Page Title"
                  />
                </div>
              </div>
              
              <div>
                <Label>Description</Label>
                <Textarea
                  value={page.description}
                  onChange={(e) => updatePage(index, { description: e.target.value })}
                  placeholder="Page description for SEO"
                  rows={2}
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label>Change Frequency</Label>
                  <Select
                    value={page.changeFrequency}
                    onValueChange={(value: any) => updatePage(index, { changeFrequency: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="always">Always</SelectItem>
                      <SelectItem value="hourly">Hourly</SelectItem>
                      <SelectItem value="daily">Daily</SelectItem>
                      <SelectItem value="weekly">Weekly</SelectItem>
                      <SelectItem value="monthly">Monthly</SelectItem>
                      <SelectItem value="yearly">Yearly</SelectItem>
                      <SelectItem value="never">Never</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Priority</Label>
                  <Input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={page.priority}
                    onChange={(e) => updatePage(index, { priority: parseFloat(e.target.value) })}
                  />
                </div>
                <div>
                  <Label>Language</Label>
                  <Select
                    value={page.language}
                    onValueChange={(value) => updatePage(index, { language: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {config.languages.map(lang => (
                        <SelectItem key={lang} value={lang}>
                          {lang.toUpperCase()}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          ))}
          
          <Button onClick={addPage} variant="outline" className="w-full">
            Add Page
          </Button>
        </CardContent>
      </Card>

      {/* Generated Files */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Generated Files
          </CardTitle>
          <CardDescription>
            Download generated sitemap and robots.txt files
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button onClick={downloadSitemap} disabled={!generatedSitemap}>
              <Download className="h-4 w-4 mr-2" />
              Download Sitemap
            </Button>
            <Button onClick={downloadRobots} disabled={!generatedRobots}>
              <Download className="h-4 w-4 mr-2" />
              Download Robots.txt
            </Button>
            <Button onClick={generateSitemap} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Regenerate
            </Button>
          </div>
          
          {validationErrors.length > 0 && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <h4 className="text-sm font-medium text-red-800 mb-2">Configuration Issues:</h4>
              <ul className="text-sm text-red-700 space-y-1">
                {validationErrors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SitemapGenerator;
