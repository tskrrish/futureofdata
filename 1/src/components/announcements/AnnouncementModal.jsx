import React, { useState } from 'react';
import { X, AlertTriangle, Info, CheckCircle, AlertCircle, Clock, MapPin, Users, Briefcase } from 'lucide-react';
import { useAnnouncements } from '../../hooks/useAnnouncements';

const AnnouncementModal = ({ isOpen, onClose }) => {
  const { 
    getAnnouncementsForUser, 
    getUnreadAnnouncements,
    markAnnouncementAsRead,
    userContext 
  } = useAnnouncements();
  
  const [filter, setFilter] = useState('all'); // 'all', 'unread'
  
  const allAnnouncements = getAnnouncementsForUser();
  const unreadAnnouncements = getUnreadAnnouncements();
  
  const displayedAnnouncements = filter === 'unread' ? unreadAnnouncements : allAnnouncements;

  if (!isOpen) return null;

  const getAnnouncementIcon = (type) => {
    switch (type) {
      case 'urgent':
        return <AlertTriangle className="w-4 h-4" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4" />;
      case 'success':
        return <CheckCircle className="w-4 h-4" />;
      case 'info':
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const getAnnouncementStyles = (type, isRead) => {
    const baseOpacity = isRead ? 'opacity-75' : 'opacity-100';
    const baseBg = isRead ? 'bg-gray-50' : '';
    
    switch (type) {
      case 'urgent':
        return {
          border: 'border-l-red-500',
          icon: 'text-red-600',
          badge: 'bg-red-100 text-red-800',
          bg: baseBg,
          opacity: baseOpacity
        };
      case 'warning':
        return {
          border: 'border-l-yellow-500',
          icon: 'text-yellow-600',
          badge: 'bg-yellow-100 text-yellow-800',
          bg: baseBg,
          opacity: baseOpacity
        };
      case 'success':
        return {
          border: 'border-l-green-500',
          icon: 'text-green-600',
          badge: 'bg-green-100 text-green-800',
          bg: baseBg,
          opacity: baseOpacity
        };
      case 'info':
      default:
        return {
          border: 'border-l-blue-500',
          icon: 'text-blue-600',
          badge: 'bg-blue-100 text-blue-800',
          bg: baseBg,
          opacity: baseOpacity
        };
    }
  };

  const isAnnouncementRead = (announcement) => {
    return announcement.readReceipts.some(receipt => receipt.userId === userContext.userId);
  };

  const handleAnnouncementClick = (announcement) => {
    if (!isAnnouncementRead(announcement)) {
      markAnnouncementAsRead(announcement.id);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Announcements</h2>
            <p className="text-sm text-gray-500 mt-1">
              {unreadAnnouncements.length} unread • {allAnnouncements.length} total
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="px-6 py-3 border-b bg-gray-50">
          <div className="flex space-x-4">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                filter === 'all' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              All ({allAnnouncements.length})
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                filter === 'unread' 
                  ? 'bg-red-100 text-red-700' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Unread ({unreadAnnouncements.length})
            </button>
          </div>
        </div>

        {/* Current User Context */}
        <div className="px-6 py-3 bg-blue-50 border-b">
          <div className="flex items-center space-x-4 text-xs text-blue-700">
            <div className="flex items-center">
              <MapPin className="w-3 h-3 mr-1" />
              {userContext.branch}
            </div>
            <div className="flex items-center">
              <Users className="w-3 h-3 mr-1" />
              {userContext.role}
            </div>
            <div className="flex items-center">
              <Briefcase className="w-3 h-3 mr-1" />
              {userContext.department}
            </div>
          </div>
        </div>

        {/* Announcements List */}
        <div className="flex-1 overflow-y-auto">
          {displayedAnnouncements.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Info className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No {filter === 'unread' ? 'unread ' : ''}announcements to display</p>
            </div>
          ) : (
            <div className="divide-y">
              {displayedAnnouncements.map((announcement) => {
                const isRead = isAnnouncementRead(announcement);
                const styles = getAnnouncementStyles(announcement.type, isRead);
                
                return (
                  <div
                    key={announcement.id}
                    className={`p-6 border-l-4 cursor-pointer hover:bg-gray-50 transition-colors ${styles.border} ${styles.bg} ${styles.opacity}`}
                    onClick={() => handleAnnouncementClick(announcement)}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={`flex-shrink-0 mt-1 ${styles.icon}`}>
                        {getAnnouncementIcon(announcement.type)}
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className={`font-medium text-gray-900 ${isRead ? 'opacity-75' : ''}`}>
                                {announcement.title}
                              </h3>
                              {!isRead && (
                                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                              )}
                            </div>
                            
                            <p className={`text-sm text-gray-700 mb-3 ${isRead ? 'opacity-75' : ''}`}>
                              {announcement.message}
                            </p>
                            
                            {/* Metadata */}
                            <div className="flex items-center space-x-4 text-xs text-gray-500">
                              <span className={`inline-flex items-center px-2 py-1 rounded-md ${styles.badge}`}>
                                {announcement.priority.toUpperCase()}
                              </span>
                              
                              <div className="flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                {formatDate(announcement.createdAt)}
                              </div>
                              
                              <div className="flex items-center">
                                <MapPin className="w-3 h-3 mr-1" />
                                {announcement.targetBranches.includes('All') ? 'All Branches' : announcement.targetBranches.join(', ')}
                              </div>
                            </div>
                            
                            {/* Read receipts count */}
                            <div className="mt-2 text-xs text-gray-400">
                              {announcement.readReceipts.length} read
                              {announcement.readReceipts.length > 0 && announcement.readReceipts.length <= 3 && (
                                <span> • Last read: {formatDate(announcement.readReceipts[announcement.readReceipts.length - 1].readAt)}</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50">
          <div className="flex justify-between items-center">
            <p className="text-xs text-gray-500">
              Showing announcements for your current role and branch
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnnouncementModal;