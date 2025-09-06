// Utility functions for announcement management
export const announcementUtils = {
  // Check if announcement is expired
  isExpired: (announcement) => {
    const now = new Date();
    const expires = new Date(announcement.expiresAt);
    return now > expires;
  },

  // Check if user has read the announcement
  hasUserRead: (announcement, userId) => {
    return announcement.readReceipts.some(receipt => receipt.userId === userId);
  },

  // Filter announcements based on user context
  filterForUser: (announcements, userContext) => {
    const { branch, role, department } = userContext;
    
    return announcements.filter(announcement => {
      // Check if announcement is active and not expired
      if (!announcement.isActive || announcementUtils.isExpired(announcement)) {
        return false;
      }

      // Check branch targeting
      const branchMatch = announcement.targetBranches.includes("All") || 
                         announcement.targetBranches.includes(branch);
      
      // Check role targeting
      const roleMatch = announcement.targetRoles.includes("All") ||
                       announcement.targetRoles.includes(role);
      
      // Check department targeting
      const departmentMatch = announcement.targetDepartments.includes("All") ||
                             announcement.targetDepartments.includes(department);
      
      return branchMatch && roleMatch && departmentMatch;
    });
  },

  // Mark announcement as read by user
  markAsRead: (announcement, userId, branch) => {
    if (!announcementUtils.hasUserRead(announcement, userId)) {
      announcement.readReceipts.push({
        userId,
        readAt: new Date().toISOString(),
        branch
      });
    }
    return announcement;
  },

  // Get unread announcements for user
  getUnreadForUser: (announcements, userContext) => {
    const filtered = announcementUtils.filterForUser(announcements, userContext);
    return filtered.filter(announcement => 
      !announcementUtils.hasUserRead(announcement, userContext.userId)
    );
  },

  // Sort announcements by priority and date
  sortAnnouncements: (announcements) => {
    const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
    
    return [...announcements].sort((a, b) => {
      // First sort by priority
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
      if (priorityDiff !== 0) return priorityDiff;
      
      // Then by creation date (newest first)
      return new Date(b.createdAt) - new Date(a.createdAt);
    });
  }
};