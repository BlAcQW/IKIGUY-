/**
 * Template Card Component
 * Displays automation template with edit/delete menu
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  MoreVertical,
  Edit,
  Trash2,
  Play,
  Settings,
  Users,
  Clock,
  Shield,
  ExternalLink,
} from 'lucide-react';
import { AutomationTemplate } from '../../services/TemplateManagementService';
import { useToast } from '@/hooks/use-toast';

interface TemplateCardProps {
  template: AutomationTemplate;
  onEdit?: (template: AutomationTemplate) => void;
  onDelete?: (templateId: string) => void;
  onDeploy?: (template: AutomationTemplate) => void;
  onSelect?: (template: AutomationTemplate) => void;
  showActions?: boolean;
  mode?: 'management' | 'selection';
}

const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  onEdit,
  onDelete,
  onDeploy,
  onSelect,
  showActions = true,
  mode = 'management',
}) => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const { toast } = useToast();

  const handleDelete = () => {
    if (onDelete) {
      onDelete(template.id);
      setShowDeleteDialog(false);
      toast({
        title: "Template deleted",
        description: `${template.template_name} has been deleted successfully.`,
      });
    }
  };

  const handleDeploy = () => {
    if (onDeploy) {
      onDeploy(template);
      toast({
        title: "Deployment started",
        description: `${template.template_name} is being deployed...`,
      });
    }
  };

  const getIndustryColor = (industry: string) => {
    const colors: Record<string, string> = {
      Healthcare: "bg-blue-100 text-blue-800",
      Insurance: "bg-green-100 text-green-800",
      Retail: "bg-purple-100 text-purple-800",
      Finance: "bg-yellow-100 text-yellow-800",
      Education: "bg-indigo-100 text-indigo-800",
      "Real Estate": "bg-orange-100 text-orange-800",
      Generic: "bg-gray-100 text-gray-800",
    };
    return colors[industry] || "bg-gray-100 text-gray-800";
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'helpdesk': return '🎧';
      case 'sales': return '💼';
      case 'provider_locator': return '🏥';
      case 'appointment_booking': return '📅';
      case 'claims_processing': return '📋';
      case 'customer_service': return '🤝';
      case 'retention': return '🔄';
      case 'lead_generation': return '🎯';
      default: return '⚙️';
    }
  };

  return (
    <>
      <Card className="group hover:shadow-lg transition-all duration-200 border-l-4 border-l-blue-500">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{getCategoryIcon(template.category || 'general')}</span>
                <CardTitle className="text-lg font-semibold line-clamp-2">
                  {template.template_name}
                </CardTitle>
                {!template.is_active && (
                  <Badge variant="secondary" className="text-xs">
                    Inactive
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Badge className={getIndustryColor(template.industry)}>
                  {template.industry}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {(template.category || 'general').replace('_', ' ')}
                </Badge>
              </div>
            </div>

            {showActions && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem onClick={handleDeploy}>
                    <Play className="h-4 w-4 mr-2" />
                    Deploy Template
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onEdit && onEdit(template)}>
                    <Edit className="h-4 w-4 mr-2" />
                    Edit Template
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Settings className="h-4 w-4 mr-2" />
                    Configure
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View Demo
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => setShowDeleteDialog(true)}
                    className="text-red-600 focus:text-red-600"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Template
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>

          <CardDescription className="text-sm text-gray-600 line-clamp-2">
            {template.description}
          </CardDescription>
        </CardHeader>

        <CardContent className="pt-0">
          <div className="space-y-3">
            {/* Company Info */}
            <div className="text-sm">
              <span className="font-medium text-gray-700">Company:</span>
              <span className="ml-2 text-gray-600">{template.company_name}</span>
            </div>

            {/* Key Metrics */}
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <Users className="h-3 w-3" />
                <span>{template.usage_count} uses</span>
              </div>
              <div className="flex items-center gap-1">
                <Settings className="h-3 w-3" />
                <span>{template.custom_tool_names.length} tools</span>
              </div>
              <div className="flex items-center gap-1">
                <ExternalLink className="h-3 w-3" />
                <span>{template.integrations.length} integrations</span>
              </div>
            </div>

            {/* Compliance & Features */}
            <div className="flex items-center gap-2 flex-wrap">
              {template.vapi_config.compliance_level !== 'Standard' && (
                <Badge variant="outline" className="text-xs flex items-center gap-1">
                  <Shield className="h-3 w-3" />
                  {template.vapi_config.compliance_level}
                </Badge>
              )}
              {template.demo_config.emergency_simulation && (
                <Badge variant="outline" className="text-xs text-red-600">
                  Emergency Ready
                </Badge>
              )}
              {template.monitoring_config.compliance_monitoring && (
                <Badge variant="outline" className="text-xs text-green-600">
                  Monitored
                </Badge>
              )}
            </div>

            {/* Last Updated */}
            <div className="text-xs text-gray-400 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>
                Updated {new Date(template.updated_at).toLocaleDateString()}
              </span>
            </div>

            {/* Selection Mode Button */}
            {mode === 'selection' && onSelect && (
              <div className="pt-3 border-t">
                <Button
                  onClick={() => onSelect(template)}
                  className="w-full gap-2"
                  size="sm"
                >
                  <Play className="h-3 w-3" />
                  Select Template
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Template</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{template.template_name}"? This action cannot be undone.
              All deployments using this template will continue to work, but you won't be able to create new ones.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete Template
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default TemplateCard;