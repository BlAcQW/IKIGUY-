import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function PWAUpdateNotification() {
  const [showUpdate, setShowUpdate] = useState(false);
  const [updateSW, setUpdateSW] = useState<((reloadPage?: boolean) => Promise<void>) | null>(null);

  useEffect(() => {
    const handleUpdate = (event: CustomEvent) => {
      setUpdateSW(() => event.detail.updateSW);
      setShowUpdate(true);
    };

    window.addEventListener('swUpdateAvailable', handleUpdate as EventListener);
    return () => window.removeEventListener('swUpdateAvailable', handleUpdate as EventListener);
  }, []);

  const handleUpdate = () => {
    if (updateSW) {
      updateSW(true);
    }
  };

  return (
    <AnimatePresence>
      {showUpdate && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          transition={{ type: "spring", stiffness: 260, damping: 20 }}
          className="fixed bottom-4 right-4 z-50 max-w-sm"
        >
          <div className="bg-navy text-white p-4 rounded-2xl shadow-elevated border border-gold/20">
            <div className="flex items-start gap-3">
              <RefreshCw className="w-5 h-5 text-gold mt-0.5" />
              <div className="flex-1">
                <p className="font-serif font-semibold mb-1">New devotionals available!</p>
                <p className="text-sm text-white/80 mb-3">Update to get the latest spiritual content</p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleUpdate}
                    className="bg-gold hover:bg-gold-dark text-navy"
                  >
                    Update Now
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowUpdate(false)}
                    className="text-white/80 hover:text-white"
                  >
                    Later
                  </Button>
                </div>
              </div>
              <button
                onClick={() => setShowUpdate(false)}
                className="text-white/60 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
