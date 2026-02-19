import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { Calendar, Clock, User, Building, Mail, Phone, AlertCircle } from 'lucide-react';

const ScheduleDemo = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Validation functions
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePhone = (phone: string): boolean => {
    // Allow various phone formats: +1234567890, 123-456-7890, (123) 456-7890, 123.456.7890, etc.
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$|^[\+]?[1-9][\d\s\-\(\)\.]{7,}$/;
    return phone === '' || phoneRegex.test(phone.replace(/[\s\-\(\)\.]/g, ''));
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Required field validation
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.preferredDate) {
      newErrors.preferredDate = 'Preferred date is required';
    }

    if (!formData.preferredTime) {
      newErrors.preferredTime = 'Preferred time is required';
    }

    // Optional field validation
    if (formData.phone && !validatePhone(formData.phone)) {
      newErrors.phone = 'Please enter a valid phone number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  const [formData, setFormData] = useState({
    fullName: '',
    companyName: '',
    email: user?.email || '',
    phone: '',
    preferredDate: '',
    preferredTime: '',
    timezone: 'UTC',
    demoType: 'general',
    notes: ''
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form before submission
    if (!validateForm()) {
      toast({
        title: "Validation Error",
        description: "Please fix the errors in the form before submitting.",
        variant: "destructive",
      });
      return;
    }
    
    setIsLoading(true);

    try {
      const bookingData = {
        user_id: user?.id || null, // Allow null for unauthenticated users
        full_name: formData.fullName,
        company_name: formData.companyName,
        email: formData.email,
        phone: formData.phone,
        preferred_date: formData.preferredDate,
        preferred_time: formData.preferredTime,
        timezone: formData.timezone,
        demo_type: formData.demoType,
        notes: formData.notes
      };

      const { error } = await supabase
        .from('demo_bookings')
        .insert([bookingData]);

      if (error) throw error;

      // Send email notification
      try {
        const { error: emailError } = await supabase.functions.invoke('send-demo-notification', {
          body: formData
        });
        
        if (emailError) {
          console.error('Email notification error:', emailError);
        }
      } catch (emailError) {
        console.error('Failed to send email notification:', emailError);
      }

      toast({
        title: "Demo scheduled!",
        description: "We'll contact you soon to confirm your demo appointment. Confirmation email sent!",
      });

      // Reset form
      setFormData({
        fullName: '',
        companyName: '',
        email: user?.email || '',
        phone: '',
        preferredDate: '',
        preferredTime: '',
        timezone: 'UTC',
        demoType: 'general',
        notes: ''
      });
    } catch (error: any) {
      console.error('Error scheduling demo:', error);
      toast({
        title: "Error scheduling demo",
        description: error.message || "Please try again later.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted py-12">
      <div className="container mx-auto px-4 max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-tech-blue to-tech-blue-light bg-clip-text text-transparent">
            Schedule a Demo
          </h1>
          <p className="text-muted-foreground mt-2">
            Book a personalized demonstration of our AI assistant platform
          </p>
        </div>

        <Card className="shadow-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Demo Booking
            </CardTitle>
            <CardDescription>
              Fill out the form below and we'll schedule a demo that fits your needs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="fullName" className="flex items-center gap-2">
                    <User className="h-4 w-4" />
                    Full Name *
                  </Label>
                  <Input
                    id="fullName"
                    value={formData.fullName}
                    onChange={(e) => handleInputChange('fullName', e.target.value)}
                    placeholder="Enter your full name"
                    className={errors.fullName ? 'border-red-500' : ''}
                  />
                  {errors.fullName && (
                    <div className="flex items-center gap-1 text-sm text-red-500">
                      <AlertCircle className="h-3 w-3" />
                      {errors.fullName}
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="companyName" className="flex items-center gap-2">
                    <Building className="h-4 w-4" />
                    Company Name
                  </Label>
                  <Input
                    id="companyName"
                    value={formData.companyName}
                    onChange={(e) => handleInputChange('companyName', e.target.value)}
                    placeholder="Enter your company name"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="email" className="flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    Email Address *
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    placeholder="Enter your email"
                    className={errors.email ? 'border-red-500' : ''}
                  />
                  {errors.email && (
                    <div className="flex items-center gap-1 text-sm text-red-500">
                      <AlertCircle className="h-3 w-3" />
                      {errors.email}
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone" className="flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    Phone Number
                  </Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    placeholder="+1234567890 or (123) 456-7890"
                    className={errors.phone ? 'border-red-500' : ''}
                  />
                  {errors.phone && (
                    <div className="flex items-center gap-1 text-sm text-red-500">
                      <AlertCircle className="h-3 w-3" />
                      {errors.phone}
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="preferredDate" className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    Preferred Date *
                  </Label>
                  <Input
                    id="preferredDate"
                    type="date"
                    value={formData.preferredDate}
                    onChange={(e) => handleInputChange('preferredDate', e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    className={errors.preferredDate ? 'border-red-500' : ''}
                  />
                  {errors.preferredDate && (
                    <div className="flex items-center gap-1 text-sm text-red-500">
                      <AlertCircle className="h-3 w-3" />
                      {errors.preferredDate}
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select value={formData.timezone} onValueChange={(value) => handleInputChange('timezone', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="UTC">UTC (Coordinated Universal Time)</SelectItem>
                      <SelectItem value="GMT+1">GMT+1 (West Africa Time - WAT)</SelectItem>
                      <SelectItem value="GMT+2">GMT+2 (Central Africa Time - CAT)</SelectItem>
                      <SelectItem value="GMT+3">GMT+3 (East Africa Time - EAT)</SelectItem>
                      <SelectItem value="GMT+0">GMT+0 (Greenwich Mean Time)</SelectItem>
                      <SelectItem value="GMT-5">GMT-5 (Eastern Time - ET)</SelectItem>
                      <SelectItem value="GMT-8">GMT-8 (Pacific Time - PT)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Preferred Time *
                </Label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {[
                    '09:00', '10:00', '11:00', '12:00',
                    '13:00', '14:00', '15:00', '16:00',
                    '17:00', '18:00', '19:00', '20:00'
                  ].map((time) => (
                    <Button
                      key={time}
                      type="button"
                      variant={formData.preferredTime === time ? "default" : "outline"}
                      onClick={() => handleInputChange('preferredTime', time)}
                      className="text-sm"
                    >
                      {time}
                    </Button>
                  ))}
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-sm text-muted-foreground">Or enter custom time:</span>
                  <Input
                    type="time"
                    value={formData.preferredTime}
                    onChange={(e) => handleInputChange('preferredTime', e.target.value)}
                    className="w-32"
                  />
                </div>
                {errors.preferredTime && (
                  <div className="flex items-center gap-1 text-sm text-red-500">
                    <AlertCircle className="h-3 w-3" />
                    {errors.preferredTime}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="demoType">Demo Type</Label>
                <Select value={formData.demoType} onValueChange={(value) => handleInputChange('demoType', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General Overview</SelectItem>
                    <SelectItem value="banking">Banking & Finance</SelectItem>
                    <SelectItem value="insurance">Insurance</SelectItem>
                    <SelectItem value="healthcare">Healthcare</SelectItem>
                    <SelectItem value="retail">Retail & E-commerce</SelectItem>
                    <SelectItem value="real-estate">Real Estate</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Additional Notes</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  placeholder="Tell us about your specific requirements or questions..."
                  rows={4}
                />
              </div>

              <Button 
                type="submit" 
                className="w-full" 
                disabled={isLoading}
              >
                {isLoading ? "Scheduling..." : "Schedule Demo"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ScheduleDemo;