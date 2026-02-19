/**
 * MongoDB Authentication Signup Form
 * Replaces Supabase-based signup with MongoDB backend authentication
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Eye, EyeOff, Gift } from 'lucide-react';
import { useMongoAuth } from './MongoAuthContext';
import { MongoSignupRequest } from '@/lib/mongo-auth';
import { getReferralCode, attributeSignup, clearReferralData } from '@/lib/referral-tracking';
import { PostSignupAffiliatePrompt } from '@/components/affiliates/PostSignupAffiliatePrompt';

interface SignupFormData {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  organizationName: string;
  referralCode: string;
}

export const MongoSignupForm: React.FC = () => {
  const { signUp, isLoading } = useMongoAuth();
  const [formData, setFormData] = useState<SignupFormData>({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    organizationName: '',
    referralCode: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<Partial<SignupFormData>>({});
  const [hasReferralFromCookie, setHasReferralFromCookie] = useState(false);
  const [showAffiliatePrompt, setShowAffiliatePrompt] = useState(false);
  const [newUserId, setNewUserId] = useState<string | null>(null);
  const [newOrganizationId, setNewOrganizationId] = useState<string | null>(null);

  // Auto-populate referral code from cookie on mount
  useEffect(() => {
    const cookieReferralCode = getReferralCode();
    if (cookieReferralCode) {
      setFormData(prev => ({ ...prev, referralCode: cookieReferralCode }));
      setHasReferralFromCookie(true);
    }
  }, []);

  const validateForm = (): boolean => {
    const newErrors: Partial<SignupFormData> = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.firstName) {
      newErrors.firstName = 'First name is required';
    }

    if (!formData.lastName) {
      newErrors.lastName = 'Last name is required';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one uppercase letter, lowercase letter, and number';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      const signupData: MongoSignupRequest = {
        email: formData.email,
        password: formData.password,
        first_name: formData.firstName,
        last_name: formData.lastName,
        organization_name: formData.organizationName || undefined,
      };

      const response = await signUp(signupData);

      // After successful signup, attribute to referral if present
      if (response && formData.referralCode) {
        console.log('[Signup] Attributing signup to referral:', formData.referralCode);

        // Wait a moment for user/org creation to complete
        await new Promise(resolve => setTimeout(resolve, 1000));

        try {
          const attributed = await attributeSignup(
            response.user.id,
            response.user.organization_id,
          );

          if (attributed) {
            console.log('[Signup] Successfully attributed to referral');
            // Don't clear referral data yet - we'll use it for affiliate join prompt
          }
        } catch (error) {
          console.error('[Signup] Failed to attribute referral:', error);
          // Don't fail signup if attribution fails
        }
      }

      // Show affiliate join prompt after successful signup
      if (response && response.user) {
        setNewUserId(response.user.id);
        setNewOrganizationId(response.user.organization_id);
        // Small delay to let the user see the success message
        setTimeout(() => {
          setShowAffiliatePrompt(true);
        }, 1500);
      }
    } catch (error) {
      console.error('Signup error:', error);
      // Error handling is done in the MongoAuthContext with toast notifications
    }
  };

  const handleInputChange = (field: keyof SignupFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = e.target.value;
    setFormData({ ...formData, [field]: value });

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors({ ...errors, [field]: undefined });
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name</Label>
              <Input
                id="firstName"
                type="text"
                value={formData.firstName}
                onChange={handleInputChange('firstName')}
                placeholder="First name"
                className={errors.firstName ? 'border-red-500' : ''}
                disabled={isLoading}
                autoComplete="given-name"
              />
              {errors.firstName && (
                <div className="flex items-center text-sm text-red-600">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  {errors.firstName}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name</Label>
              <Input
                id="lastName"
                type="text"
                value={formData.lastName}
                onChange={handleInputChange('lastName')}
                placeholder="Last name"
                className={errors.lastName ? 'border-red-500' : ''}
                disabled={isLoading}
                autoComplete="family-name"
              />
              {errors.lastName && (
                <div className="flex items-center text-sm text-red-600">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  {errors.lastName}
                </div>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={handleInputChange('email')}
              placeholder="Enter your email"
              className={errors.email ? 'border-red-500' : ''}
              disabled={isLoading}
              autoComplete="email"
            />
            {errors.email && (
              <div className="flex items-center text-sm text-red-600">
                <AlertCircle className="w-4 h-4 mr-1" />
                {errors.email}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="organizationName">Organization Name (Optional)</Label>
            <Input
              id="organizationName"
              type="text"
              value={formData.organizationName}
              onChange={handleInputChange('organizationName')}
              placeholder="Your organization"
              disabled={isLoading}
              autoComplete="organization"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="referralCode">
                Referral Code (Optional)
              </Label>
              {hasReferralFromCookie && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <Gift className="h-3 w-3" />
                  Auto-filled
                </Badge>
              )}
            </div>
            <Input
              id="referralCode"
              type="text"
              value={formData.referralCode}
              onChange={handleInputChange('referralCode')}
              placeholder="Enter referral code"
              disabled={isLoading || hasReferralFromCookie}
              readOnly={hasReferralFromCookie}
              className="uppercase font-mono"
            />
            {hasReferralFromCookie ? (
              <Alert className="mt-2">
                <Gift className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  We detected a referral code from the link you clicked. 
                  This will credit the person who referred you when you sign up.
                </AlertDescription>
              </Alert>
            ) : (
              <p className="text-xs text-muted-foreground">
                Have a referral code? Enter it to give credit to who referred you.
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleInputChange('password')}
                placeholder="Create a password"
                className={errors.password ? 'border-red-500 pr-10' : 'pr-10'}
                disabled={isLoading}
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                disabled={isLoading}
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
            {errors.password && (
              <div className="flex items-center text-sm text-red-600">
                <AlertCircle className="w-4 h-4 mr-1" />
                {errors.password}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <div className="relative">
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                value={formData.confirmPassword}
                onChange={handleInputChange('confirmPassword')}
                placeholder="Confirm your password"
                className={errors.confirmPassword ? 'border-red-500 pr-10' : 'pr-10'}
                disabled={isLoading}
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                disabled={isLoading}
              >
                {showConfirmPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
            {errors.confirmPassword && (
              <div className="flex items-center text-sm text-red-600">
                <AlertCircle className="w-4 h-4 mr-1" />
                {errors.confirmPassword}
              </div>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? 'Creating account...' : 'Create account'}
          </Button>
        </form>

      {/* Post-Signup Affiliate Join Prompt */}
      {newUserId && newOrganizationId && (
        <PostSignupAffiliatePrompt
          open={showAffiliatePrompt}
          onOpenChange={(open) => {
            setShowAffiliatePrompt(open);
            // Clear referral data when prompt is dismissed or user joins
            if (!open) {
              clearReferralData();
            }
          }}
          userId={newUserId}
          organizationId={newOrganizationId}
        />
      )}
    </>
  );
};