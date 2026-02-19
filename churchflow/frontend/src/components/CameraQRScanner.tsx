/**
 * Camera QR Code Scanner Component
 *
 * Uses device camera to scan QR codes in real-time.
 * Lightweight wrapper around html5-qrcode library.
 * Supports switching between front and back cameras.
 */

import { useEffect, useRef, useState } from 'react'
import { Html5Qrcode } from 'html5-qrcode'
import { Camera, X, Loader, RefreshCw } from 'lucide-react'

interface CameraQRScannerProps {
  onScan: (decodedText: string) => void
  onClose: () => void
}

export default function CameraQRScanner({ onScan, onClose }: CameraQRScannerProps) {
  const [isScanning, setIsScanning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment')
  const scannerRef = useRef<Html5Qrcode | null>(null)
  const isInitialized = useRef(false)
  const isSwitching = useRef(false)

  const initScanner = async (mode: 'environment' | 'user') => {
    try {
      setIsScanning(true)
      setError(null)

      // Create new scanner instance
      const scanner = new Html5Qrcode('qr-reader')
      scannerRef.current = scanner

      // Start scanning with specified camera
      await scanner.start(
        { facingMode: mode },
        {
          fps: 10,
          qrbox: { width: 250, height: 250 },
        },
        (decodedText) => {
          console.log('QR Code detected:', decodedText)
          stopScanner()
          onScan(decodedText)
        },
        () => {
          // Scanning errors (normal, happens constantly while scanning)
        }
      )
    } catch (err: any) {
      console.error('Failed to start camera:', err)
      setError('Failed to access camera. Please ensure camera permissions are granted.')
      setIsScanning(false)
    }
  }

  useEffect(() => {
    // Prevent double initialization in React strict mode
    if (isInitialized.current && !isSwitching.current) return
    isInitialized.current = true
    isSwitching.current = false

    initScanner(facingMode)

    // Cleanup on unmount
    return () => {
      stopScanner()
    }
  }, [facingMode])

  const stopScanner = async () => {
    if (scannerRef.current?.isScanning) {
      try {
        await scannerRef.current.stop()
        scannerRef.current.clear()
      } catch (err) {
        console.error('Error stopping scanner:', err)
      }
    }
    setIsScanning(false)
  }

  const switchCamera = async () => {
    // Stop current scanner
    if (scannerRef.current?.isScanning) {
      try {
        await scannerRef.current.stop()
        scannerRef.current.clear()
      } catch (err) {
        console.error('Error stopping scanner for switch:', err)
      }
    }
    scannerRef.current = null
    setIsScanning(false)

    // Toggle facing mode - this will trigger useEffect to reinitialize
    isSwitching.current = true
    setFacingMode(prev => prev === 'environment' ? 'user' : 'environment')
  }

  const handleClose = async () => {
    await stopScanner()
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/80 z-[70] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-modal max-w-lg w-full overflow-hidden animate-modal-enter">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Camera className="w-5 h-5 text-white" />
            <h2 className="text-lg font-semibold text-white">Scan QR Code</h2>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={switchCamera}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title={facingMode === 'environment' ? 'Switch to Front Camera' : 'Switch to Back Camera'}
            >
              <RefreshCw className="w-5 h-5 text-white" />
            </button>
            <button
              onClick={handleClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>

        {/* Scanner Area */}
        <div className="p-5">
          {error ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-center">
              <p className="text-red-700 text-sm mb-4">{error}</p>
              <button onClick={handleClose} className="btn-danger">
                Close
              </button>
            </div>
          ) : (
            <>
              {/* Camera feed container */}
              <div id="qr-reader" className="rounded-xl overflow-hidden border-2 border-purple-100"></div>

              {/* Instructions */}
              <div className="mt-5 text-center">
                <div className="flex items-center justify-center gap-2 text-gray-600 mb-2">
                  {isScanning ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin text-purple-600" />
                      <span className="text-sm">
                        {facingMode === 'environment' ? 'Back' : 'Front'} camera active
                      </span>
                    </>
                  ) : (
                    <span className="text-sm">Starting camera...</span>
                  )}
                </div>
                <p className="text-xs text-gray-500">
                  Position QR code within frame. Detection is automatic.
                </p>
              </div>

              {/* Close button */}
              <div className="mt-5">
                <button onClick={handleClose} className="btn-secondary w-full">
                  Cancel
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
