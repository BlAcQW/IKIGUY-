import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Users, BookOpen, Globe, Loader2 } from "lucide-react";
import { realApiClient } from "@/lib/realApi";

const Languages = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [languageFamilies, setLanguageFamilies] = useState<any[]>([]);
  const [featuredLanguages, setFeaturedLanguages] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    loadData();

    // Check for search parameter from URL
    const searchParam = searchParams.get('search');
    if (searchParam) {
      setSearchQuery(searchParam);
    }
  }, [searchParams]);

  useEffect(() => {
    if (searchQuery.length >= 2) {
      performSearch();
    } else {
      setSearchResults([]);
    }
  }, [searchQuery]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [familiesData, languagesData, statsData] = await Promise.all([
        realApiClient.getLanguageFamilies(),
        realApiClient.getLanguages(),
        realApiClient.getLanguageStats()
      ]);

      setLanguageFamilies(familiesData);
      // Use first 6 languages as featured
      setFeaturedLanguages(languagesData.slice(0, 6));
      setStats(statsData);
    } catch (error) {
      console.error("Failed to load data:", error);
      // Fallback to mock data
      setLanguageFamilies([
        { id: '1', name: 'Niger-Congo', language_count: 45, description: 'Largest language family in Africa' },
        { id: '2', name: 'Afro-Asiatic', language_count: 25, description: 'Includes Arabic and Ethiopian languages' },
        { id: '3', name: 'Nilo-Saharan', language_count: 15, description: 'Central and Eastern African languages' }
      ]);
      setFeaturedLanguages([
        { code: 'yo', name: 'Yoruba', native_name: 'Yorùbá', speakers: 45000000, family: 'Niger-Congo' },
        { code: 'ig', name: 'Igbo', native_name: 'Igbo', speakers: 27000000, family: 'Niger-Congo' },
        { code: 'sw', name: 'Swahili', native_name: 'Kiswahili', speakers: 150000000, family: 'Niger-Congo' },
        { code: 'am', name: 'Amharic', native_name: 'አማርኛ', speakers: 32000000, family: 'Afro-Asiatic' },
        { code: 'zu', name: 'Zulu', native_name: 'isiZulu', speakers: 12000000, family: 'Niger-Congo' },
        { code: 'ha', name: 'Hausa', native_name: 'Harshen Hausa', speakers: 70000000, family: 'Afro-Asiatic' }
      ]);
      setStats({ total_languages: 120, total_families: 4, most_contributed: 'Yoruba', total_hours: 15000 });
    } finally {
      setLoading(false);
    }
  };

  const performSearch = async () => {
    if (searchQuery.length < 2) return;

    try {
      setSearching(true);
      const results = await realApiClient.searchLanguages(searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error("Search failed:", error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleLanguageClick = (languageCode: string) => {
    navigate(`/languages/${languageCode}`);
  };

  const handleFamilyExplore = (familyId: string) => {
    navigate(`/languages/families/${familyId}`);
  };

  const handleSearchResultClick = (languageCode: string) => {
    navigate(`/languages/${languageCode}`);
    setSearchQuery("");
    setSearchResults([]);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">African Languages</h1>
          <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
            Explore the rich diversity of African languages across major language families.
            Discover resources, datasets, and AI models for each language.
          </p>
        </div>

        {/* Search */}
        <div className="mb-8 max-w-md mx-auto">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search languages..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searching && (
              <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin" />
            )}
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="mt-4 bg-white border rounded-lg shadow-lg p-4 max-h-60 overflow-y-auto">
              <h3 className="font-semibold mb-2">Search Results</h3>
              <div className="space-y-2">
                {searchResults.map((result) => (
                  <div
                    key={result.code}
                    className="flex items-center justify-between p-2 hover:bg-gray-50 rounded cursor-pointer"
                    onClick={() => handleSearchResultClick(result.code)}
                  >
                    <div>
                      <div className="font-medium">{result.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {result.native_name} • {result.family} • {result.speakers.toLocaleString()} speakers
                      </div>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {result.tier}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Language Families Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {loading ? (
            <div className="col-span-full flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            languageFamilies.map((family) => (
              <Card key={family.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl">{family.name}</CardTitle>
                    <Badge variant="secondary">{family.top_languages.length} languages</Badge>
                  </div>
                  <CardDescription>{family.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Stats */}
                    <div className="flex gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        {family.total_speakers} speakers
                      </div>
                      <div className="flex items-center gap-1">
                        <Globe className="h-4 w-4" />
                        {family.countries} countries
                      </div>
                    </div>

                    {/* Language Tags */}
                    <div className="flex flex-wrap gap-2">
                      {family.top_languages.map((lang) => (
                        <Badge key={lang.code} variant="outline" className="text-xs">
                          {lang.name}
                        </Badge>
                      ))}
                    </div>

                    {/* Action Button */}
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full mt-4"
                      onClick={() => handleFamilyExplore(family.id)}
                    >
                      <BookOpen className="h-4 w-4 mr-2" />
                      Explore {family.name} Languages
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Featured Languages Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-6">Featured Languages</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {loading ? (
              <div className="col-span-full flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              featuredLanguages.map((lang) => (
                <Card
                  key={lang.code}
                  className="hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => handleLanguageClick(lang.code)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold">{lang.name}</h3>
                      <Badge variant="secondary" className="text-xs">
                        {lang.priority_level === 'high' ? 'High Priority' :
                         lang.priority_level === 'medium' ? 'Medium Priority' : 'Low Priority'}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                      {lang.speakers.toLocaleString()} speakers • {lang.progress}% progress
                    </p>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Languages;