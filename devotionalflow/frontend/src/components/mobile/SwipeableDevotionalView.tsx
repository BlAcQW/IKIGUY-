import { useState } from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

interface SwipeableDevotionalViewProps {
  devotionalId: string;
  prevId?: string;
  nextId?: string;
  children: React.ReactNode;
}

/**
 * SwipeableDevotionalView - Card-deck style navigation between devotionals
 * Swipe left for next, swipe right for previous
 */
export function SwipeableDevotionalView({
  devotionalId,
  prevId,
  nextId,
  children
}: SwipeableDevotionalViewProps) {
  const [direction, setDirection] = useState(0);
  const navigate = useNavigate();

  const swipeThreshold = 50; // Minimum drag distance
  const swipeVelocity = 500; // Minimum velocity for swipe

  const handleDragEnd = (event: any, info: PanInfo) => {
    const { offset, velocity } = info;

    // Determine if swipe was strong enough
    const shouldSwipe =
      Math.abs(velocity.x) > swipeVelocity ||
      Math.abs(offset.x) > swipeThreshold;

    if (shouldSwipe) {
      if (offset.x > 0 && prevId) {
        // Swipe right - go to previous devotional
        setDirection(-1);
        setTimeout(() => navigate(`/devotional/${prevId}`), 100);
      } else if (offset.x < 0 && nextId) {
        // Swipe left - go to next devotional
        setDirection(1);
        setTimeout(() => navigate(`/devotional/${nextId}`), 100);
      }
    }
  };

  const variants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 300 : -300,
      opacity: 0,
      scale: 0.95
    }),
    center: {
      x: 0,
      opacity: 1,
      scale: 1
    },
    exit: (direction: number) => ({
      x: direction < 0 ? 300 : -300,
      opacity: 0,
      scale: 0.95
    })
  };

  return (
    <AnimatePresence custom={direction} mode="wait">
      <motion.div
        key={devotionalId}
        custom={direction}
        variants={variants}
        initial="enter"
        animate="center"
        exit="exit"
        transition={{
          x: { type: 'spring', stiffness: 300, damping: 30 },
          opacity: { duration: 0.2 },
          scale: { duration: 0.2 }
        }}
        drag="x"
        dragConstraints={{ left: 0, right: 0 }}
        dragElastic={0.2}
        onDragEnd={handleDragEnd}
        className="cursor-grab active:cursor-grabbing"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
