import React, { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, BookOpen, GraduationCap, Heart, Building, TrendingUp, Star, CheckCircle } from 'lucide-react';

const GreenBook = () => {
  useEffect(() => {
    document.title = "Green Book - NDC Achievements | AI Labs Africa";
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <section className="py-16 bg-gradient-to-r from-green-600 to-emerald-700 text-white">
        <div className="container text-center">
          <h1 className="text-5xl font-bold mb-6">
            The Green Book
          </h1>
          <p className="text-2xl mb-4">
            Accounting to the People
          </p>
          <p className="text-xl text-white/90 max-w-3xl mx-auto mb-8">
            Discover the comprehensive achievements of the NDC government under President John Dramani Mahama
          </p>
          <Badge variant="secondary" className="bg-white text-green-600 text-lg px-4 py-2">
            NDC Achievements 2008-2016
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
                  Meet Abena, Your NDC Guide
                </h2>
                <p className="text-lg text-muted-foreground mb-6">
                  Abena is your knowledgeable, friendly, and engaging virtual guide to the National Democratic Congress (NDC). 
                  She provides clear, factual, and detailed information based on the "Accounting to the People" (Green Book) document.
                </p>
              </div>

              {/* Key Achievements */}
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <GraduationCap className="h-5 w-5 text-blue-500" />
                      Education Transformation
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>Massive expansion of 11,823 educational institutions, elimination of 1,614 "Schools Under Trees" projects, 
                    and establishment of new universities like UHAS and UENR.</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Heart className="h-5 w-5 text-red-500" />
                      Healthcare for All
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>US$2 billion investment in health infrastructure, 6,000 new hospital beds, and NHIS claims growing to 
                    over GH¢1 billion in 2014.</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Building className="h-5 w-5 text-purple-500" />
                      Modern Infrastructure
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>Iconic projects like the Kwame Nkrumah Interchange, Atuabo Gas Processing Plant, and 76% national 
                    water coverage achieved.</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-green-500" />
                      Economic Growth
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>364,665 new workers registered, revival of local industries like Kumasi Shoe Factory, and 
                    implementation of anti-corruption measures.</p>
                  </CardContent>
                </Card>
              </div>

              {/* Key Features */}
              <div>
                <h3 className="text-2xl font-bold mb-4">What Abena can help you with:</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Detailed project information</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Statistical data and figures</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Policy explanations</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Historical context</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Infrastructure details</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Social program information</span>
                  </div>
                </div>
              </div>

              {/* Information Notice */}
              <Card className="border-blue-200 bg-blue-50">
                <CardHeader>
                  <CardTitle className="text-blue-800">Information Source</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-blue-700">
                    All information provided by Abena is sourced exclusively from the "Accounting to the People" 
                    (Green Book) document published in December 2015. This ensures accuracy and factual reliability.
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
                    Ask Abena about any NDC achievement, project, or policy from the Green Book.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center p-8 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
                    <BookOpen className="h-16 w-16 text-green-500 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold mb-2">Abena is ready to help</h3>
                    <p className="text-muted-foreground mb-4">
                      Get detailed information about NDC achievements, infrastructure projects, and policy implementations.
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* External Demo Link */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ExternalLink className="h-5 w-5" />
                    Full Demo Experience
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="mb-4">
                    Experience the complete Green Book demo with all features and detailed information.
                  </p>
                  <Button 
                    asChild 
                    variant="outline"
                    className="w-full"
                  >
                    <a 
                      href="https://ailabsafrica.com/demos/green-book.html" 
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

export default GreenBook;

