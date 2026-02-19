import { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence, PanInfo, useAnimation } from 'framer-motion'
import { X } from 'lucide-react'
import { useIsMobile } from '../hooks/useMediaQuery'

interface BottomSheetProps {
  isOpen: boolean
  onClose: () => void
  children: React.ReactNode
  title?: string
  snapPoints?: number[]
  initialSnap?: number
  showDragHandle?: boolean
  showCloseButton?: boolean
  className?: string
}

/**
 * Mobile-optimized bottom sheet component.
 *
 * On mobile: slides up from bottom with swipe-to-close
 * On desktop: renders as a centered modal
 */
export default function BottomSheet({
  isOpen,
  onClose,
  children,
  title,
  snapPoints = [0.5, 0.9],
  initialSnap = 0,
  showDragHandle = true,
  showCloseButton = true,
  className = '',
}: BottomSheetProps) {
  const isMobile = useIsMobile()
  const controls = useAnimation()
  const sheetRef = useRef<HTMLDivElement>(null)
  const [currentSnap, setCurrentSnap] = useState(initialSnap)

  // Calculate snap point heights
  const getSnapHeight = useCallback(
    (snapIndex: number) => {
      const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 800
      return viewportHeight * snapPoints[snapIndex]
    },
    [snapPoints]
  )

  // Handle drag end
  const handleDragEnd = useCallback(
    (_: any, info: PanInfo) => {
      const velocity = info.velocity.y
      const offset = info.offset.y

      // If swiped down fast or dragged down far enough, close
      if (velocity > 500 || offset > 100) {
        onClose()
        return
      }

      // If swiped up fast, go to highest snap point
      if (velocity < -500) {
        setCurrentSnap(snapPoints.length - 1)
        controls.start({ height: getSnapHeight(snapPoints.length - 1) })
        return
      }

      // Otherwise, snap to nearest point
      const currentHeight = sheetRef.current?.offsetHeight || 0
      let nearestSnap = 0
      let minDistance = Infinity

      snapPoints.forEach((_, index) => {
        const snapHeight = getSnapHeight(index)
        const distance = Math.abs(currentHeight - offset - snapHeight)
        if (distance < minDistance) {
          minDistance = distance
          nearestSnap = index
        }
      })

      setCurrentSnap(nearestSnap)
      controls.start({ height: getSnapHeight(nearestSnap) })
    },
    [controls, getSnapHeight, onClose, snapPoints]
  )

  // Reset to initial snap when opened
  useEffect(() => {
    if (isOpen) {
      setCurrentSnap(initialSnap)
      controls.start({ height: getSnapHeight(initialSnap) })
    }
  }, [isOpen, initialSnap, controls, getSnapHeight])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // Prevent body scroll when open on mobile
  useEffect(() => {
    if (isMobile && isOpen) {
      document.body.style.overflow = 'hidden'
      return () => {
        document.body.style.overflow = ''
      }
    }
  }, [isMobile, isOpen])

  // Mobile: Bottom sheet
  if (isMobile) {
    return (
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/50 z-50"
              onClick={onClose}
            />

            {/* Sheet */}
            <motion.div
              ref={sheetRef}
              initial={{ y: '100%' }}
              animate={{ y: 0, height: getSnapHeight(currentSnap) }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
              drag="y"
              dragConstraints={{ top: 0 }}
              dragElastic={0.2}
              onDragEnd={handleDragEnd}
              className={`fixed bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-2xl z-50 flex flex-col ${className}`}
              style={{ maxHeight: '90vh', paddingBottom: 'env(safe-area-inset-bottom)' }}
            >
              {/* Header */}
              <div className="flex-shrink-0 pt-2 pb-2">
                {showDragHandle && (
                  <div className="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-2" />
                )}

                {(title || showCloseButton) && (
                  <div className="flex items-center justify-between px-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {title || ''}
                    </h3>
                    {showCloseButton && (
                      <button
                        onClick={onClose}
                        className="p-2 rounded-full hover:bg-gray-100 transition-colors -mr-2"
                      >
                        <X className="w-5 h-5 text-gray-500" />
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto px-4 pb-4">
                {children}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    )
  }

  // Desktop: Centered modal
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={onClose}
          >
            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className={`bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[85vh] flex flex-col ${className}`}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              {(title || showCloseButton) && (
                <div className="flex items-center justify-between p-4 border-b border-gray-100">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {title || ''}
                  </h3>
                  {showCloseButton && (
                    <button
                      onClick={onClose}
                      className="p-2 rounded-full hover:bg-gray-100 transition-colors -mr-2"
                    >
                      <X className="w-5 h-5 text-gray-500" />
                    </button>
                  )}
                </div>
              )}

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-4">
                {children}
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
