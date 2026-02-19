import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import type { PropertyCreate } from "@/lib/types/property";

interface FinancialStepProps {
  formData: Partial<PropertyCreate>;
  updateFormData: (data: Partial<PropertyCreate>) => void;
}

export function FinancialStep({ formData, updateFormData }: FinancialStepProps) {
  const updateFinancial = (field: string, value: any) => {
    updateFormData({
      financial: {
        ...formData.financial,
        [field]: value,
      },
    });
  };

  return (
    <div className="space-y-6 animate-slide-up-fade">
      <Card variant="premium">
        <CardContent className="p-6">
          <div className="space-y-2">
            <Label htmlFor="price_usd" className="text-lg font-semibold">Listing Price (USD) *</Label>
            <Input
              id="price_usd"
              type="number"
              min="0"
              placeholder="500000"
              value={formData.financial?.price_usd || ""}
              onChange={(e) => updateFinancial("price_usd", parseFloat(e.target.value) || 0)}
              className="text-2xl h-14"
            />
          </div>
        </CardContent>
      </Card>

      <div className="space-y-2">
        <Label htmlFor="base_currency">Base Currency</Label>
        <Input
          id="base_currency"
          placeholder="USD"
          value={formData.financial?.base_currency || "USD"}
          onChange={(e) => updateFinancial("base_currency", e.target.value)}
          disabled
        />
      </div>

      <Card variant="elevated">
        <CardContent className="p-6">
          <Label className="text-base font-semibold mb-4 block">Additional Costs (Optional)</Label>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="hoa_fees_monthly">HOA Fees (Monthly)</Label>
              <Input
                id="hoa_fees_monthly"
                type="number"
                min="0"
                placeholder="250"
                value={formData.financial?.hoa_fees_monthly || ""}
                onChange={(e) => updateFinancial("hoa_fees_monthly", e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="property_tax_annual">Property Tax (Annual)</Label>
              <Input
                id="property_tax_annual"
                type="number"
                min="0"
                placeholder="5000"
                value={formData.financial?.property_tax_annual || ""}
                onChange={(e) => updateFinancial("property_tax_annual", e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="insurance_estimate">Insurance (Annual)</Label>
              <Input
                id="insurance_estimate"
                type="number"
                min="0"
                placeholder="1200"
                value={formData.financial?.insurance_estimate || ""}
                onChange={(e) => updateFinancial("insurance_estimate", e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
