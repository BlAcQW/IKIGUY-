/**
 * Tool Call Log Detail Modal Component
 *
 * Displays comprehensive details about a single tool call log entry.
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  CheckCircle,
  XCircle,
  Clock,
  Target,
  AlertTriangle,
  Database,
  FileText,
  Zap,
  MapPin,
  TrendingUp,
  Activity,
} from 'lucide-react';
import { ToolCallLog } from '@/services/ToolCallLogsService';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

interface ToolCallLogDetailModalProps {
  log: ToolCallLog;
  open: boolean;
  onClose: () => void;
}

export const ToolCallLogDetailModal: React.FC<ToolCallLogDetailModalProps> = ({
  log,
  open,
  onClose,
}) => {
  // Helper functions
  const formatMs = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getStatusIcon = () => {
    switch (log.status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
      case 'error':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'timeout':
        return <Clock className="h-5 w-5 text-orange-600" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.8) return 'High';
    if (score >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getStatusIcon()}
            Tool Call Details
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Status Overview */}
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Status</p>
                  <Badge
                    variant={log.status === 'success' ? 'default' : 'destructive'}
                    className="capitalize"
                  >
                    {log.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Processing Time</p>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-gray-600" />
                    <span className="font-medium">{formatMs(log.processing_time)}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Confidence</p>
                  <div className="flex items-center gap-2">
                    <Target className={cn('h-4 w-4', getConfidenceColor(log.confidence_score))} />
                    <span className={cn('font-medium', getConfidenceColor(log.confidence_score))}>
                      {(log.confidence_score * 100).toFixed(1)}% ({getConfidenceLabel(log.confidence_score)})
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Cached</p>
                  <Badge variant={log.is_cached ? 'secondary' : 'outline'}>
                    {log.is_cached ? (
                      <>
                        <Zap className="h-3 w-3 mr-1" />
                        Yes
                      </>
                    ) : (
                      'No'
                    )}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Query Information */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Query Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Original Query</p>
                  <div className="bg-muted p-3 rounded-md text-sm">
                    {log.query_original}
                  </div>
                </div>

                {log.query_normalized && log.query_normalized !== log.query_original && (
                  <div>
                    <p className="text-xs text-gray-600 mb-1">Normalized Query</p>
                    <div className="bg-muted p-3 rounded-md text-sm">
                      {log.query_normalized}
                    </div>
                  </div>
                )}

                {log.city_normalization && (
                  <div>
                    <p className="text-xs text-gray-600 mb-1 flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      City Normalization
                    </p>
                    <div className="bg-muted p-3 rounded-md text-sm space-y-1">
                      <div className="grid grid-cols-2 gap-2">
                        <span className="text-gray-600">Original:</span>
                        <span className="font-medium">{log.city_normalization.original}</span>
                        <span className="text-gray-600">Normalized:</span>
                        <span className="font-medium">{log.city_normalization.normalized}</span>
                        <span className="text-gray-600">Confidence:</span>
                        <span>{(log.city_normalization.confidence * 100).toFixed(1)}%</span>
                        <span className="text-gray-600">Method:</span>
                        <span className="text-xs">{log.city_normalization.method}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-2 text-sm pt-2 border-t">
                  <span className="text-gray-600">Tool Call ID:</span>
                  <span className="font-mono text-xs">{log.tool_call_id}</span>

                  <span className="text-gray-600">Company:</span>
                  <span className="text-xs">{log.company_name}</span>

                  {log.vapi_call_id && (
                    <>
                      <span className="text-gray-600">VAPI Call ID:</span>
                      <span className="font-mono text-xs">{log.vapi_call_id}</span>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Performance Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-gray-600 mb-1">Total Time</p>
                    <p className="font-medium">{formatMs(log.processing_time)}</p>
                  </div>

                  {log.retrieval_time !== undefined && (
                    <div>
                      <p className="text-xs text-gray-600 mb-1">Retrieval Time</p>
                      <p className="font-medium">{formatMs(log.retrieval_time)}</p>
                    </div>
                  )}

                  {log.llm_time !== undefined && (
                    <div>
                      <p className="text-xs text-gray-600 mb-1">LLM Time</p>
                      <p className="font-medium">{formatMs(log.llm_time)}</p>
                    </div>
                  )}

                  <div>
                    <p className="text-xs text-gray-600 mb-1">Documents Retrieved</p>
                    <p className="font-medium">{log.documents_retrieved}</p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-600 mb-1">Docs Sent to LLM</p>
                    <p className="font-medium">{log.documents_sent_to_llm}</p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-600 mb-1">Response Length</p>
                    <p className="font-medium">{log.response_length} chars</p>
                  </div>
                </div>

                {(log.retrieval_time !== undefined && log.llm_time !== undefined) && (
                  <div className="pt-3 border-t">
                    <p className="text-xs text-gray-600 mb-2">Time Breakdown</p>
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span>Retrieval</span>
                          <span>{((log.retrieval_time / log.processing_time) * 100).toFixed(1)}%</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500"
                            style={{ width: `${(log.retrieval_time / log.processing_time) * 100}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span>LLM Processing</span>
                          <span>{((log.llm_time / log.processing_time) * 100).toFixed(1)}%</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-purple-500"
                            style={{ width: `${(log.llm_time / log.processing_time) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="pt-3 border-t text-xs text-gray-600">
                  {format(new Date(log.created_at), 'PPpp')}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Response */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Response</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-muted p-4 rounded-md text-sm max-h-60 overflow-y-auto whitespace-pre-wrap">
                {log.response}
              </div>
            </CardContent>
          </Card>

          {/* Sources Used */}
          {log.sources_used.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  Sources Used ({log.sources_used.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {log.sources_used.map((source, index) => (
                    <div
                      key={index}
                      className="bg-muted p-3 rounded-md text-sm"
                    >
                      <div className="flex items-start gap-2">
                        <Badge variant="secondary" className="text-xs">
                          {index + 1}
                        </Badge>
                        <span className="flex-1">{source}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Escalation Information */}
          {log.requires_escalation && (
            <Card className="border-orange-200 bg-orange-50">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2 text-orange-700">
                  <AlertTriangle className="h-4 w-4" />
                  Escalation Required
                </CardTitle>
              </CardHeader>
              <CardContent>
                {log.escalation_reason ? (
                  <div className="text-sm text-orange-800">
                    <p className="font-medium mb-1">Reason:</p>
                    <p>{log.escalation_reason}</p>
                  </div>
                ) : (
                  <p className="text-sm text-orange-800">
                    This query requires human review or escalation to support.
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Error Information */}
          {log.error_message && (
            <Card className="border-red-200 bg-red-50">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2 text-red-700">
                  <XCircle className="h-4 w-4" />
                  Error Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-red-100 p-3 rounded-md text-sm text-red-800 font-mono">
                  {log.error_message}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Metadata */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Additional Metadata</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {log.ip_address && (
                  <>
                    <span className="text-gray-600">IP Address:</span>
                    <span className="font-mono text-xs">{log.ip_address}</span>
                  </>
                )}

                {log.user_agent && (
                  <>
                    <span className="text-gray-600">User Agent:</span>
                    <span className="text-xs truncate" title={log.user_agent}>
                      {log.user_agent}
                    </span>
                  </>
                )}

                {log.cache_key && (
                  <>
                    <span className="text-gray-600">Cache Key:</span>
                    <span className="font-mono text-xs truncate" title={log.cache_key}>
                      {log.cache_key}
                    </span>
                  </>
                )}

                <span className="text-gray-600">Log ID:</span>
                <span className="font-mono text-xs">{log.id}</span>

                <span className="text-gray-600">Created:</span>
                <span className="text-xs">{format(new Date(log.created_at), 'PPpp')}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Footer Actions */}
        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ToolCallLogDetailModal;
