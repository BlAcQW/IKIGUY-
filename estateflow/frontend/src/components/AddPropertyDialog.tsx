import { useState } from "react";
import { Check, ChevronLeft, ChevronRight, Home, MapPin, Settings, DollarSign, ImageIcon } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useCreateProperty } from "@/hooks/use-properties";
import type { PropertyCreate } from "@/lib/types/property";
import { PropertyType, PropertyStatus } from "@/lib/types/property";
import { BasicInfoStep } from "./wizard-steps/BasicInfoStep";
import { LocationStep } from "./wizard-steps/LocationStep";
import { FeaturesStep } from "./wizard-steps/FeaturesStep";
import { FinancialStep } from "./wizard-steps/FinancialStep";
import { MediaStep } from "./wizard-steps/MediaStep";

interface AddPropertyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const steps = [
  { id: 0, label: "Basic Info", icon: Home },
  { id: 1, label: "Location", icon: MapPin },
  { id: 2, label: "Features", icon: Settings },
  { id: 3, label: "Financial", icon: DollarSign },
  { id: 4, label: "Media", icon: ImageIcon },
];

export function AddPropertyDialog(props: AddPropertyDialogProps) {
  const { open, onOpenChange } = props;
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<Partial<PropertyCreate>>({
    property_type: PropertyType.HOUSE,
    status: PropertyStatus.ACTIVE,
    location: { country: "Ghana" },
    features: {},
    financial: {},
  });

  const createMutation = useCreateProperty({
    onSuccess: () => {
      onOpenChange(false);
      resetForm();
    },
  });

  const resetForm = () => {
    setCurrentStep(0);
    setFormData({
      property_type: PropertyType.HOUSE,
      status: PropertyStatus.ACTIVE,
      location: { country: "Ghana" },
      features: {},
      financial: {},
    });
  };

  const updateFormData = (data: Partial<PropertyCreate>) => {
    setFormData((prev) => ({ ...prev, ...data }));
  };

  const handleSubmit = () => {
    createMutation.mutate(formData as PropertyCreate);
  };

  const isLastStep = currentStep === steps.length - 1;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">Add New Property</DialogTitle>
        </DialogHeader>

        <div className="flex items-center justify-between mb-8 px-4">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div className={"flex items-center justify-center w-12 h-12 rounded-full transition-all duration-200 " + (currentStep === index ? "bg-primary text-white shadow-premium scale-110" : currentStep > index ? "bg-success text-white" : "bg-muted text-muted-foreground")}>
                  {currentStep > index ? <Check className="h-6 w-6" /> : <step.icon className="h-6 w-6" />}
                </div>
                <span className={"mt-2 text-xs font-medium " + (currentStep === index ? "text-foreground" : "text-muted-foreground")}>
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div className={"flex-1 h-1 mx-2 transition-colors duration-200 rounded " + (currentStep > index ? "bg-success" : "bg-muted")} />
              )}
            </div>
          ))}
        </div>

        <div className="min-h-[400px] px-4 py-6">
          {currentStep === 0 && <BasicInfoStep formData={formData} updateFormData={updateFormData} />}
          {currentStep === 1 && <LocationStep formData={formData} updateFormData={updateFormData} />}
          {currentStep === 2 && <FeaturesStep formData={formData} updateFormData={updateFormData} />}
          {currentStep === 3 && <FinancialStep formData={formData} updateFormData={updateFormData} />}
          {currentStep === 4 && <MediaStep formData={formData} updateFormData={updateFormData} />}
        </div>

        <div className="flex items-center justify-between pt-6 border-t px-4">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
            className="gap-2"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>

          <div className="text-sm text-muted-foreground">
            Step {currentStep + 1} of {steps.length}
          </div>

          {isLastStep ? (
            <Button
              onClick={handleSubmit}
              disabled={createMutation.isPending}
              variant="gradient"
              className="gap-2"
            >
              {createMutation.isPending ? "Creating..." : "Create Property"}
            </Button>
          ) : (
            <Button
              onClick={() => setCurrentStep(Math.min(steps.length - 1, currentStep + 1))}
              variant="default"
              className="gap-2"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
