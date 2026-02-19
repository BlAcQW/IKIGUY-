/**
 * Map View Page
 *
 * Interactive map showing all properties with markers.
 * Coming soon - will integrate with mapping library.
 */

import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Map as MapIcon, ArrowLeft } from "lucide-react";

export default function Map() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background pb-20 md:pb-0">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        {/* Header - Desktop only */}
        <div className="hidden md:flex items-center gap-3 mb-6">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/properties")}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-2xl font-bold">Property Map</h1>
        </div>

        {/* Mobile Header */}
        <div className="md:hidden mb-4">
          <h1 className="text-xl font-bold">Property Map</h1>
          <p className="text-sm text-muted-foreground">
            Explore properties on map
          </p>
        </div>

        {/* Coming Soon Card */}
        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-12 text-center space-y-6">
            <div className="flex justify-center">
              <div className="p-6 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20">
                <MapIcon className="h-16 w-16 text-primary" />
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-bold mb-2">Interactive Map Coming Soon</h2>
              <p className="text-muted-foreground">
                We're building an interactive map to help you explore properties by location.
                Features will include:
              </p>
            </div>
            <ul className="text-left max-w-md mx-auto space-y-2 text-sm text-muted-foreground">
              <li>• Interactive markers for all properties</li>
              <li>• Cluster view for high-density areas</li>
              <li>• Quick property preview cards</li>
              <li>• Draw custom search boundaries</li>
              <li>• Filter by price, type, and amenities</li>
              <li>• Nearby schools, hospitals, and amenities</li>
            </ul>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button
                onClick={() => navigate("/properties")}
                size="lg"
              >
                Browse Properties
              </Button>
              <Button
                onClick={() => navigate("/contact")}
                variant="outline"
                size="lg"
              >
                Request Early Access
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
