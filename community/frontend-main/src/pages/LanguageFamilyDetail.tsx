import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, Globe, Users, MapPin, TrendingUp } from 'lucide-react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { apiClient } from '@/lib/api';
import type { LanguageFamily, LanguageBasic } from '@/lib/api';

const LanguageFamilyDetail: React.FC = () => {
  const { familyId } = useParams<{ familyId: string }>();
  const [family, setFamily] = useState<LanguageFamily | null>(null);
  const [languages, setLanguages] = useState<LanguageBasic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFamilyData = async () => {
      if (!familyId) return;

      try {
        setLoading(true);
        // Fetch family details and all languages in the family
        const [familyData, familyLanguages] = await Promise.all([
          fetch(`https://language-community-api.ailabsafrica.com/api/v1/languages/families/${familyId}`).then(res => res.json()),
          fetch(`https://language-community-api.ailabsafrica.com/api/v1/languages/families/${familyId}/languages`).then(res => res.json())
        ]);

        setFamily(familyData);
        setLanguages(familyLanguages);
      } catch (err) {
        console.error('Error fetching family data:', err);
        setError('Failed to load language family data');
      } finally {
        setLoading(false);
      }
    };

    fetchFamilyData();
  }, [familyId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading language family...</p>
            </div>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  if (error || !family) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-destructive mb-4">Family Not Found</h1>
            <p className="text-muted-foreground mb-6">{error || 'The requested language family could not be found.'}</p>
            <Button asChild>
              <Link to="/languages">Browse Languages</Link>
            </Button>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <div className="container mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/languages" className="flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Languages
            </Link>
          </Button>
        </div>

        {/* Family Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className={`w-4 h-4 rounded-full bg-${family.color || 'primary'}`}></div>
            <h1 className="text-3xl font-bold">{family.name}</h1>
            <Badge variant="secondary" className="capitalize">
              {family.priority_level} Priority
            </Badge>
          </div>

          <p className="text-lg text-muted-foreground mb-6 max-w-3xl">
            {family.description}
          </p>

          {/* Key Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardContent className="p-4 text-center">
                <Users className="w-6 h-6 text-primary mx-auto mb-2" />
                <div className="text-2xl font-bold">{family.total_speakers}</div>
                <div className="text-sm text-muted-foreground">Total Speakers</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <MapPin className="w-6 h-6 text-primary mx-auto mb-2" />
                <div className="text-2xl font-bold">{family.countries}</div>
                <div className="text-sm text-muted-foreground">Countries</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <TrendingUp className="w-6 h-6 text-primary mx-auto mb-2" />
                <div className="text-2xl font-bold">{family.total_contributions.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Contributions</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <Globe className="w-6 h-6 text-primary mx-auto mb-2" />
                <div className="text-2xl font-bold">{languages.length}</div>
                <div className="text-sm text-muted-foreground">Languages</div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Featured Languages */}
        {family.featured_languages && family.featured_languages.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Featured Languages</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {family.featured_languages.map((lang, index) => (
                  <Badge key={index} variant="outline">
                    {lang}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Top Languages */}
        {family.top_languages && family.top_languages.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Top Languages by Speakers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {family.top_languages.map((lang, index) => (
                  <div key={lang.code} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="text-lg font-semibold text-muted-foreground">#{index + 1}</div>
                      <div>
                        <Link
                          to={`/languages/${lang.code}`}
                          className="text-lg font-semibold hover:text-primary transition-colors"
                        >
                          {lang.name}
                        </Link>
                        <div className="text-sm text-muted-foreground">{lang.native_name}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">{lang.speakers.toLocaleString()} speakers</div>
                      <Badge variant={lang.tier === 'tier-1' ? 'default' : lang.tier === 'tier-2' ? 'secondary' : 'outline'}>
                        {lang.tier}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* All Languages */}
        <Card>
          <CardHeader>
            <CardTitle>All Languages ({languages.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {languages.map((lang) => (
                <Link
                  key={lang.code}
                  to={`/languages/${lang.code}`}
                  className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                >
                  <h3 className="font-semibold">{lang.name}</h3>
                  <p className="text-sm text-muted-foreground mb-2">{lang.native_name}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {lang.speakers.toLocaleString()} speakers
                    </span>
                    <Badge
                      variant={lang.tier === 'tier-1' ? 'default' : lang.tier === 'tier-2' ? 'secondary' : 'outline'}
                      className="text-xs"
                    >
                      {lang.tier}
                    </Badge>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Footer />
    </div>
  );
};

export default LanguageFamilyDetail;