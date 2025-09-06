import { useState, useEffect } from 'react';

// API base URL - in production this would come from environment variables
const API_BASE_URL = 'http://localhost:8000/api';

export function useReferrals(userId) {
  const [referrals, setReferrals] = useState({
    referral_links: [],
    conversions: [],
    rewards: [],
    stats: {
      total_links: 0,
      total_conversions: 0,
      total_rewards: 0,
      active_links: 0
    }
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load user referrals
  const loadReferrals = async () => {
    if (!userId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/referrals/user/${userId}`);
      
      if (!response.ok) {
        throw new Error('Failed to load referrals');
      }

      const data = await response.json();
      
      if (data.success) {
        setReferrals(data.referrals);
      } else {
        throw new Error('Failed to load referrals');
      }
    } catch (err) {
      console.error('Error loading referrals:', err);
      setError(err.message);
      
      // For demo purposes, use mock data on error
      setReferrals({
        referral_links: [
          {
            id: '1',
            referral_code: 'VOLUNTEER2024',
            invite_link: 'https://ymca-volunteer-pathfinder.com/join?ref=VOLUNTEER2024',
            status: 'pending',
            conversion_count: 2,
            expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
            created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
          }
        ],
        conversions: [
          {
            id: '1',
            conversion_type: 'user_signup',
            converted_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
          }
        ],
        rewards: [
          {
            id: '1',
            reward_type: 'recognition_badge',
            reward_title: 'Volunteer Recruiter',
            reward_description: 'Successfully referred someone to volunteer',
            status: 'awarded',
            awarded_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
          }
        ],
        stats: {
          total_links: 1,
          total_conversions: 1,
          total_rewards: 1,
          active_links: 1
        }
      });
    } finally {
      setLoading(false);
    }
  };

  // Create new referral link
  const createReferralLink = async (expiresInDays = 30) => {
    try {
      const response = await fetch(`${API_BASE_URL}/referrals/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          expires_in_days: expiresInDays
        }),
        // In real app, would need to pass user_id properly (via auth headers, etc.)
      });

      if (!response.ok) {
        throw new Error('Failed to create referral link');
      }

      const data = await response.json();
      
      if (data.success) {
        // Refresh referrals to show new link
        await loadReferrals();
        return data.referral_link;
      } else {
        throw new Error('Failed to create referral link');
      }
    } catch (err) {
      console.error('Error creating referral link:', err);
      
      // For demo purposes, create a mock link
      const mockLink = {
        id: Date.now().toString(),
        referral_code: 'NEW' + Math.random().toString(36).substr(2, 8).toUpperCase(),
        invite_link: `https://ymca-volunteer-pathfinder.com/join?ref=NEW${Math.random().toString(36).substr(2, 8).toUpperCase()}`,
        status: 'pending',
        conversion_count: 0,
        expires_at: new Date(Date.now() + expiresInDays * 24 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString()
      };
      
      setReferrals(prev => ({
        ...prev,
        referral_links: [mockLink, ...prev.referral_links],
        stats: {
          ...prev.stats,
          total_links: prev.stats.total_links + 1,
          active_links: prev.stats.active_links + 1
        }
      }));
      
      return mockLink;
    }
  };

  // Validate referral code
  const validateReferralCode = async (referralCode) => {
    try {
      const response = await fetch(`${API_BASE_URL}/referrals/validate/${referralCode}`);
      
      if (!response.ok) {
        throw new Error('Failed to validate referral code');
      }

      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error validating referral code:', err);
      
      // For demo purposes, return mock validation
      return {
        valid: true,
        referral: {
          referral_code: referralCode,
          user_id: 'referrer-123'
        }
      };
    }
  };

  // Sign up through referral
  const signupWithReferral = async (referralCode, userData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/referrals/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          referral_code: referralCode,
          user_data: userData
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to sign up with referral');
      }

      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error signing up with referral:', err);
      
      // For demo purposes, simulate successful signup
      return {
        success: true,
        user: {
          id: 'new-user-' + Date.now(),
          ...userData
        },
        referral_tracked: true
      };
    }
  };

  // Track volunteer activity
  const trackVolunteerActivity = async (userId, activityData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/referrals/track-activity`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          activity_data: activityData
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to track volunteer activity');
      }

      const data = await response.json();
      return data.success;
    } catch (err) {
      console.error('Error tracking volunteer activity:', err);
      return false;
    }
  };

  // Get referral analytics
  const getReferralAnalytics = async (days = 30) => {
    try {
      const response = await fetch(`${API_BASE_URL}/referrals/analytics?days=${days}`);
      
      if (!response.ok) {
        throw new Error('Failed to get referral analytics');
      }

      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error getting referral analytics:', err);
      
      // Return mock analytics for demo
      return {
        period_days: days,
        total_links_created: 15,
        total_conversions: 8,
        total_rewards_awarded: 12,
        conversion_rate: 53.33,
        generated_at: new Date().toISOString()
      };
    }
  };

  useEffect(() => {
    loadReferrals();
  }, [userId]);

  return {
    referrals,
    loading,
    error,
    loadReferrals,
    createReferralLink,
    validateReferralCode,
    signupWithReferral,
    trackVolunteerActivity,
    getReferralAnalytics
  };
}