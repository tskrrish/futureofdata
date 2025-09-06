import React, { useEffect, useRef, useState } from 'react';
import QrScanner from 'qr-scanner';
import { Camera, CameraOff } from 'lucide-react';

export const QRScanner = ({ onScan, isActive }) => {
  const videoRef = useRef(null);
  const scannerRef = useRef(null);
  const [hasCamera, setHasCamera] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initScanner = async () => {
      if (!videoRef.current || !isActive) return;

      try {
        const hasCamera = await QrScanner.hasCamera();
        setHasCamera(hasCamera);
        
        if (hasCamera) {
          scannerRef.current = new QrScanner(
            videoRef.current,
            (result) => {
              onScan(result.data);
            },
            {
              preferredCamera: 'environment',
              highlightScanRegion: true,
              highlightCodeOutline: true,
            }
          );
          
          await scannerRef.current.start();
          setError(null);
        }
      } catch (err) {
        setError('Camera access denied or unavailable');
        console.error('QR Scanner error:', err);
      }
    };

    initScanner();

    return () => {
      if (scannerRef.current) {
        scannerRef.current.destroy();
        scannerRef.current = null;
      }
    };
  }, [isActive, onScan]);

  if (!isActive) return null;

  return (
    <div className="relative">
      {hasCamera ? (
        <div className="relative rounded-lg overflow-hidden bg-black">
          <video
            ref={videoRef}
            className="w-full h-64 object-cover"
            playsInline
            muted
          />
          <div className="absolute inset-0 border-2 border-white/30 rounded-lg">
            <div className="absolute top-4 left-4 w-6 h-6 border-l-2 border-t-2 border-blue-400"></div>
            <div className="absolute top-4 right-4 w-6 h-6 border-r-2 border-t-2 border-blue-400"></div>
            <div className="absolute bottom-4 left-4 w-6 h-6 border-l-2 border-b-2 border-blue-400"></div>
            <div className="absolute bottom-4 right-4 w-6 h-6 border-r-2 border-b-2 border-blue-400"></div>
          </div>
          <div className="absolute bottom-2 left-2 right-2 text-center">
            <p className="text-white text-sm bg-black/50 px-2 py-1 rounded">
              Point camera at QR code
            </p>
          </div>
        </div>
      ) : (
        <div className="w-full h-64 bg-gray-100 rounded-lg flex flex-col items-center justify-center text-gray-500">
          <CameraOff className="w-12 h-12 mb-2" />
          <p className="text-lg font-medium">Camera Not Available</p>
          {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
        </div>
      )}
    </div>
  );
};