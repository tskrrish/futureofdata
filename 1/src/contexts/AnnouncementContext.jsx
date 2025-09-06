/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useState } from 'react';
import { SAMPLE_ANNOUNCEMENTS } from '../data/announcementData';
import { announcementUtils } from '../utils/announcementUtils';

export const AnnouncementContext = createContext();

export const AnnouncementProvider = ({ children }) => {
  const [announcements, setAnnouncements] = useState(SAMPLE_ANNOUNCEMENTS);
  const [userContext, setUserContext] = useState({
    userId: 'current-user', // In a real app, this would come from auth
    branch: 'Blue Ash', // Default branch
    role: 'volunteer', // Default role
    department: 'Youth Development' // Default department
  });

  // Get announcements filtered for current user
  const getAnnouncementsForUser = () => {
    const filtered = announcementUtils.filterForUser(announcements, userContext);
    return announcementUtils.sortAnnouncements(filtered);
  };

  // Get unread announcements for current user
  const getUnreadAnnouncements = () => {
    return announcementUtils.getUnreadForUser(announcements, userContext);
  };

  // Mark announcement as read
  const markAnnouncementAsRead = (announcementId) => {
    setAnnouncements(prev => prev.map(announcement => {
      if (announcement.id === announcementId) {
        return announcementUtils.markAsRead(announcement, userContext.userId, userContext.branch);
      }
      return announcement;
    }));
  };

  // Add new announcement (for admin functionality)
  const addAnnouncement = (newAnnouncement) => {
    const announcement = {
      ...newAnnouncement,
      id: `ann-${Date.now()}`,
      createdAt: new Date().toISOString(),
      readReceipts: [],
      isActive: true
    };
    setAnnouncements(prev => [announcement, ...prev]);
  };

  // Update announcement
  const updateAnnouncement = (announcementId, updates) => {
    setAnnouncements(prev => prev.map(announcement =>
      announcement.id === announcementId 
        ? { ...announcement, ...updates }
        : announcement
    ));
  };

  // Delete announcement
  const deleteAnnouncement = (announcementId) => {
    setAnnouncements(prev => prev.filter(announcement => announcement.id !== announcementId));
  };

  // Update user context (branch, role, etc.)
  const updateUserContext = (updates) => {
    setUserContext(prev => ({ ...prev, ...updates }));
  };

  // Get read receipt stats for an announcement
  const getReadReceiptStats = (announcementId) => {
    const announcement = announcements.find(ann => ann.id === announcementId);
    if (!announcement) return { totalReads: 0, readReceipts: [] };

    return {
      totalReads: announcement.readReceipts.length,
      readReceipts: announcement.readReceipts
    };
  };

  const value = {
    announcements,
    userContext,
    getAnnouncementsForUser,
    getUnreadAnnouncements,
    markAnnouncementAsRead,
    addAnnouncement,
    updateAnnouncement,
    deleteAnnouncement,
    updateUserContext,
    getReadReceiptStats
  };

  return (
    <AnnouncementContext.Provider value={value}>
      {children}
    </AnnouncementContext.Provider>
  );
};