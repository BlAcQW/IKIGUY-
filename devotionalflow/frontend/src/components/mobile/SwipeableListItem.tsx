import { useState, useRef, useEffect } from 'react';
import { motion, PanInfo } from 'framer-motion';
import { Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SwipeableListItemProps {
  /**
   * The content to display in the list item.
   */
  children: React.ReactNode;
  
  /**
   * Callback when delete button is clicked.
   */
  onDelete: () => void;
  
  /**
   * Optional callback when item is clicked (for navigation).
   */
  onClick?: () => void;
  
  /**
   * Whether the item is disabled.
   */
  disabled?: boolean;
  
  /**
   * Additional CSS classes for the container.
   */
  className?: string;
}

/**
 * SwipeableListItem - Mobile swipe-to-reveal delete button component
 * 
 * On mobile devices, users can swipe left to reveal a delete button.
 * On desktop, the delete button is always visible or can be accessed via hover.
 * 
 * Args:
 *   children: The content to display in the list item.
 *   onDelete: Callback when delete button is clicked.
 *   onClick: Optional callback when item is clicked (for navigation).
 *   disabled: Whether the item is disabled.
 *   className: Additional CSS classes for the container.
 */
export function SwipeableListItem({
  children,
  onDelete,
  onClick,
  disabled = false,
  className = '',
}: SwipeableListItemProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const deleteButtonWidth = 80; // Width of delete button in pixels

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('touchstart', handleClickOutside);
      };
    }
  }, [isOpen]);

  const handleDragEnd = (event: any, info: PanInfo) => {
    const { offset, velocity } = info;
    const threshold = deleteButtonWidth * 0.5; // 50% of button width
    
    // Determine if swipe was strong enough to reveal/hide delete button
    if (Math.abs(velocity.x) > 500 || Math.abs(offset.x) > threshold) {
      if (offset.x < 0) {
        // Swipe left - reveal delete button
        setIsOpen(true);
      } else {
        // Swipe right - hide delete button
        setIsOpen(false);
      }
    } else {
      // Snap back to current state
      setIsOpen(false);
    }
    setIsDragging(false);
  };

  const handleDrag = () => {
    if (!isDragging) {
      setIsDragging(true);
    }
  };

  const handleItemClick = () => {
    // Only trigger onClick if not dragging and delete button is not open
    if (!isDragging && !isOpen && onClick) {
      onClick();
    }
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(false);
    onDelete();
  };

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden ${className}`}
    >
      {/* Delete Button - Revealed on swipe */}
      <motion.div
        className="absolute right-0 top-0 bottom-0 flex items-center justify-center bg-destructive z-10"
        initial={{ width: 0 }}
        animate={{ width: isOpen ? deleteButtonWidth : 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
      >
        <Button
          variant="destructive"
          size="icon"
          onClick={handleDeleteClick}
          className="h-full w-full rounded-none"
          disabled={disabled}
        >
          <Trash2 className="w-5 h-5" />
        </Button>
      </motion.div>

      {/* Main Content - Swipeable */}
      <motion.div
        drag="x"
        dragConstraints={{ left: -deleteButtonWidth, right: 0 }}
        dragElastic={0.1}
        onDrag={handleDrag}
        onDragEnd={handleDragEnd}
        animate={{
          x: isOpen ? -deleteButtonWidth : 0,
        }}
        transition={{
          type: 'spring',
          stiffness: 300,
          damping: 30,
        }}
        onClick={handleItemClick}
        className={`cursor-pointer ${disabled ? 'opacity-50' : ''}`}
        style={{
          touchAction: 'pan-x pan-y',
        }}
      >
        {children}
      </motion.div>
    </div>
  );
}

