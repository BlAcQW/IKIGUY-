import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Shield, AlertTriangle, Heart, DollarSign, ShoppingCart } from 'lucide-react';

interface IndustryConfigHandlerProps {
  industry: string;
  config: any;
  onConfigChange: (updates: any) => void;
}

export const IndustryConfigHandler: React.FC<IndustryConfigHandlerProps> = ({
  industry,
  config,
  onConfigChange
}) => {
  const handleChange = (field: string, value: any) => {
    onConfigChange({
      [field]: value
    });
  };

  const getIndustryIcon = (industry: string) => {
    switch (industry.toLowerCase()) {
      case 'healthcare':
        return <Heart className="h-5 w-5 text-red-500" />;
      case 'finance':
        return <DollarSign className="h-5 w-5 text-green-500" />;
      case 'retail':
        return <ShoppingCart className="h-5 w-5 text-blue-500" />;
      default:
        return <Shield className="h-5 w-5 text-gray-500" />;
    }
  };

  const renderHealthcareConfig = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="h-4 w-4 text-amber-500" />
        <span className="text-sm font-medium text-amber-700">HIPAA Compliance Required</span>
        <Badge variant="outline" className="text-xs">Healthcare</Badge>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="hipaa-enabled">HIPAA Compliance</Label>
          <div className="flex items-center space-x-2 mt-1">
            <Switch
              id="hipaa-enabled"
              checked={config.hipaaCompliant || false}
              onCheckedChange={(checked) => handleChange('hipaaCompliant', checked)}
            />
            <span className="text-sm">Enable HIPAA compliance mode</span>
          </div>
        </div>

        <div>
          <Label htmlFor="patient-data">Patient Data Handling</Label>
          <div className="flex items-center space-x-2 mt-1">
            <Switch
              id="patient-data"
              checked={config.patientDataEnabled || false}
              onCheckedChange={(checked) => handleChange('patientDataEnabled', checked)}
            />
            <span className="text-sm">Handle patient information</span>
          </div>
        </div>
      </div>

      <div>
        <Label htmlFor="provider-types">Healthcare Provider Types</Label>
        <Input
          id="provider-types"
          placeholder="e.g., General Practice, Cardiology, Pediatrics"
          value={config.providerTypes || ''}
          onChange={(e) => handleChange('providerTypes', e.target.value)}
          className="mt-1"
        />
      </div>

      <div>
        <Label htmlFor="emergency-protocols">Emergency Protocols</Label>
        <Textarea
          id="emergency-protocols"
          placeholder="Define emergency escalation procedures..."
          value={config.emergencyProtocols || ''}
          onChange={(e) => handleChange('emergencyProtocols', e.target.value)}
          className="mt-1"
          rows={3}
        />
      </div>
    </div>
  );

  const renderFinanceConfig = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="h-4 w-4 text-amber-500" />
        <span className="text-sm font-medium text-amber-700">PCI DSS Compliance Required</span>
        <Badge variant="outline" className="text-xs">Finance</Badge>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="pci-compliance">PCI DSS Compliance</Label>
          <div className="flex items-center space-x-2 mt-1">
            <Switch
              id="pci-compliance"
              checked={config.pciCompliant || false}
              onCheckedChange={(checked) => handleChange('pciCompliant', checked)}
            />
            <span className="text-sm">Enable PCI DSS compliance</span>
          </div>
        </div>

        <div>
          <Label htmlFor="fraud-detection">Fraud Detection</Label>
          <div className="flex items-center space-x-2 mt-1">
            <Switch
              id="fraud-detection"
              checked={config.fraudDetectionEnabled || false}
              onCheckedChange={(checked) => handleChange('fraudDetectionEnabled', checked)}
            />
            <span className="text-sm">Enable fraud detection</span>
          </div>
        </div>
      </div>

      <div>
        <Label htmlFor="transaction-limits">Transaction Limits</Label>
        <Input
          id="transaction-limits"
          type="number"
          placeholder="Maximum transaction amount"
          value={config.transactionLimit || ''}
          onChange={(e) => handleChange('transactionLimit', parseFloat(e.target.value))}
          className="mt-1"
        />
      </div>

      <div>
        <Label htmlFor="kyc-requirements">KYC Requirements</Label>
        <Textarea
          id="kyc-requirements"
          placeholder="Define Know Your Customer requirements..."
          value={config.kycRequirements || ''}
          onChange={(e) => handleChange('kycRequirements', e.target.value)}
          className="mt-1"
          rows={3}
        />
      </div>
    </div>
  );

  const renderRetailConfig = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <ShoppingCart className="h-4 w-4 text-blue-500" />
        <span className="text-sm font-medium text-blue-700">E-commerce Configuration</span>
        <Badge variant="outline" className="text-xs">Retail</Badge>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="inventory-tracking">Inventory Tracking</Label>
          <div className="flex items-center space-x-2 mt-1">
            <Switch
              id="inventory-tracking"
              checked={config.inventoryTracking || false}
              onCheckedChange={(checked) => handleChange('inventoryTracking', checked)}
            />
            <span className="text-sm">Track inventory levels</span>
          </div>
        </div>

        <div>
          <Label htmlFor="order-management">Order Management</Label>
          <div className="flex items-center space-x-2 mt-1">
            <Switch
              id="order-management"
              checked={config.orderManagement || false}
              onCheckedChange={(checked) => handleChange('orderManagement', checked)}
            />
            <span className="text-sm">Handle order processing</span>
          </div>
        </div>
      </div>

      <div>
        <Label htmlFor="product-categories">Product Categories</Label>
        <Input
          id="product-categories"
          placeholder="e.g., Electronics, Clothing, Books"
          value={config.productCategories || ''}
          onChange={(e) => handleChange('productCategories', e.target.value)}
          className="mt-1"
        />
      </div>

      <div>
        <Label htmlFor="return-policy">Return Policy</Label>
        <Textarea
          id="return-policy"
          placeholder="Define return and refund policies..."
          value={config.returnPolicy || ''}
          onChange={(e) => handleChange('returnPolicy', e.target.value)}
          className="mt-1"
          rows={3}
        />
      </div>
    </div>
  );

  const renderGenericConfig = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Shield className="h-4 w-4 text-gray-500" />
        <span className="text-sm font-medium text-gray-700">General Configuration</span>
        <Badge variant="outline" className="text-xs">Generic</Badge>
      </div>

      <div>
        <Label htmlFor="business-hours">Business Hours</Label>
        <Input
          id="business-hours"
          placeholder="e.g., Monday-Friday 9AM-5PM"
          value={config.businessHours || ''}
          onChange={(e) => handleChange('businessHours', e.target.value)}
          className="mt-1"
        />
      </div>

      <div>
        <Label htmlFor="contact-info">Contact Information</Label>
        <Textarea
          id="contact-info"
          placeholder="Primary contact details for escalations..."
          value={config.contactInfo || ''}
          onChange={(e) => handleChange('contactInfo', e.target.value)}
          className="mt-1"
          rows={3}
        />
      </div>

      <div>
        <Label htmlFor="custom-fields">Custom Fields</Label>
        <Textarea
          id="custom-fields"
          placeholder="Additional industry-specific configurations..."
          value={config.customFields || ''}
          onChange={(e) => handleChange('customFields', e.target.value)}
          className="mt-1"
          rows={3}
        />
      </div>
    </div>
  );

  const renderConfigByIndustry = () => {
    switch (industry?.toLowerCase()) {
      case 'healthcare':
        return renderHealthcareConfig();
      case 'finance':
        return renderFinanceConfig();
      case 'retail':
        return renderRetailConfig();
      default:
        return renderGenericConfig();
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {getIndustryIcon(industry)}
          {industry} Configuration
        </CardTitle>
        <CardDescription>
          Industry-specific settings and compliance requirements
        </CardDescription>
      </CardHeader>
      <CardContent>
        {renderConfigByIndustry()}
      </CardContent>
    </Card>
  );
};

export default IndustryConfigHandler;