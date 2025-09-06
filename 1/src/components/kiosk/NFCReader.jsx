import React, { useState, useEffect, useCallback } from 'react';
import { Nfc, Zap, AlertCircle } from 'lucide-react';

export const NFCReader = ({ onNFCScan, isActive }) => {
  const [isReading, setIsReading] = useState(false);
  const [hasNFCSupport, setHasNFCSupport] = useState(false);
  const [error, setError] = useState(null);
  const [abortController, setAbortController] = useState(null);

  useEffect(() => {
    if ('NDEFReader' in window) {
      setHasNFCSupport(true);
    } else {
      setHasNFCSupport(false);
    }
  }, []);

  const startNFCReading = useCallback(async () => {
    if (!hasNFCSupport || !isActive) return;

    try {
      const ndef = new window.NDEFReader();
      const controller = new AbortController();
      setAbortController(controller);
      
      await ndef.scan({ signal: controller.signal });
      setIsReading(true);
      setError(null);

      ndef.addEventListener('reading', ({ message, serialNumber }) => {
        console.log('NFC tag read:', { message, serialNumber });
        
        let data = serialNumber;
        
        if (message && message.records.length > 0) {
          const record = message.records[0];
          if (record.recordType === 'text') {
            const textDecoder = new TextDecoder(record.encoding || 'utf-8');
            data = textDecoder.decode(record.data);
          } else if (record.recordType === 'url') {
            data = new TextDecoder().decode(record.data);
          }
        }
        
        onNFCScan(data);
        setIsReading(false);
      });

      ndef.addEventListener('readingerror', (error) => {
        console.error('NFC reading error:', error);
        setError('Failed to read NFC tag');
        setIsReading(false);
      });

    } catch (error) {
      console.error('NFC scan error:', error);
      if (error.name === 'NotAllowedError') {
        setError('NFC access denied. Please enable NFC permissions.');
      } else if (error.name === 'NotSupportedError') {
        setError('NFC not supported on this device.');
      } else {
        setError('NFC scanning failed.');
      }
      setIsReading(false);
    }
  }, [hasNFCSupport, isActive, onNFCScan]);

  const stopNFCReading = useCallback(() => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
    }
    setIsReading(false);
  }, [abortController]);

  useEffect(() => {
    if (isActive && hasNFCSupport) {
      startNFCReading();
    } else {
      stopNFCReading();
    }

    return () => {
      stopNFCReading();
    };
  }, [isActive, hasNFCSupport, startNFCReading, stopNFCReading]);

  if (!isActive) return null;

  if (!hasNFCSupport) {
    return (
      <div className="text-center p-6 bg-gray-50 rounded-lg border">
        <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-400" />
        <h3 className="text-lg font-medium text-gray-700 mb-2">NFC Not Supported</h3>
        <p className="text-sm text-gray-500">
          This device does not support NFC reading or Web NFC is not enabled.
        </p>
        <p className="text-xs text-gray-400 mt-2">
          Web NFC requires HTTPS and is currently only supported in Chrome on Android.
        </p>
      </div>
    );
  }

  return (
    <div className="text-center p-6">
      <div className={`w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center
                      ${isReading ? 'bg-blue-100 animate-pulse' : 'bg-gray-100'}`}>
        <Nfc className={`w-10 h-10 ${isReading ? 'text-blue-500' : 'text-gray-400'}`} />
      </div>
      
      <h3 className="text-lg font-semibold text-gray-700 mb-2">
        {isReading ? 'NFC Ready' : 'NFC Scanner'}
      </h3>
      
      {isReading ? (
        <div className="space-y-2">
          <div className="flex items-center justify-center space-x-2 text-blue-600">
            <Zap className="w-4 h-4" />
            <p className="text-sm font-medium">Hold NFC tag near device</p>
          </div>
          <p className="text-xs text-gray-500">Scanning for NFC tags...</p>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-sm text-gray-600">Tap to start NFC scanning</p>
          <button
            onClick={startNFCReading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium
                     hover:bg-blue-600 transition-colors"
          >
            Start NFC Scanner
          </button>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
    </div>
  );
};