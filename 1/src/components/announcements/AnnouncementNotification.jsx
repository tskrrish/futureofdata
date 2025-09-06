import React, { useState } from 'react';
import { Bell } from 'lucide-react';
import { useAnnouncements } from '../../hooks/useAnnouncements';
import AnnouncementModal from './AnnouncementModal';

const AnnouncementNotification = () => {
  const { getUnreadAnnouncements } = useAnnouncements();
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const unreadCount = getUnreadAnnouncements().length;

  return (
    <>
      <div className="relative">
        <button
          onClick={() => setIsModalOpen(true)}
          className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
          title={`${unreadCount} unread announcements`}
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>
      </div>

      {isModalOpen && (
        <AnnouncementModal 
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </>
  );
};

export default AnnouncementNotification;