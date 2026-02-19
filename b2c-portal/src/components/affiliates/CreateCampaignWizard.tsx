import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { Calendar, TrendingUp, Target, Award, ArrowLeft, Save } from 'lucide-react';
import { affiliateApi } from '@/lib/core-api';

interface CreateCampaignWizardProps {
  onClose: () => void;
  onSuccess: () => void;
}

const CreateCampaignWizard: React.FC<CreateCampaignWizardProps> = ({ onClose, onSuccess }) => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    campaign_code: '',
    start_date: '',
    end_date: '',
    bonus_rate: '',
    target_referrals: '',
    target_sales: '',
    prize: '',
    landing_page_url: '',
    utm_campaign: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleCampaignCodeChange = (value: string) => {
    // Auto-format: uppercase, alphanumeric + hyphens/underscores
    const formatted = value
      .toUpperCase()
      .replace(/[^A-Z0-9_-]/g, '')
      .slice(0, 50);
    handleInputChange('campaign_code', formatted);
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Required fields
    if (!formData.name.trim()) {
      newErrors.name = 'Campaign name is required';
    }

    if (!formData.campaign_code.trim()) {
      newErrors.campaign_code = 'Campaign code is required';
    } else if (formData.campaign_code.length < 3) {
      newErrors.campaign_code = 'Campaign code must be at least 3 characters';
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }

    if (!formData.end_date) {
      newErrors.end_date = 'End date is required';
    } else if (formData.start_date && new Date(formData.end_date) <= new Date(formData.start_date)) {
      newErrors.end_date = 'End date must be after start date';
    }

    if (!formData.bonus_rate) {
      newErrors.bonus_rate = 'Bonus rate is required';
    } else {
      const rate = parseFloat(formData.bonus_rate);
      if (isNaN(rate) || rate <= 0 || rate > 100) {
        newErrors.bonus_rate = 'Bonus rate must be between 0 and 100';
      }
    }

    // Optional numeric fields validation
    if (formData.target_referrals) {
      const value = parseInt(formData.target_referrals);
      if (isNaN(value) || value <= 0) {
        newErrors.target_referrals = 'Must be a positive number';
      }
    }

    if (formData.target_sales) {
      const value = parseFloat(formData.target_sales);
      if (isNaN(value) || value <= 0) {
        newErrors.target_sales = 'Must be a positive number';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      toast({
        title: 'Validation Error',
        description: 'Please fix the errors in the form',
        variant: 'destructive'
      });
      return;
    }

    setIsSubmitting(true);

    try {
      // Convert form data to API format
      const campaignData = {
        name: formData.name,
        description: formData.description || undefined,
        campaign_code: formData.campaign_code,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
        bonus_rate: parseFloat(formData.bonus_rate) / 100, // Convert percentage to decimal
        target_referrals: formData.target_referrals ? parseInt(formData.target_referrals) : undefined,
        target_sales: formData.target_sales ? parseFloat(formData.target_sales) : undefined,
        prize: formData.prize || undefined,
        landing_page_url: formData.landing_page_url || undefined,
        utm_campaign: formData.utm_campaign || undefined
      };

      await affiliateApi.createCampaign(campaignData);

      toast({
        title: 'Campaign Created',
        description: `Campaign "${formData.name}" has been created successfully`,
      });

      onSuccess();
    } catch (error: any) {
      toast({
        title: 'Error Creating Campaign',
        description: error.message || 'Failed to create campaign',
        variant: 'destructive'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={onClose}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h2 className="text-2xl font-bold">Create Referral Campaign</h2>
          <p className="text-muted-foreground">Set up a time-limited promotion with bonus commissions</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Basic Information
            </CardTitle>
            <CardDescription>Campaign name, description, and unique code</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">Campaign Name *</Label>
              <Input
                id="name"
                placeholder="Summer Sale 2024"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className={errors.name ? 'border-red-500' : ''}
              />
              {errors.name && <p className="text-sm text-red-500 mt-1">{errors.name}</p>}
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe your campaign goals and strategy"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                rows={3}
              />
            </div>

            <div>
              <Label htmlFor="campaign_code">Campaign Code *</Label>
              <Input
                id="campaign_code"
                placeholder="SUMMER2024"
                value={formData.campaign_code}
                onChange={(e) => handleCampaignCodeChange(e.target.value)}
                className={errors.campaign_code ? 'border-red-500' : ''}
              />
              <p className="text-sm text-muted-foreground mt-1">
                3-50 characters, uppercase letters, numbers, hyphens, and underscores only
              </p>
              {errors.campaign_code && <p className="text-sm text-red-500 mt-1">{errors.campaign_code}</p>}
            </div>
          </CardContent>
        </Card>

        {/* Time Frame */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Campaign Duration
            </CardTitle>
            <CardDescription>Set the start and end dates for this campaign</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start_date">Start Date *</Label>
                <Input
                  id="start_date"
                  type="datetime-local"
                  value={formData.start_date}
                  onChange={(e) => handleInputChange('start_date', e.target.value)}
                  className={errors.start_date ? 'border-red-500' : ''}
                />
                {errors.start_date && <p className="text-sm text-red-500 mt-1">{errors.start_date}</p>}
              </div>

              <div>
                <Label htmlFor="end_date">End Date *</Label>
                <Input
                  id="end_date"
                  type="datetime-local"
                  value={formData.end_date}
                  onChange={(e) => handleInputChange('end_date', e.target.value)}
                  className={errors.end_date ? 'border-red-500' : ''}
                />
                {errors.end_date && <p className="text-sm text-red-500 mt-1">{errors.end_date}</p>}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Bonus Commission */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Bonus Commission
            </CardTitle>
            <CardDescription>Extra commission percentage on top of regular tier rates</CardDescription>
          </CardHeader>
          <CardContent>
            <div>
              <Label htmlFor="bonus_rate">Bonus Rate (%) *</Label>
              <Input
                id="bonus_rate"
                type="number"
                placeholder="5"
                min="0"
                max="100"
                step="0.1"
                value={formData.bonus_rate}
                onChange={(e) => handleInputChange('bonus_rate', e.target.value)}
                className={errors.bonus_rate ? 'border-red-500' : ''}
              />
              <p className="text-sm text-muted-foreground mt-1">
                This bonus is added on top of your regular tier commission rates
              </p>
              {errors.bonus_rate && <p className="text-sm text-red-500 mt-1">{errors.bonus_rate}</p>}
            </div>
          </CardContent>
        </Card>

        {/* Goals & Prizes */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5" />
              Goals & Prizes (Optional)
            </CardTitle>
            <CardDescription>Set targets and rewards for achieving campaign goals</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="target_referrals">Target Referrals</Label>
                <Input
                  id="target_referrals"
                  type="number"
                  placeholder="50"
                  min="1"
                  value={formData.target_referrals}
                  onChange={(e) => handleInputChange('target_referrals', e.target.value)}
                  className={errors.target_referrals ? 'border-red-500' : ''}
                />
                {errors.target_referrals && <p className="text-sm text-red-500 mt-1">{errors.target_referrals}</p>}
              </div>

              <div>
                <Label htmlFor="target_sales">Target Sales ($)</Label>
                <Input
                  id="target_sales"
                  type="number"
                  placeholder="1000"
                  min="0"
                  step="0.01"
                  value={formData.target_sales}
                  onChange={(e) => handleInputChange('target_sales', e.target.value)}
                  className={errors.target_sales ? 'border-red-500' : ''}
                />
                {errors.target_sales && <p className="text-sm text-red-500 mt-1">{errors.target_sales}</p>}
              </div>
            </div>

            <div>
              <Label htmlFor="prize">Prize / Reward</Label>
              <Input
                id="prize"
                placeholder="$500 bonus, iPad, etc."
                value={formData.prize}
                onChange={(e) => handleInputChange('prize', e.target.value)}
              />
              <p className="text-sm text-muted-foreground mt-1">
                Describe the prize for reaching campaign goals
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Advanced Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Advanced Settings (Optional)</CardTitle>
            <CardDescription>Custom landing page and UTM parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="landing_page_url">Custom Landing Page URL</Label>
              <Input
                id="landing_page_url"
                type="url"
                placeholder="https://example.com/summer-sale"
                value={formData.landing_page_url}
                onChange={(e) => handleInputChange('landing_page_url', e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="utm_campaign">UTM Campaign Parameter</Label>
              <Input
                id="utm_campaign"
                placeholder="summer_sale_2024"
                value={formData.utm_campaign}
                onChange={(e) => handleInputChange('utm_campaign', e.target.value)}
              />
              <p className="text-sm text-muted-foreground mt-1">
                Used for tracking campaign performance in analytics
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting} className="flex-1">
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Creating Campaign...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Create Campaign
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default CreateCampaignWizard;
