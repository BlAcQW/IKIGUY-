import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  ArrowLeft,
  ThumbsUp,
  ThumbsDown,
  Clock,
  CheckCircle,
  XCircle,
  Calendar,
  User,
  Share2,
  Loader2,
  TrendingUp,
  Users
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useBackendAuth } from '@/contexts/BackendAuthContext';
import { useToast } from '@/hooks/use-toast';

const ProposalDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useBackendAuth();
  const { toast } = useToast();

  const [proposal, setProposal] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [voting, setVoting] = useState(false);
  const [userVote, setUserVote] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadProposal();
    }
  }, [id]);

  const loadProposal = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getProposalDetails(id!);
      setProposal(data);
      setUserVote(data.user_vote || null);
    } catch (error) {
      console.error('Failed to load proposal:', error);
      toast({
        title: 'Load Failed',
        description: 'Failed to load proposal details',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (vote: 'support' | 'oppose') => {
    if (!user) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to vote on proposals',
        variant: 'destructive'
      });
      return;
    }

    if (userVote) {
      toast({
        title: 'Already Voted',
        description: 'You have already voted on this proposal',
        variant: 'destructive'
      });
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to ${vote === 'support' ? 'support' : 'oppose'} this proposal? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      setVoting(true);
      await apiClient.voteOnProposal(id!, { vote });

      toast({
        title: 'Vote Recorded',
        description: `Your ${vote === 'support' ? 'support' : 'opposition'} has been recorded`
      });

      // Reload proposal to get updated vote counts
      await loadProposal();
    } catch (error) {
      console.error('Failed to vote:', error);
      toast({
        title: 'Vote Failed',
        description: error instanceof Error ? error.message : 'Failed to record your vote',
        variant: 'destructive'
      });
    } finally {
      setVoting(false);
    }
  };

  const handleShare = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url);
    toast({
      title: 'Link Copied',
      description: 'Proposal link copied to clipboard'
    });
  };

  const getStatusBadge = (status: string) => {
    const statusLower = (status || 'active').toLowerCase();

    if (statusLower === 'active' || statusLower === 'pending') {
      return (
        <Badge className="bg-blue-100 text-blue-800 text-base px-3 py-1">
          <Clock className="h-4 w-4 mr-1" />
          Active
        </Badge>
      );
    }
    if (statusLower === 'passed' || statusLower === 'approved') {
      return (
        <Badge className="bg-green-100 text-green-800 text-base px-3 py-1">
          <CheckCircle className="h-4 w-4 mr-1" />
          Passed
        </Badge>
      );
    }
    if (statusLower === 'rejected' || statusLower === 'failed') {
      return (
        <Badge className="bg-red-100 text-red-800 text-base px-3 py-1">
          <XCircle className="h-4 w-4 mr-1" />
          Rejected
        </Badge>
      );
    }
    return <Badge variant="outline" className="text-base px-3 py-1">{status}</Badge>;
  };

  const getCategoryBadge = (category: string) => {
    const label = category?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Other';
    return <Badge variant="secondary" className="text-base px-3 py-1">{label}</Badge>;
  };

  const getTimeRemaining = (expiresAt: string) => {
    if (!expiresAt) return null;

    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();

    if (diffMs < 0) return 'Expired';

    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

    if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} remaining`;
    if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? 's' : ''} remaining`;
    return 'Ending soon';
  };

  const getVotePercentage = () => {
    if (!proposal) return 0;
    const totalVotes = (proposal.votes_for || 0) + (proposal.votes_against || 0);
    if (totalVotes === 0) return 0;
    return Math.round(((proposal.votes_for || 0) / totalVotes) * 100);
  };

  const renderDescription = (text: string) => {
    return text.split('\n\n').map((para, i) => (
      <p key={i} className="mb-4 last:mb-0">
        {para}
      </p>
    ));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Header />
        <main className="flex-1 container mx-auto px-4 py-8 flex items-center justify-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </main>
        <Footer />
      </div>
    );
  }

  if (!proposal) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Header />
        <main className="flex-1 container mx-auto px-4 py-8">
          <Card>
            <CardContent className="py-16 text-center">
              <XCircle className="h-16 w-16 mx-auto mb-4 text-red-500" />
              <h3 className="text-lg font-medium mb-2">Proposal Not Found</h3>
              <p className="text-muted-foreground mb-4">
                The proposal you're looking for doesn't exist or has been removed
              </p>
              <Button onClick={() => navigate('/proposals')}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Proposals
              </Button>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </div>
    );
  }

  const isActive = proposal.status?.toLowerCase() === 'active' || proposal.status?.toLowerCase() === 'pending';
  const canVote = user && isActive && !userVote;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        {/* Back Button */}
        <Button variant="ghost" onClick={() => navigate('/proposals')} className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Proposals
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Proposal Header */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      {getStatusBadge(proposal.status)}
                      {getCategoryBadge(proposal.category)}
                    </div>
                    <CardTitle className="text-3xl mb-3">{proposal.title}</CardTitle>
                  </div>
                  <Button variant="outline" size="icon" onClick={handleShare}>
                    <Share2 className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    {proposal.author_name || proposal.created_by || 'Anonymous'}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {new Date(proposal.created_at).toLocaleDateString()}
                  </span>
                  {proposal.expires_at && isActive && (
                    <span className="flex items-center gap-1 text-orange-600 font-medium">
                      <Clock className="h-4 w-4" />
                      {getTimeRemaining(proposal.expires_at)}
                    </span>
                  )}
                </div>
              </CardHeader>

              <CardContent>
                <div className="prose prose-sm max-w-none">
                  {renderDescription(proposal.description)}
                </div>
              </CardContent>
            </Card>

            {/* Voting Buttons */}
            {isActive && (
              <Card>
                <CardHeader>
                  <CardTitle>Cast Your Vote</CardTitle>
                  <CardDescription>
                    {userVote
                      ? `You voted to ${userVote === 'support' ? 'support' : 'oppose'} this proposal`
                      : 'Help the community decide on this proposal'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4">
                    <Button
                      onClick={() => handleVote('support')}
                      disabled={!canVote || voting}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                      size="lg"
                    >
                      {voting ? (
                        <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      ) : (
                        <ThumbsUp className="h-5 w-5 mr-2" />
                      )}
                      Support
                    </Button>
                    <Button
                      onClick={() => handleVote('oppose')}
                      disabled={!canVote || voting}
                      className="flex-1 bg-red-600 hover:bg-red-700"
                      size="lg"
                    >
                      {voting ? (
                        <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      ) : (
                        <ThumbsDown className="h-5 w-5 mr-2" />
                      )}
                      Oppose
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Vote Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Vote Breakdown</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="font-medium">Support</span>
                    <span className="text-green-600 font-bold">{getVotePercentage()}%</span>
                  </div>
                  <Progress value={getVotePercentage()} className="h-3" />
                </div>

                <Separator />

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm">
                      <ThumbsUp className="h-4 w-4 text-green-600" />
                      Support
                    </span>
                    <span className="font-bold text-green-600">{proposal.votes_for || 0}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm">
                      <ThumbsDown className="h-4 w-4 text-red-600" />
                      Oppose
                    </span>
                    <span className="font-bold text-red-600">{proposal.votes_against || 0}</span>
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm font-medium">
                      <Users className="h-4 w-4" />
                      Total Votes
                    </span>
                    <span className="font-bold">
                      {(proposal.votes_for || 0) + (proposal.votes_against || 0)}
                    </span>
                  </div>
                </div>

                {proposal.quorum_required && (
                  <>
                    <Separator />
                    <div className="text-xs text-muted-foreground">
                      Quorum: {proposal.quorum_percentage || 10}% of active members required
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Proposal Info */}
            <Card>
              <CardHeader>
                <CardTitle>Proposal Info</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <div className="mt-1">{getStatusBadge(proposal.status)}</div>
                </div>

                <div>
                  <span className="text-muted-foreground">Category:</span>
                  <div className="mt-1">{getCategoryBadge(proposal.category)}</div>
                </div>

                <Separator />

                <div>
                  <span className="text-muted-foreground">Created:</span>
                  <div className="font-medium mt-1">
                    {new Date(proposal.created_at).toLocaleString()}
                  </div>
                </div>

                {proposal.expires_at && (
                  <div>
                    <span className="text-muted-foreground">
                      {isActive ? 'Expires:' : 'Expired:'}
                    </span>
                    <div className="font-medium mt-1">
                      {new Date(proposal.expires_at).toLocaleString()}
                    </div>
                  </div>
                )}

                {proposal.decided_at && (
                  <div>
                    <span className="text-muted-foreground">Decided:</span>
                    <div className="font-medium mt-1">
                      {new Date(proposal.decided_at).toLocaleString()}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default ProposalDetail;
