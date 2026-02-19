import React, { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, User, Target, Building, TrendingUp, Star, CheckCircle, Heart } from 'lucide-react';

const KojoBonsuCampaign = () => {
  useEffect(() => {
    document.title = "Kojo Bonsu Campaign | AI Labs Africa";
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <section className="py-16 bg-gradient-to-r from-emerald-600 to-green-700 text-white">
        <div className="container text-center">
          <h1 className="text-5xl font-bold mb-6">
            Honourable Kojo Bonsu
          </h1>
          <p className="text-2xl mb-4">
            Victory through Unity and Accountability
          </p>
          <p className="text-xl text-white/90 max-w-3xl mx-auto mb-8">
            Meet Kofi, your campaign manager for Honourable Kojo Bonsu's bid to become the NDC flagbearer and next President of Ghana
          </p>
          <Badge variant="secondary" className="bg-white text-emerald-600 text-lg px-4 py-2">
            NDC Flagbearer Campaign
          </Badge>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-16">
        <div className="container">
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            {/* Left Column - Description */}
            <div className="space-y-8">
              <div>
                <h2 className="text-3xl font-bold mb-4">
                  Meet Kofi, Your Campaign Manager
                </h2>
                <p className="text-lg text-muted-foreground mb-6">
                  Kofi is passionate, persuasive, and deeply knowledgeable about Honourable Kojo Bonsu's vision for Ghana. 
                  He connects past successes to future plans and aligns his vision with the NDC's historic achievements.
                </p>
              </div>

              {/* Key Qualities */}
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-blue-500" />
                      A Proven "Man of Action"
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>Honourable Bonsu has proven himself in business and public service, delivering tangible results as Mayor of Kumasi 
                    with projects like the Kejetia Market redevelopment and Rattray Park modernization.</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Heart className="h-5 w-5 text-red-500" />
                      A Unifier
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>His core message is "Victory through Unity and Accountability." He initiated the NDC Unity Walks to reconnect 
                    the party with its grassroots and create a "New NDC."</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Building className="h-5 w-5 text-purple-500" />
                      Economic Self-Sufficiency
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>His vision includes an agricultural revolution with the motto "What we eat we must produce," value addition 
                    through industrialization, and modern infrastructure including a monorail system for Accra and Kumasi.</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-green-500" />
                      Creating Opportunities
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>Aims to create ten local billionaires, ensure every graduate finds meaningful employment, and increase 
                    power generation by 5,000 megawatts to restore Ghana's status as a power exporter.</p>
                  </CardContent>
                </Card>
              </div>

              {/* Key Features */}
              <div>
                <h3 className="text-2xl font-bold mb-4">What Kofi can help you with:</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Campaign outreach</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Policy presentation</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Voter engagement</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Political advocacy</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Vision explanation</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Track record details</span>
                  </div>
                </div>
              </div>

              {/* Campaign Notice */}
              <Card className="border-emerald-200 bg-emerald-50">
                <CardHeader>
                  <CardTitle className="text-emerald-800">Campaign Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-emerald-700">
                    Kofi represents Honourable Kojo Bonsu's campaign for the NDC flagbearer position. All information is based on 
                    his official manifesto and campaign materials. This is a political campaign tool for voter education and engagement.
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Right Column - Demo Widget */}
            <div className="space-y-6">
              <Card className="sticky top-6">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Star className="h-5 w-5 text-yellow-500" />
                    Live Demo
                  </CardTitle>
                  <CardDescription>
                    Talk with Kofi about Honourable Kojo Bonsu's vision, policies, and campaign for Ghana's future.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center p-8 bg-gradient-to-br from-emerald-50 to-green-50 rounded-lg">
                    <User className="h-16 w-16 text-emerald-500 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold mb-2">Kofi is ready to engage</h3>
                    <p className="text-muted-foreground mb-4">
                      Learn about Honourable Kojo Bonsu's vision for Ghana, his track record, and his plans for the future.
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* External Demo Link */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ExternalLink className="h-5 w-5" />
                    Full Campaign Experience
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="mb-4">
                    Experience the complete Kojo Bonsu campaign demo with all features and detailed information.
                  </p>
                  <Button 
                    asChild 
                    variant="outline"
                    className="w-full"
                  >
                    <a 
                      href="https://ailabsafrica.com/demos/bonsu.html" 
                      target="_blank" 
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Open Full Demo
                    </a>
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default KojoBonsuCampaign;

