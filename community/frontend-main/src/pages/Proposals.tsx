import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { CreateProposalModal } from '@/components/CreateProposalModal';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import {
  PlusCircle,
  Search,
  ThumbsUp,
  ThumbsDown,
  Clock,
  CheckCircle,
  XCircle,
  FileText,
  Loader2,
  Calendar,
  User,
  TrendingUp
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useBackendAuth } from '@/contexts/BackendAuthContext';

const Proposals = () => {
  const navigate = useNavigate();
  const { user } = useBackendAuth();

  const [proposals, setProposals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentTab, setCurrentTab] = useState('active');
  const [searchQuery, setSearchQuery] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadProposals();
  }, [currentTab, page]);

  const loadProposals = async () => {
    try {
      setLoading(true);
      const statusFilter = currentTab === 'all' ? undefined : currentTab;
      const data = await apiClient.getCommunityProposals(statusFilter, page, 20);

      const proposalsList = Array.isArray(data) ? data : (data?.items || []);
      setProposals(proposalsList);
      setTotalCount(data?.total_count || proposalsList.length);
    } catch (error) {
      console.error('Failed to load proposals:', error);
      setProposals([]);
    } finally {
      setLoading(false);
    }
  };

  const handleProposalCreated = () => {
    setCreateModalOpen(false);
    loadProposals(); // Refresh list
  };

  const getStatusBadge = (status: string) => {
    const statusLower = (status || 'active').toLowerCase();

    if (statusLower === 'active' || statusLower === 'pending') {
      return (
        <Badge className="bg-blue-100 text-blue-800">
          <Clock className="h-3 w-3 mr-1" />
          Active
        </Badge>
      );
    }
    if (statusLower === 'passed' || statusLower === 'approved') {
      return (
        <Badge className="bg-green-100 text-green-800">
          <CheckCircle className="h-3 w-3 mr-1" />
          Passed
        </Badge>
      );
    }
    if (statusLower === 'rejected' || statusLower === 'failed') {
      return (
        <Badge className="bg-red-100 text-red-800">
          <XCircle className="h-3 w-3 mr-1" />
          Rejected
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="text-gray-600">
        {status}
      </Badge>
    );
  };

  const getCategoryBadge = (category: string) => {
    const colors = {
      'language_addition': 'bg-purple-100 text-purple-800',
      'policy_change': 'bg-orange-100 text-orange-800',
      'feature_request': 'bg-blue-100 text-blue-800',
      'resource_allocation': 'bg-green-100 text-green-800',
      'other': 'bg-gray-100 text-gray-800'
    };

    const color = colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-800';
    const label = category?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Other';

    return <Badge className={color}>{label}</Badge>;
  };

  const getTimeRemaining = (expiresAt: string) => {
    if (!expiresAt) return null;

    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();

    if (diffMs < 0) return 'Expired';

    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

    if (diffDays > 0) return `${diffDays}d remaining`;
    if (diffHours > 0) return `${diffHours}h remaining`;
    return 'Ending soon';
  };

  const getVotePercentage = (proposal: any) => {
    const totalVotes = (proposal.votes_for || 0) + (proposal.votes_against || 0);
    if (totalVotes === 0) return 0;
    return Math.round(((proposal.votes_for || 0) / totalVotes) * 100);
  };

  const filteredProposals = proposals.filter(proposal =>
    searchQuery === '' ||
    proposal.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    proposal.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold mb-2">Community Proposals</h1>
              <p className="text-lg text-muted-foreground">
                Shape the future of the platform through community governance
              </p>
            </div>
            {user && (
              <Button onClick={() => setCreateModalOpen(true)} size="lg">
                <PlusCircle className="h-5 w-5 mr-2" />
                Create Proposal
              </Button>
            )}
          </div>

          {/* Search Bar */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search proposals..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={currentTab} onValueChange={setCurrentTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 max-w-2xl">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="active">Active</TabsTrigger>
            <TabsTrigger value="passed">Passed</TabsTrigger>
            <TabsTrigger value="rejected">Rejected</TabsTrigger>
          </TabsList>

          <TabsContent value={currentTab} className="space-y-4">
            {loading ? (
              <div className="flex justify-center py-16">
                <Loader2 className="h-12 w-12 animate-spin text-primary" />
              </div>
            ) : filteredProposals.length > 0 ? (
              <div className="space-y-4">
                {filteredProposals.map((proposal) => (
                  <Card
                    key={proposal.id}
                    className="hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => navigate(`/proposals/${proposal.id}`)}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <CardTitle className="text-xl">{proposal.title}</CardTitle>
                            {getStatusBadge(proposal.status)}
                          </div>
                          <CardDescription className="line-clamp-2">
                            {proposal.description}
                          </CardDescription>
                        </div>
                        {getCategoryBadge(proposal.category)}
                      </div>
                    </CardHeader>

                    <CardContent>
                      <div className="space-y-4">
                        {/* Vote Progress */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-4">
                              <span className="flex items-center gap-1 text-green-600">
                                <ThumbsUp className="h-4 w-4" />
                                {proposal.votes_for || 0}
                              </span>
                              <span className="flex items-center gap-1 text-red-600">
                                <ThumbsDown className="h-4 w-4" />
                                {proposal.votes_against || 0}
                              </span>
                            </div>
                            <span className="font-medium">{getVotePercentage(proposal)}% support</span>
                          </div>
                          <Progress value={getVotePercentage(proposal)} className="h-2" />
                        </div>

                        {/* Metadata */}
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <User className="h-4 w-4" />
                            {proposal.author_name || proposal.created_by || 'Anonymous'}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            {new Date(proposal.created_at).toLocaleDateString()}
                          </span>
                          {proposal.expires_at && proposal.status === 'active' && (
                            <span className="flex items-center gap-1 text-orange-600">
                              <Clock className="h-4 w-4" />
                              {getTimeRemaining(proposal.expires_at)}
                            </span>
                          )}
                          {proposal.total_votes !== undefined && (
                            <span className="flex items-center gap-1">
                              <TrendingUp className="h-4 w-4" />
                              {proposal.total_votes} votes
                            </span>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="py-16 text-center">
                  <FileText className="h-16 w-16 mx-auto mb-4 opacity-30 text-muted-foreground" />
                  <h3 className="text-lg font-medium mb-2">
                    {searchQuery ? 'No proposals found' : 'No proposals yet'}
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    {searchQuery
                      ? 'Try adjusting your search terms'
                      : 'Be the first to create a proposal for the community'}
                  </p>
                  {!searchQuery && user && (
                    <Button onClick={() => setCreateModalOpen(true)}>
                      <PlusCircle className="h-4 w-4 mr-2" />
                      Create First Proposal
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Pagination */}
            {!loading && filteredProposals.length > 0 && totalCount > 20 && (
              <div className="flex justify-center gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * 20 >= totalCount}
                >
                  Next
                </Button>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>

      <Footer />

      {/* Create Proposal Modal */}
      {user && (
        <CreateProposalModal
          open={createModalOpen}
          onOpenChange={setCreateModalOpen}
          onSuccess={handleProposalCreated}
        />
      )}
    </div>
  );
};

export default Proposals;
