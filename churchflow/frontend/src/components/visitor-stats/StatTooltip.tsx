/**
 * Stat Tooltip Component
 *
 * Contextual information tooltip that appears on card hover.
 * Uses Framer Motion for smooth enter/exit animations.
 */

import { motion, AnimatePresence } from 'framer-motion';

interface StatTooltipProps {
  isVisible: boolean;
  content: string;
}

export default function StatTooltip({ isVisible, content }: StatTooltipProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          transition={{ duration: 0.2, delay: 0.3 }}
          className="absolute -top-14 left-1/2 transform -translate-x-1/2 z-50"
        >
          <div className="relative bg-gray-900/95 backdrop-blur-sm text-white text-xs px-3 py-2 rounded-lg shadow-xl max-w-[200px] text-center">
            {content}
            {/* Arrow pointer */}
            <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900/95 rotate-45"></div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
