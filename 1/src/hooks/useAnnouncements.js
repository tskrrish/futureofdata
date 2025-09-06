import { useContext } from 'react';
import { AnnouncementContext } from '../contexts/AnnouncementContext';

export const useAnnouncements = () => {
  const context = useContext(AnnouncementContext);
  if (!context) {
    throw new Error('useAnnouncements must be used within an AnnouncementProvider');
  }
  return context;
};