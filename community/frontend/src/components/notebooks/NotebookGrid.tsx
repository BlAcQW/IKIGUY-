import React from 'react';
import { NotebookCard } from './NotebookCard';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface NotebookGridProps {
  notebooks: any[];
  loading?: boolean;
  pagination?: {
    page: number;
    total_pages: number;
    total: number;
  };
  onPageChange?: (page: number) => void;
  onView?: (id: string) => void;
  onDownload?: (id: string) => void;
  onVote?: (id: string, voteType: 'upvote' | 'downvote') => void;
}

export const NotebookGrid: React.FC<NotebookGridProps> = ({
  notebooks,
  loading = false,
  pagination,
  onPageChange,
  onView,
  onDownload,
  onVote
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, index) => (
          <div key={index} className="h-96 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (notebooks.length === 0) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">No notebooks found</h3>
        <p className="text-gray-500">Try adjusting your search criteria or filters.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {notebooks.map((notebook) => (
          <NotebookCard
            key={notebook.id}
            notebook={notebook}
            onView={onView}
            onDownload={onDownload}
            onVote={onVote}
          />
        ))}
      </div>

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing page {pagination.page} of {pagination.total_pages} ({pagination.total} total notebooks)
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(pagination.page - 1)}
              disabled={pagination.page <= 1}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(pagination.page + 1)}
              disabled={pagination.page >= pagination.total_pages}
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};