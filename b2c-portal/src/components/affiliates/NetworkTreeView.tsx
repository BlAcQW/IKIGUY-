import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { affiliateApi, NetworkStats } from '@/lib/core-api';
import {
  Network,
  Users,
  ChevronDown,
  ChevronRight,
  DollarSign,
  TrendingUp,
  Award
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface NetworkNode {
  id: string;
  user_id: string;
  email?: string;
  referral_code: string;
  tier_level: number;
  total_referrals: number;
  total_commissions_earned: number;
  direct_referrals: number;
  isExpanded?: boolean;
  children?: NetworkNode[];
}

interface NetworkTreeViewProps {
  organizationId?: string;
}

const NetworkTreeView: React.FC<NetworkTreeViewProps> = ({ organizationId }) => {
  const [networkStats, setNetworkStats] = useState<NetworkStats | null>(null);
  const [networkTree, setNetworkTree] = useState<NetworkNode[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  useEffect(() => {
    loadNetworkData();
  }, []);

  const loadNetworkData = async () => {
    setIsLoading(true);
    try {
      const [stats, tree] = await Promise.all([
        affiliateApi.getNetworkStats(),
        affiliateApi.getNetworkTree()
      ]);
      setNetworkStats(stats);
      setNetworkTree(tree as NetworkNode[]);
    } catch (error) {
      console.error('Failed to load network data:', error);
      toast({
        title: 'Error loading network',
        description: error instanceof Error ? error.message : 'Please try again',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const buildMockTree = (stats: NetworkStats): NetworkNode[] => {
    // This is a simplified mock. In production, the backend should return tree structure
    const tree: NetworkNode[] = [];

    // Create nodes based on network stats
    if (stats.tier1_count > 0) {
      for (let i = 0; i < Math.min(stats.tier1_count, 5); i++) {
        tree.push({
          id: `tier1_${i}`,
          user_id: `user_tier1_${i}`,
          email: `user${i}@example.com`,
          referral_code: `REF${i}`,
          tier_level: 1,
          total_referrals: Math.floor(Math.random() * 10),
          total_commissions_earned: Math.random() * 1000,
          direct_referrals: Math.floor(Math.random() * 5),
          children: []
        });
      }
    }

    return tree;
  };

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getTierColor = (tier: number) => {
    const colors: Record<number, string> = {
      1: 'bg-green-600',
      2: 'bg-blue-600',
      3: 'bg-purple-600'
    };
    return colors[tier] || 'bg-gray-600';
  };

  const getTierLabel = (tier: number) => {
    const labels: Record<number, string> = {
      1: 'Direct',
      2: 'Tier 2',
      3: 'Tier 3'
    };
    return labels[tier] || `Tier ${tier}`;
  };

  const renderNode = (node: NetworkNode, depth: number = 0) => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children && node.children.length > 0;

    return (
      <div key={node.id} className="mb-2">
        <div
          className={`flex items-center gap-3 p-3 rounded-lg border transition-all hover:bg-gray-50 ${
            depth > 0 ? 'ml-' + (depth * 6) : ''
          }`}
          style={{ marginLeft: `${depth * 24}px` }}
        >
          {/* Expand/Collapse Button */}
          {hasChildren ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleNode(node.id)}
              className="h-6 w-6 p-0"
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          ) : (
            <div className="h-6 w-6" />
          )}

          {/* User Avatar */}
          <div className={`h-10 w-10 rounded-full ${getTierColor(node.tier_level)} flex items-center justify-center text-white font-bold`}>
            {node.email?.charAt(0).toUpperCase() || 'U'}
          </div>

          {/* User Info */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-sm">{node.email || 'Unknown User'}</span>
              <Badge className={`${getTierColor(node.tier_level)} text-white text-xs`}>
                {getTierLabel(node.tier_level)}
              </Badge>
            </div>
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Users className="h-3 w-3" />
                {node.direct_referrals} referrals
              </span>
              <span className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                {formatCurrency(node.total_commissions_earned)}
              </span>
            </div>
          </div>

          {/* Referral Code */}
          <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
            {node.referral_code}
          </code>
        </div>

        {/* Render Children */}
        {isExpanded && hasChildren && (
          <div className="mt-1">
            {node.children!.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Network Stats Summary */}
      {networkStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Network</p>
                  <p className="text-2xl font-bold">{networkStats.total_network_size}</p>
                </div>
                <Network className="h-8 w-8 text-blue-600 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Tier 1</p>
                  <p className="text-2xl font-bold text-green-600">{networkStats.tier1_count}</p>
                </div>
                <Award className="h-8 w-8 text-green-600 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Tier 2</p>
                  <p className="text-2xl font-bold text-blue-600">{networkStats.tier2_count}</p>
                </div>
                <Award className="h-8 w-8 text-blue-600 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Tier 3</p>
                  <p className="text-2xl font-bold text-purple-600">{networkStats.tier3_count}</p>
                </div>
                <Award className="h-8 w-8 text-purple-600 opacity-20" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Network Tree */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Network className="h-5 w-5 text-blue-600" />
                Your Network Tree
              </CardTitle>
              <CardDescription>
                Visualize your multi-level marketing network structure
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadNetworkData}
              disabled={isLoading}
            >
              {isLoading ? 'Loading...' : 'Refresh'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
              ))}
            </div>
          ) : networkTree.length === 0 ? (
            <div className="text-center py-12">
              <Network className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No network yet</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Start building your network by sharing your referral link
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {networkTree.map(node => renderNode(node))}

              {networkStats && networkStats.total_network_size > 5 && (
                <div className="text-center py-4">
                  <p className="text-sm text-muted-foreground">
                    Showing top 5 direct referrals. You have {networkStats.total_network_size} total members in your network.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Legend */}
          {networkTree.length > 0 && (
            <div className="mt-6 pt-6 border-t">
              <h4 className="font-semibold text-sm mb-3">Commission Structure</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-green-600" />
                  <span className="text-sm">
                    <strong>Tier 1 (Direct):</strong> 15% commission
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-blue-600" />
                  <span className="text-sm">
                    <strong>Tier 2:</strong> 8% commission
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-purple-600" />
                  <span className="text-sm">
                    <strong>Tier 3:</strong> 3% commission
                  </span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Network Performance */}
      {networkStats && networkStats.total_network_size > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Network Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Total Network Sales</span>
                <span className="text-lg font-bold text-green-600">
                  {formatCurrency(networkStats.total_sales)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Total Commissions Earned</span>
                <span className="text-lg font-bold text-blue-600">
                  {formatCurrency(networkStats.total_commissions)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Average Commission per Member</span>
                <span className="text-lg font-bold text-purple-600">
                  {formatCurrency(networkStats.total_commissions / networkStats.total_network_size)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default NetworkTreeView;
