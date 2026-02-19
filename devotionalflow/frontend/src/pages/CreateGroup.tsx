/**
 * Create Group Page
 * Form to create a new Bible study group
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ArrowLeft, Globe, Lock, BookOpen } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { MainNavigation } from '@/components/navigation/MainNavigation';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

export default function CreateGroup() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_public: true,
    discussion_topic: '',
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      return await apiClient.createGroup(data);
    },
    onSuccess: (group) => {
      toast({
        title: "Group created!",
        description: "Your Bible study group is ready",
      });
      navigate(`/groups/${group.id}`);
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to create group",
        variant: "destructive"
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast({
        title: "Name required",
        description: "Please enter a group name",
        variant: "destructive"
      });
      return;
    }

    createMutation.mutate(formData);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center pb-20">
        <div className="text-center max-w-md px-4">
          <h2 className="font-serif text-2xl font-bold mb-2">Sign In Required</h2>
          <p className="text-muted-foreground mb-6">
            Please sign in to create a group
          </p>
          <div className="flex gap-3 justify-center">
            <Button onClick={() => navigate('/login?redirect=/groups/new')}>
              Sign In
            </Button>
            <Button variant="outline" onClick={() => navigate('/signup?redirect=/groups/new')}>
              Create Account
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      <MainNavigation />

      <div className="container mx-auto px-4 py-6">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="flex items-center gap-4 mb-6">
            <Button variant="ghost" size="icon" onClick={() => navigate('/groups')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-serif text-2xl font-bold text-foreground">
                Create Bible Study Group
              </h1>
              <p className="text-sm text-muted-foreground">
                Start a community to study and grow together
              </p>
            </div>
          </div>

          {/* Form */}
          <motion.form
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            onSubmit={handleSubmit}
            className="space-y-6"
          >
            {/* Group Name */}
            <div className="space-y-2">
              <Label htmlFor="name">Group Name *</Label>
              <Input
                id="name"
                placeholder="e.g., Young Adults Bible Study"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                maxLength={100}
              />
              <p className="text-xs text-muted-foreground">
                Choose a clear, descriptive name for your group
              </p>
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Tell others what this group is about..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
                maxLength={500}
              />
              <p className="text-xs text-muted-foreground">
                {formData.description.length}/500 characters
              </p>
            </div>

            {/* Privacy */}
            <div className="space-y-2">
              <Label>Privacy</Label>
              <RadioGroup
                value={formData.is_public ? 'public' : 'private'}
                onValueChange={(value) => setFormData({ ...formData, is_public: value === 'public' })}
              >
                <div className="flex items-center space-x-2 p-4 border border-border rounded-lg hover:bg-muted/50">
                  <RadioGroupItem value="public" id="public" />
                  <Label htmlFor="public" className="flex-1 cursor-pointer">
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4" />
                      <div>
                        <p className="font-medium">Public</p>
                        <p className="text-xs text-muted-foreground">
                          Anyone can find and join this group
                        </p>
                      </div>
                    </div>
                  </Label>
                </div>
                <div className="flex items-center space-x-2 p-4 border border-border rounded-lg hover:bg-muted/50">
                  <RadioGroupItem value="private" id="private" />
                  <Label htmlFor="private" className="flex-1 cursor-pointer">
                    <div className="flex items-center gap-2">
                      <Lock className="w-4 h-4" />
                      <div>
                        <p className="font-medium">Private</p>
                        <p className="text-xs text-muted-foreground">
                          Only invited members can join
                        </p>
                      </div>
                    </div>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Discussion Topic */}
            <div className="space-y-2">
              <Label htmlFor="topic">Discussion Topic (Optional)</Label>
              <Input
                id="topic"
                placeholder="e.g., Book of Romans, Prayer, Faith"
                value={formData.discussion_topic}
                onChange={(e) => setFormData({ ...formData, discussion_topic: e.target.value })}
                maxLength={200}
              />
              <p className="text-xs text-muted-foreground">
                What will this group focus on?
              </p>
            </div>

            {/* Submit */}
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/groups')}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending || !formData.name.trim()}
                className="flex-1 gap-2"
              >
                {createMutation.isPending ? (
                  <>
                    <span className="w-4 h-4 border-2 border-secondary-foreground/30 border-t-secondary-foreground rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <BookOpen className="w-4 h-4" />
                    Create Group
                  </>
                )}
              </Button>
            </div>
          </motion.form>
        </div>
      </div>

    </div>
  );
}

