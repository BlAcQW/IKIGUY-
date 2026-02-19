import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  Download,
  Eye,
  ThumbsUp,
  ThumbsDown,
  Star,
  Calendar,
  User,
  FileText,
  Tag
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface NotebookCardProps {
  notebook: {
    id: string;
    title: string;
    description: string;
    category: string;
    difficulty: string;
    language_codes: string[];
    tags: string[];
    author_name: string;
    current_version: string;
    file_size: number;
    upvotes: number;
    downvotes: number;
    rating: number;
    usage_stats: {
      downloads: number;
      views: number;
    };
    created_at: string;
    updated_at: string;
    user_vote?: 'upvote' | 'downvote';
    is_bookmarked?: boolean;
    is_owner?: boolean;
  };
  onView?: (id: string) => void;
  onDownload?: (id: string) => void;
  onVote?: (id: string, voteType: 'upvote' | 'downvote') => void;
}

const categoryColors = {
  data_acquisition: 'bg-blue-100 text-blue-800',
  data_processing: 'bg-green-100 text-green-800',
  asr_training: 'bg-purple-100 text-purple-800',
  tts_training: 'bg-pink-100 text-pink-800',
  llm_training: 'bg-orange-100 text-orange-800',
  evaluation: 'bg-yellow-100 text-yellow-800',
  deployment: 'bg-red-100 text-red-800',
  research: 'bg-indigo-100 text-indigo-800',
  tutorial: 'bg-teal-100 text-teal-800',
  other: 'bg-gray-100 text-gray-800'
};

const difficultyColors = {
  beginner: 'bg-green-100 text-green-800',
  intermediate: 'bg-yellow-100 text-yellow-800',
  advanced: 'bg-orange-100 text-orange-800',
  expert: 'bg-red-100 text-red-800'
};

export const NotebookCard: React.FC<NotebookCardProps> = ({
  notebook,
  onView,
  onDownload,
  onVote
}) => {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const renderStars = (rating: number) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;

    for (let i = 0; i < fullStars; i++) {
      stars.push(<Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />);
    }

    if (hasHalfStar) {
      stars.push(<Star key="half" className="w-4 h-4 fill-yellow-200 text-yellow-400" />);
    }

    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(<Star key={`empty-${i}`} className="w-4 h-4 text-gray-300" />);
    }

    return stars;
  };

  return (
    <Card className="h-full transition-all duration-200 hover:shadow-lg hover:scale-[1.02]">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold line-clamp-2 mb-2">
              {notebook.title}
            </CardTitle>
            <p className="text-sm text-gray-600 line-clamp-3 mb-3">
              {notebook.description}
            </p>
          </div>
        </div>

        {/* Category and Difficulty Badges */}
        <div className="flex flex-wrap gap-2 mb-3">
          <Badge
            className={categoryColors[notebook.category as keyof typeof categoryColors] || categoryColors.other}
            variant="secondary"
          >
            {notebook.category.replace('_', ' ')}
          </Badge>
          <Badge
            className={difficultyColors[notebook.difficulty as keyof typeof difficultyColors]}
            variant="secondary"
          >
            {notebook.difficulty}
          </Badge>
        </div>

        {/* Language Codes */}
        {notebook.language_codes.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {notebook.language_codes.slice(0, 3).map((code) => (
              <Badge key={code} variant="outline" className="text-xs">
                {code.toUpperCase()}
              </Badge>
            ))}
            {notebook.language_codes.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{notebook.language_codes.length - 3}
              </Badge>
            )}
          </div>
        )}

        {/* Tags */}
        {notebook.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {notebook.tags.slice(0, 4).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                <Tag className="w-3 h-3 mr-1" />
                {tag}
              </Badge>
            ))}
            {notebook.tags.length > 4 && (
              <Badge variant="outline" className="text-xs">
                +{notebook.tags.length - 4}
              </Badge>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className="pb-3">
        {/* Author and Version Info */}
        <div className="flex items-center gap-3 mb-3">
          <div className="flex items-center gap-2">
            <Avatar className="w-6 h-6">
              <AvatarFallback className="text-xs">
                {notebook.author_name.split(' ').map(n => n[0]).join('').toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <span className="text-sm text-gray-600">{notebook.author_name}</span>
          </div>
          <Badge variant="outline" className="text-xs">
            v{notebook.current_version}
          </Badge>
        </div>

        {/* Stats Row */}
        <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <Eye className="w-4 h-4" />
              {notebook.usage_stats.views}
            </div>
            <div className="flex items-center gap-1">
              <Download className="w-4 h-4" />
              {notebook.usage_stats.downloads}
            </div>
            <div className="flex items-center gap-1">
              <FileText className="w-4 h-4" />
              {formatFileSize(notebook.file_size)}
            </div>
          </div>
        </div>

        {/* Rating and Votes */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              {renderStars(notebook.rating)}
            </div>
            <span className="text-sm text-gray-600">
              ({notebook.rating.toFixed(1)})
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant={notebook.user_vote === 'upvote' ? 'default' : 'outline'}
              size="sm"
              className="h-8 px-2"
              onClick={() => onVote?.(notebook.id, 'upvote')}
            >
              <ThumbsUp className="w-4 h-4 mr-1" />
              {notebook.upvotes}
            </Button>
            <Button
              variant={notebook.user_vote === 'downvote' ? 'destructive' : 'outline'}
              size="sm"
              className="h-8 px-2"
              onClick={() => onVote?.(notebook.id, 'downvote')}
            >
              <ThumbsDown className="w-4 h-4 mr-1" />
              {notebook.downvotes}
            </Button>
          </div>
        </div>

        {/* Date */}
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Calendar className="w-3 h-3" />
          Updated {formatDistanceToNow(new Date(notebook.updated_at), { addSuffix: true })}
        </div>
      </CardContent>

      <CardFooter className="pt-3">
        <div className="flex gap-2 w-full">
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => onView?.(notebook.id)}
          >
            <Eye className="w-4 h-4 mr-2" />
            View
          </Button>
          <Button
            variant="default"
            className="flex-1"
            onClick={() => onDownload?.(notebook.id)}
          >
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};