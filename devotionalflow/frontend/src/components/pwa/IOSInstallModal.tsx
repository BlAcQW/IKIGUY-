import { motion } from 'framer-motion';
import { Share, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface IOSInstallModalProps {
  open: boolean;
  onClose: () => void;
}

/**
 * IOSInstallModal - Step-by-step iOS PWA installation instructions
 * Guides iOS/Safari users through the manual installation process
 */
export function IOSInstallModal({ open, onClose }: IOSInstallModalProps) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="font-serif text-2xl">Install FreshManna</DialogTitle>
          <DialogDescription>
            Add FreshManna to your home screen for easy access to daily spiritual content.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">

          <div className="space-y-4">
            {/* Step 1 */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="flex items-start gap-3"
            >
              <div className="w-8 h-8 rounded-full bg-gold/20 flex items-center justify-center shrink-0 text-gold font-semibold">
                1
              </div>
              <div className="flex-1">
                <p className="font-medium mb-1">Tap the Share button</p>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Share className="w-4 h-4" />
                  <span>Usually at the bottom of the screen</span>
                </div>
              </div>
            </motion.div>

            {/* Step 2 */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="flex items-start gap-3"
            >
              <div className="w-8 h-8 rounded-full bg-gold/20 flex items-center justify-center shrink-0 text-gold font-semibold">
                2
              </div>
              <div className="flex-1">
                <p className="font-medium mb-1">Scroll and tap "Add to Home Screen"</p>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Plus className="w-4 h-4" />
                  <span>Look for this icon</span>
                </div>
              </div>
            </motion.div>

            {/* Step 3 */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="flex items-start gap-3"
            >
              <div className="w-8 h-8 rounded-full bg-gold/20 flex items-center justify-center shrink-0 text-gold font-semibold">
                3
              </div>
              <div className="flex-1">
                <p className="font-medium">Tap "Add" to confirm</p>
                <p className="text-sm text-muted-foreground">FreshManna will appear on your home screen</p>
              </div>
            </motion.div>
          </div>

          <Button onClick={onClose} className="w-full bg-gold hover:bg-gold-dark text-navy">
            Got it!
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
