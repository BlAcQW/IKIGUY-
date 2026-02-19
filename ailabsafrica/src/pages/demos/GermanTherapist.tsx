import React, { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, Heart, Brain, Clock, Users, Star, CheckCircle } from 'lucide-react';

const GermanTherapist = () => {
  useEffect(() => {
    document.title = "Mara - German Therapist | AI Labs Africa";
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <section className="py-16 bg-gradient-to-r from-pink-500 to-purple-600 text-white">
        <div className="container text-center">
          <h1 className="text-5xl font-bold mb-6">MARA</h1>
          <p className="text-2xl mb-4">Deine Tages-Coachin, ohne Shame & Blame</p>
          <p className="text-xl text-white/90 max-w-3xl mx-auto mb-8">
            Schaffe deinen Tag. Mit Ruhe und Selbstmitgefühl.
          </p>
          <Badge variant="secondary" className="bg-white text-purple-600 text-lg px-4 py-2">
            Neurodiversitäts-affirmativ
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
                  Sprich mit Mara, deiner neurodiversitäts-affirmativen KI-Begleiterin
                </h2>
                <p className="text-lg text-muted-foreground mb-6">
                  Sie hilft dir, deine Aufgaben mit kleinen, machbaren Schritten und ohne Druck zu meistern.
                </p>
              </div>

              {/* Features */}
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Clock className="h-5 w-5 text-blue-500" />
                      Time-Boxing
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>Starte Aufgaben in kurzen, fokussierten Sprints (z.B. 2 oder 10 Minuten), um Überforderung zu vermeiden.</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Users className="h-5 w-5 text-green-500" />
                      Body-Doubling
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>Mara bleibt als ruhige "Begleitstimme" bei dir, während du eine Aufgabe beginnst, um den Start zu erleichtern.</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Heart className="h-5 w-5 text-pink-500" />
                      Self-Compassion
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>Erhalte Unterstützung ohne Schuldzuweisungen. Jeder kleine Schritt ist ein Erfolg.</p>
                  </CardContent>
                </Card>
              </div>

              {/* Key Features */}
              <div>
                <h3 className="text-2xl font-bold mb-4">Was macht Mara besonders?</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Langsam sprechen (80-85% TTS Rate)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Kurze Sätze (5-8 Wörter)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Häufige Check-ins</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Kindgerechte Sprache</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>ADHS/Autismus-freundlich</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Ohne Druck & Schuld</span>
                  </div>
                </div>
              </div>

              {/* Safety Notice */}
              <Card className="border-orange-200 bg-orange-50">
                <CardHeader>
                  <CardTitle className="text-orange-800">Sicherheitshinweis</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-orange-700">
                    Mara ist keine Ärztin oder Therapeutin. Bei medizinischen Fragen oder Krisen wende dich bitte an Fachpersonen. 
                    EU-Notruf: <strong>112</strong> | DE TelefonSeelsorge: <strong>0800-1110111</strong>
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
                    Klicke auf das Widget unten rechts, um jetzt mit Mara zu sprechen.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center p-8 bg-gradient-to-br from-pink-50 to-purple-50 rounded-lg">
                    <Brain className="h-16 w-16 text-purple-500 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold mb-2">Mara ist bereit für dich</h3>
                    <p className="text-muted-foreground mb-4">
                      Sprich mit Mara über deine Aufgaben und lass dich sanft durch den Tag führen.
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* External Demo Link */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ExternalLink className="h-5 w-5" />
                    Vollständige Demo
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="mb-4">
                    Erlebe Mara in ihrer vollständigen Umgebung mit allen Funktionen.
                  </p>
                  <Button 
                    asChild 
                    variant="outline"
                    className="w-full"
                  >
                    <a 
                      href="https://ailabsafrica.com/demos/german-therapist.html" 
                      target="_blank" 
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Vollständige Demo öffnen
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

export default GermanTherapist;
