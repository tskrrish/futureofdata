import React, { useState, useCallback, useEffect } from 'react';
import { QrCode, Hash, Nfc, Settings, Wifi, WifiOff, Clock, Users, CheckCircle, AlertTriangle } from 'lucide-react';
import { QRScanner } from './QRScanner';
import { PINEntry } from './PINEntry';
import { NFCReader } from './NFCReader';
import { useOfflineAttendance } from '../../hooks/useOfflineAttendance';

export const KioskCheckIn = ({ 
  onBackToDashboard, 
  branch = 'Main Branch',
  kioskId = 'KIOSK_001' 
}) => {
  const [activeMethod, setActiveMethod] = useState('qr'); // 'qr', 'pin', 'nfc'
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showSettings, setShowSettings] = useState(false);
  const [recentCheckIns, setRecentCheckIns] = useState([]);
  const [currentTime, setCurrentTime] = useState(new Date());

  const {
    addAttendanceEntry,
    stats,
    lastSyncTime,
    exportOfflineData
  } = useOfflineAttendance();

  // Update online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Update current time
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);


  const handleCheckIn = useCallback(async (data) => {
    try {
      // Simulate volunteer lookup (in real app, this would query a database)
      const volunteer = await lookupVolunteer(data.identifier, data.type);
      
      const entry = addAttendanceEntry({
        type: data.type,
        identifier: data.identifier,
        volunteerId: volunteer?.id,
        volunteerName: volunteer?.name,
        branch: branch
      });

      // Add to recent check-ins display
      setRecentCheckIns(prev => [
        {
          id: entry.id,
          name: volunteer?.name || `ID: ${data.identifier}`,
          time: new Date(),
          method: data.type.toUpperCase(),
          status: 'success'
        },
        ...prev.slice(0, 4) // Keep only last 5
      ]);

      // Show success feedback
      showCheckInFeedback(volunteer?.name || data.identifier, true);

    } catch (error) {
      console.error('Check-in error:', error);
      setRecentCheckIns(prev => [
        {
          id: crypto.randomUUID(),
          name: `Failed: ${data.identifier}`,
          time: new Date(),
          method: data.type.toUpperCase(),
          status: 'error'
        },
        ...prev.slice(0, 4)
      ]);
      showCheckInFeedback(data.identifier, false);
    }
  }, [addAttendanceEntry, branch]);

  const handleQRScan = useCallback((qrData) => {
    handleCheckIn({ type: 'qr', identifier: qrData });
  }, [handleCheckIn]);

  const handlePINSubmit = useCallback((pin) => {
    handleCheckIn({ type: 'pin', identifier: pin });
  }, [handleCheckIn]);

  const handleNFCScan = useCallback((nfcData) => {
    handleCheckIn({ type: 'nfc', identifier: nfcData });
  }, [handleCheckIn]);

  const lookupVolunteer = async (identifier, type) => {
    // Simulate API call - in real implementation, this would query your volunteer database
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock volunteer data based on identifier
    const volunteers = {
      'pin': {
        '1234': { id: 'v001', name: 'John Doe' },
        '5678': { id: 'v002', name: 'Jane Smith' },
        '9999': { id: 'v003', name: 'Admin User' }
      },
      'qr': {}, // QR codes would contain volunteer IDs
      'nfc': {} // NFC tags would contain volunteer IDs
    };

    return volunteers[type]?.[identifier] || null;
  };

  const showCheckInFeedback = (identifier, success) => {
    // This could trigger animations, sounds, or other feedback
    console.log(`Check-in ${success ? 'successful' : 'failed'} for:`, identifier);
  };

  const methodOptions = [
    { id: 'qr', label: 'QR Code', icon: QrCode, description: 'Scan QR code' },
    { id: 'pin', label: 'PIN', icon: Hash, description: 'Enter PIN code' },
    { id: 'nfc', label: 'NFC', icon: Nfc, description: 'Tap NFC tag' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      {/* Header */}
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-800">YMCA Check-In Kiosk</h1>
              <div className="text-sm text-gray-600">
                <div className="font-medium">{branch}</div>
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4" />
                  <span>{currentTime.toLocaleString()}</span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Online Status */}
              <div className={`flex items-center space-x-1 text-sm ${isOnline ? 'text-green-600' : 'text-red-600'}`}>
                {isOnline ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                <span>{isOnline ? 'Online' : 'Offline'}</span>
              </div>
              
              {/* Stats */}
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <Users className="w-4 h-4" />
                  <span>{stats.total} entries</span>
                </div>
                {stats.pending > 0 && (
                  <div className="flex items-center space-x-1 text-orange-600">
                    <AlertTriangle className="w-4 h-4" />
                    <span>{stats.pending} pending sync</span>
                  </div>
                )}
              </div>
              
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Check-in Area */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-6">
              {/* Method Selection */}
              <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Choose Check-in Method</h2>
                <div className="grid grid-cols-3 gap-4">
                  {methodOptions.map((method) => {
                    const Icon = method.icon;
                    return (
                      <button
                        key={method.id}
                        onClick={() => setActiveMethod(method.id)}
                        className={`p-4 rounded-lg border-2 transition-all text-center ${
                          activeMethod === method.id
                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                            : 'border-gray-200 hover:border-gray-300 text-gray-600'
                        }`}
                      >
                        <Icon className="w-8 h-8 mx-auto mb-2" />
                        <div className="font-medium">{method.label}</div>
                        <div className="text-sm text-gray-500">{method.description}</div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Active Method Interface */}
              <div className="min-h-[400px] flex items-center justify-center">
                {activeMethod === 'qr' && (
                  <QRScanner onScan={handleQRScan} isActive={true} />
                )}
                {activeMethod === 'pin' && (
                  <PINEntry onPinSubmit={handlePINSubmit} isActive={true} />
                )}
                {activeMethod === 'nfc' && (
                  <NFCReader onNFCScan={handleNFCScan} isActive={true} />
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Recent Check-ins */}
            <div className="bg-white rounded-lg shadow-sm p-4">
              <h3 className="font-semibold text-gray-800 mb-4">Recent Check-ins</h3>
              <div className="space-y-3">
                {recentCheckIns.length === 0 ? (
                  <p className="text-gray-500 text-sm">No recent check-ins</p>
                ) : (
                  recentCheckIns.map((checkIn) => (
                    <div key={checkIn.id} className="flex items-center space-x-3 p-2 bg-gray-50 rounded">
                      <div className={`w-2 h-2 rounded-full ${
                        checkIn.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-800 truncate">
                          {checkIn.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {checkIn.method} • {checkIn.time.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-lg shadow-sm p-4">
              <h3 className="font-semibold text-gray-800 mb-4">System Status</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span>Kiosk ID:</span>
                  <span className="font-mono text-gray-600">{kioskId}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Entries:</span>
                  <span className="font-medium">{stats.total}</span>
                </div>
                <div className="flex justify-between">
                  <span>Pending Sync:</span>
                  <span className={stats.pending > 0 ? 'text-orange-600 font-medium' : ''}>
                    {stats.pending}
                  </span>
                </div>
                {lastSyncTime && (
                  <div className="flex justify-between">
                    <span>Last Sync:</span>
                    <span className="text-gray-600">
                      {lastSyncTime.toLocaleTimeString()}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Admin Actions */}
            <div className="bg-white rounded-lg shadow-sm p-4">
              <h3 className="font-semibold text-gray-800 mb-4">Admin</h3>
              <div className="space-y-2">
                <button
                  onClick={exportOfflineData}
                  className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 
                           rounded transition-colors text-left"
                >
                  Export Data
                </button>
                <button
                  onClick={onBackToDashboard}
                  className="w-full px-3 py-2 text-sm bg-blue-100 hover:bg-blue-200 
                           text-blue-700 rounded transition-colors text-left"
                >
                  Back to Dashboard
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};