import React from 'react';
import { X, AlertTriangle, Info, CheckCircle, AlertCircle, Bell } from 'lucide-react';
import { useAnnouncements } from '../../hooks/useAnnouncements';

const AnnouncementBanner = () => {
  const { getUnreadAnnouncements, markAnnouncementAsRead } = useAnnouncements();
  
  const unreadAnnouncements = getUnreadAnnouncements();
  const highPriorityAnnouncement = unreadAnnouncements.find(
    ann => ann.priority === 'urgent' || ann.priority === 'high'
  );

  if (!highPriorityAnnouncement) return null;

  const getAnnouncementIcon = (type) => {
    switch (type) {
      case 'urgent':
        return <AlertTriangle className="w-5 h-5" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5" />;
      case 'success':
        return <CheckCircle className="w-5 h-5" />;
      case 'info':
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  const getAnnouncementStyles = (type) => {
    switch (type) {
      case 'urgent':
        return {
          bg: 'bg-red-50 border-red-200',
          text: 'text-red-800',
          icon: 'text-red-600',
          button: 'text-red-600 hover:text-red-800'
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50 border-yellow-200',
          text: 'text-yellow-800',
          icon: 'text-yellow-600',
          button: 'text-yellow-600 hover:text-yellow-800'
        };
      case 'success':
        return {
          bg: 'bg-green-50 border-green-200',
          text: 'text-green-800',
          icon: 'text-green-600',
          button: 'text-green-600 hover:text-green-800'
        };
      case 'info':
      default:
        return {
          bg: 'bg-blue-50 border-blue-200',
          text: 'text-blue-800',
          icon: 'text-blue-600',
          button: 'text-blue-600 hover:text-blue-800'
        };
    }
  };

  const styles = getAnnouncementStyles(highPriorityAnnouncement.type);

  const handleDismiss = () => {
    markAnnouncementAsRead(highPriorityAnnouncement.id);
  };

  return (
    <div className={`border-l-4 p-4 ${styles.bg}`}>
      <div className="flex items-start">
        <div className={`flex-shrink-0 ${styles.icon}`}>
          {getAnnouncementIcon(highPriorityAnnouncement.type)}
        </div>
        <div className="ml-3 flex-1">
          <div className="flex items-start justify-between">
            <div>
              <h3 className={`text-sm font-medium ${styles.text}`}>
                {highPriorityAnnouncement.title}
              </h3>
              <p className={`mt-1 text-sm ${styles.text} opacity-90`}>
                {highPriorityAnnouncement.message}
              </p>
              <div className="mt-2 flex items-center text-xs opacity-75">
                <span className={styles.text}>
                  Priority: {highPriorityAnnouncement.priority.toUpperCase()}
                </span>
                <span className={`mx-2 ${styles.text}`}>•</span>
                <span className={styles.text}>
                  Expires: {new Date(highPriorityAnnouncement.expiresAt).toLocaleDateString()}
                </span>
              </div>
            </div>
            {highPriorityAnnouncement.dismissible && (
              <button
                type="button"
                className={`ml-4 ${styles.button} transition-colors duration-200`}
                onClick={handleDismiss}
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnnouncementBanner;