/**
 * Announcement Card Component
 * 
 * Displays an announcement card on the landing page with image, title, description, and CTA.
 */

import { Link } from 'react-router-dom';
import { ArrowRight, ExternalLink } from 'lucide-react';

interface AnnouncementCardProps {
  announcement: {
    id: string;
    title: string;
    description?: string;
    image_url?: string;
    cta_text?: string;
    cta_link?: string;
    event_id?: string;
  };
}

import { normalizeAnnouncementImageUrl } from '../utils/imageUrl';

export default function AnnouncementCard({ announcement }: AnnouncementCardProps) {
  const imageUrl = normalizeAnnouncementImageUrl(announcement.image_url);
  const isExternalLink = announcement.cta_link?.startsWith('http://') || announcement.cta_link?.startsWith('https://');
  const linkComponent = announcement.cta_link ? (
    isExternalLink ? (
      <a
        href={announcement.cta_link}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all shadow-lg hover:shadow-xl"
      >
        {announcement.cta_text || 'Learn More'}
        <ExternalLink className="w-4 h-4" />
      </a>
    ) : (
      <Link
        to={announcement.cta_link}
        className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all shadow-lg hover:shadow-xl"
      >
        {announcement.cta_text || 'Learn More'}
        <ArrowRight className="w-4 h-4" />
      </Link>
    )
  ) : null;

  return (
    <div className="card card-hover overflow-hidden group">
      {/* Image */}
      {imageUrl && (
        <div className="relative h-48 overflow-hidden -m-6 mb-4">
          <img
            src={imageUrl}
            alt={announcement.title}
            loading="lazy"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        </div>
      )}
      
      {/* Content */}
      <div className="pt-2">
        <h3 className="font-bold text-gray-900 mb-2 line-clamp-2 text-lg">
          {announcement.title}
        </h3>
        
        {announcement.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-3">
            {announcement.description}
          </p>
        )}

        {/* CTA Button */}
        {linkComponent && (
          <div className="pt-4 border-t border-gray-100">
            {linkComponent}
          </div>
        )}
      </div>
    </div>
  );
}

