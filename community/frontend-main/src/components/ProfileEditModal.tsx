import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  User,
  Mail,
  MapPin,
  Globe,
  Settings,
  Camera,
  Save,
  X,
  Plus,
  Trash2,
  Bell,
  Lock,
  Eye,
  EyeOff,
  Loader2
} from 'lucide-react';
import { useBackendAuth } from '@/contexts/BackendAuthContext';

interface ProfileEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave?: () => void;
}

interface ProfileData {
  username: string;
  full_name: string;
  bio: string;
  location: string;
  website: string;
  avatar_url: string;
  languages_spoken: string[];
  language_expertise: any[];
  preferences: {
    notifications: {
      email_updates: boolean;
      submission_status: boolean;
      validation_alerts: boolean;
      community_updates: boolean;
    };
    privacy: {
      profile_visibility: 'public' | 'private' | 'community';
      show_email: boolean;
      show_location: boolean;
      show_activity: boolean;
    };
    accessibility: {
      high_contrast: boolean;
      reduced_motion: boolean;
      large_text: boolean;
    };
  };
}

const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

export const ProfileEditModal: React.FC<ProfileEditModalProps> = ({
  isOpen,
  onClose,
  onSave
}) => {
  const { user, updateProfile } = useBackendAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [newLanguage, setNewLanguage] = useState('');
  const [availableLanguages, setAvailableLanguages] = useState<any[]>([]);

  const [profileData, setProfileData] = useState<ProfileData>({
    username: '',
    full_name: '',
    bio: '',
    location: '',
    website: '',
    avatar_url: '',
    languages_spoken: [],
    language_expertise: [],
    preferences: {
      notifications: {
        email_updates: true,
        submission_status: true,
        validation_alerts: true,
        community_updates: false,
      },
      privacy: {
        profile_visibility: 'public',
        show_email: false,
        show_location: true,
        show_activity: true,
      },
      accessibility: {
        high_contrast: false,
        reduced_motion: false,
        large_text: false,
      },
    },
  });

  // Load profile data when modal opens
  useEffect(() => {
    if (isOpen && user) {
      loadProfileData();
      loadAvailableLanguages();
    }
  }, [isOpen, user]);

  const loadProfileData = async () => {
    if (!user) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('auth_access_token');
      if (!token) {
        console.error('No auth token found');
        return;
      }

      const response = await fetch(`${API_BASE}/auth/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load profile');
      }

      const result = await response.json();
      const userProfile = result.data || result;

      if (userProfile) {
        setProfileData({
          username: userProfile.username || '',
          full_name: userProfile.full_name || '',
          bio: userProfile.bio || '',
          location: userProfile.location || '',
          website: userProfile.website || '',
          avatar_url: userProfile.avatar_url || '',
          languages_spoken: userProfile.languages_spoken || [],
          language_expertise: userProfile.language_expertise || [],
          preferences: {
            notifications: userProfile.preferences?.notifications || profileData.preferences.notifications,
            privacy: userProfile.preferences?.privacy || profileData.preferences.privacy,
            accessibility: userProfile.preferences?.accessibility || profileData.preferences.accessibility,
          },
        });
      }
    } catch (error) {
      console.error('Failed to load profile data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableLanguages = async () => {
    try {
      const response = await fetch(`${API_BASE}/languages`);
      if (response.ok) {
        const data = await response.json();
        setAvailableLanguages(data.items || data || []);
      }
    } catch (error) {
      console.error('Failed to load languages:', error);
    }
  };

  const handleSave = async () => {
    if (!user) return;

    setSaving(true);
    try {
      const token = localStorage.getItem('auth_access_token');
      if (!token) {
        throw new Error('No auth token found');
      }

      const response = await fetch(`${API_BASE}/auth/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update profile');
      }

      const result = await response.json();
      const updatedUser = result.data || result;

      // Update auth context
      if (updateProfile) {
        await updateProfile(updatedUser);
      }

      onSave?.();
      onClose();
    } catch (error: any) {
      console.error('Failed to save profile:', error);
      alert(error.message || 'Failed to save profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handlePreferenceChange = (category: string, field: string, value: any) => {
    setProfileData(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [category]: {
          ...prev.preferences[category as keyof typeof prev.preferences],
          [field]: value
        }
      }
    }));
  };

  const addLanguage = () => {
    if (newLanguage && !profileData.languages_spoken.includes(newLanguage)) {
      setProfileData(prev => ({
        ...prev,
        languages_spoken: [...prev.languages_spoken, newLanguage]
      }));
      setNewLanguage('');
    }
  };

  const removeLanguage = (language: string) => {
    setProfileData(prev => ({
      ...prev,
      languages_spoken: prev.languages_spoken.filter(l => l !== language)
    }));
  };

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file
    if (file.size > 5 * 1024 * 1024) {
      alert('Avatar image must be less than 5MB');
      return;
    }

    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    try {
      setSaving(true);

      // For now, use a placeholder URL
      // TODO: Implement file upload endpoint in backend
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result as string;
        handleInputChange('avatar_url', base64String);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Avatar upload failed:', error);
      alert('Failed to upload avatar. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-2xl">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2">Loading profile...</span>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Profile</DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="languages">Languages</TabsTrigger>
            <TabsTrigger value="preferences">Preferences</TabsTrigger>
            <TabsTrigger value="privacy">Privacy</TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile" className="space-y-6">
            <div className="grid gap-6">
              {/* Avatar Section */}
              <div className="flex items-center gap-6">
                <div className="relative">
                  <Avatar className="h-24 w-24">
                    <AvatarImage src={profileData.avatar_url} alt="Profile picture" />
                    <AvatarFallback className="text-lg">
                      {profileData.full_name?.split(' ').map(n => n[0]).join('') || 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <Button
                    size="sm"
                    className="absolute -bottom-2 -right-2"
                    onClick={() => document.getElementById('avatar-upload')?.click()}
                    disabled={saving}
                  >
                    <Camera className="h-4 w-4" />
                  </Button>
                  <input
                    id="avatar-upload"
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarUpload}
                    className="hidden"
                  />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold">Profile Picture</h3>
                  <p className="text-sm text-muted-foreground">
                    Upload a profile picture. Max size: 5MB
                  </p>
                </div>
              </div>

              {/* Basic Information */}
              <div className="grid gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="username"
                        value={profileData.username}
                        onChange={(e) => handleInputChange('username', e.target.value)}
                        className="pl-10"
                        placeholder="Enter username"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input
                      id="full_name"
                      value={profileData.full_name}
                      onChange={(e) => handleInputChange('full_name', e.target.value)}
                      placeholder="Enter full name"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bio">Bio</Label>
                  <Textarea
                    id="bio"
                    value={profileData.bio}
                    onChange={(e) => handleInputChange('bio', e.target.value)}
                    placeholder="Tell us about yourself..."
                    rows={3}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="location">Location</Label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="location"
                        value={profileData.location}
                        onChange={(e) => handleInputChange('location', e.target.value)}
                        className="pl-10"
                        placeholder="Your location"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="website">Website</Label>
                    <div className="relative">
                      <Globe className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="website"
                        value={profileData.website}
                        onChange={(e) => handleInputChange('website', e.target.value)}
                        className="pl-10"
                        placeholder="https://yourwebsite.com"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Languages Tab */}
          <TabsContent value="languages" className="space-y-6">
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold mb-2">Languages You Speak</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Add languages you can speak to help with validation and contributions
                </p>

                <div className="flex gap-2 mb-4">
                  <Select value={newLanguage} onValueChange={setNewLanguage}>
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder="Select a language" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableLanguages
                        .filter(lang => !profileData.languages_spoken.includes(lang.code))
                        .map(lang => (
                          <SelectItem key={lang.code} value={lang.code}>
                            {lang.name} ({lang.native_name})
                          </SelectItem>
                        ))
                      }
                    </SelectContent>
                  </Select>
                  <Button onClick={addLanguage} disabled={!newLanguage}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex flex-wrap gap-2">
                  {profileData.languages_spoken.map(langCode => {
                    const language = availableLanguages.find(l => l.code === langCode);
                    return (
                      <Badge key={langCode} variant="secondary" className="flex items-center gap-1">
                        {language?.name || langCode}
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-4 w-4 p-0 hover:bg-transparent"
                          onClick={() => removeLanguage(langCode)}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </Badge>
                    );
                  })}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Preferences Tab */}
          <TabsContent value="preferences" className="space-y-6">
            <div className="space-y-6">
              {/* Notifications */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Bell className="h-5 w-5" />
                    Notifications
                  </CardTitle>
                  <CardDescription>
                    Choose what notifications you want to receive
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {Object.entries(profileData.preferences.notifications).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium capitalize">
                          {key.replace('_', ' ')}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {key === 'email_updates' && 'Weekly summary emails'}
                          {key === 'submission_status' && 'Updates on your submissions'}
                          {key === 'validation_alerts' && 'New validations to review'}
                          {key === 'community_updates' && 'Community news and updates'}
                        </p>
                      </div>
                      <Switch
                        checked={value}
                        onCheckedChange={(checked) =>
                          handlePreferenceChange('notifications', key, checked)
                        }
                      />
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Accessibility */}
              <Card>
                <CardHeader>
                  <CardTitle>Accessibility</CardTitle>
                  <CardDescription>
                    Customize the interface for your needs
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {Object.entries(profileData.preferences.accessibility).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium capitalize">
                          {key.replace('_', ' ')}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {key === 'high_contrast' && 'Increase contrast for better visibility'}
                          {key === 'reduced_motion' && 'Reduce animations and transitions'}
                          {key === 'large_text' && 'Increase text size throughout the app'}
                        </p>
                      </div>
                      <Switch
                        checked={value}
                        onCheckedChange={(checked) =>
                          handlePreferenceChange('accessibility', key, checked)
                        }
                      />
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Privacy Tab */}
          <TabsContent value="privacy" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lock className="h-5 w-5" />
                  Privacy Settings
                </CardTitle>
                <CardDescription>
                  Control who can see your information and activity
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>Profile Visibility</Label>
                  <Select
                    value={profileData.preferences.privacy.profile_visibility}
                    onValueChange={(value) =>
                      handlePreferenceChange('privacy', 'profile_visibility', value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="public">Public - Anyone can see</SelectItem>
                      <SelectItem value="community">Community - Only community members</SelectItem>
                      <SelectItem value="private">Private - Only you</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {Object.entries(profileData.preferences.privacy)
                  .filter(([key]) => key !== 'profile_visibility')
                  .map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium capitalize">
                          {key.replace('_', ' ')}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {key === 'show_email' && 'Display your email on your profile'}
                          {key === 'show_location' && 'Display your location on your profile'}
                          {key === 'show_activity' && 'Show your recent activity to others'}
                        </p>
                      </div>
                      <Switch
                        checked={value as boolean}
                        onCheckedChange={(checked) =>
                          handlePreferenceChange('privacy', key, checked)
                        }
                      />
                    </div>
                  ))}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ProfileEditModal;