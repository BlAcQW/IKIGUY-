import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Bot, MessageSquare, Users, Zap } from 'lucide-react';

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
        <CardDescription>
          Get started with common tasks
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button className="w-full justify-start gap-3" variant="outline">
          <Plus className="h-4 w-4" />
          Create Assistant
        </Button>
        <Button className="w-full justify-start gap-3" variant="outline">
          <MessageSquare className="h-4 w-4" />
          Launch Campaign
        </Button>
        <Button className="w-full justify-start gap-3" variant="outline">
          <Users className="h-4 w-4" />
          Import Contacts
        </Button>
        <Button className="w-full justify-start gap-3" variant="outline">
          <Zap className="h-4 w-4" />
          Quick Setup
        </Button>
      </CardContent>
    </Card>
  );
}