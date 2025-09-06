import React, { useState } from 'react';
import { Share, Gift, Users, Trophy, Copy, Check, ExternalLink } from 'lucide-react';
import { useReferrals } from '../../hooks/useReferrals';

export function ReferralTab() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [copiedLink, setCopiedLink] = useState('');
  
  // Mock user ID - in real app this would come from auth context
  const currentUserId = 'demo-user-123';
  
  const {
    referrals: userReferrals,
    loading,
    error,
    createReferralLink
  } = useReferrals(currentUserId);

  const handleCreateReferralLink = async () => {
    try {
      await createReferralLink();
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create referral link:', error);
      alert('Failed to create referral link. Please try again.');
    }
  };

  const copyToClipboard = (link, code) => {
    navigator.clipboard.writeText(link);
    setCopiedLink(code);
    setTimeout(() => setCopiedLink(''), 2000);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'expired': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRewardIcon = (type) => {
    switch (type) {
      case 'recognition_badge': return <Trophy className="w-5 h-5" />;
      case 'volunteer_hours': return <Users className="w-5 h-5" />;
      case 'gift_card': return <Gift className="w-5 h-5" />;
      default: return <Gift className="w-5 h-5" />;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-2xl"></div>
          ))}
        </div>
        <div className="h-96 bg-gray-200 rounded-2xl"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-6 border">
          <div className="flex items-center">
            <Share className="w-5 h-5 text-blue-600" />
            <span className="ml-2 text-sm text-neutral-600">Active Links</span>
          </div>
          <p className="text-2xl font-bold text-neutral-900 mt-2">{userReferrals.stats.active_links}</p>
        </div>
        
        <div className="bg-white rounded-2xl p-6 border">
          <div className="flex items-center">
            <Users className="w-5 h-5 text-green-600" />
            <span className="ml-2 text-sm text-neutral-600">Total Referrals</span>
          </div>
          <p className="text-2xl font-bold text-neutral-900 mt-2">{userReferrals.stats.total_conversions}</p>
        </div>
        
        <div className="bg-white rounded-2xl p-6 border">
          <div className="flex items-center">
            <Gift className="w-5 h-5 text-purple-600" />
            <span className="ml-2 text-sm text-neutral-600">Rewards Earned</span>
          </div>
          <p className="text-2xl font-bold text-neutral-900 mt-2">{userReferrals.stats.total_rewards}</p>
        </div>
        
        <div className="bg-white rounded-2xl p-6 border">
          <div className="flex items-center">
            <Trophy className="w-5 h-5 text-orange-600" />
            <span className="ml-2 text-sm text-neutral-600">Success Rate</span>
          </div>
          <p className="text-2xl font-bold text-neutral-900 mt-2">
            {userReferrals.stats.total_links > 0 
              ? Math.round((userReferrals.stats.total_conversions / userReferrals.stats.total_links) * 100) 
              : 0}%
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Referral Links */}
        <div className="lg:col-span-2 bg-white rounded-2xl border">
          <div className="p-6 border-b">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-neutral-900">Your Referral Links</h3>
              <button
                onClick={() => setShowCreateForm(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm hover:bg-blue-700 transition-colors"
              >
                Create New Link
              </button>
            </div>
          </div>
          
          <div className="p-6">
            {showCreateForm && (
              <div className="mb-6 p-4 bg-blue-50 rounded-xl border border-blue-200">
                <h4 className="font-semibold text-blue-900 mb-2">Create New Referral Link</h4>
                <p className="text-sm text-blue-700 mb-4">
                  Share this link with friends and family to invite them to volunteer with YMCA.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleCreateReferralLink}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
                  >
                    Generate Link
                  </button>
                  <button
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
            
            <div className="space-y-4">
              {userReferrals.referral_links.map(link => (
                <div key={link.id} className="border rounded-xl p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-neutral-900">{link.referral_code}</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(link.status)}`}>
                          {link.status}
                        </span>
                      </div>
                      <p className="text-sm text-neutral-600">
                        {link.conversion_count} referrals • Expires {formatDate(link.expires_at)}
                      </p>
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => copyToClipboard(link.invite_link, link.referral_code)}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Copy link"
                      >
                        {copiedLink === link.referral_code ? 
                          <Check className="w-4 h-4 text-green-600" /> : 
                          <Copy className="w-4 h-4" />
                        }
                      </button>
                      <button
                        onClick={() => window.open(link.invite_link, '_blank')}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Open link"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 font-mono bg-gray-50 p-2 rounded border">
                    {link.invite_link}
                  </div>
                </div>
              ))}
              
              {userReferrals.referral_links.length === 0 && (
                <div className="text-center py-8">
                  <Share className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500">No referral links created yet</p>
                  <p className="text-sm text-gray-400">Create your first referral link to start inviting friends!</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Rewards */}
        <div className="bg-white rounded-2xl border">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-neutral-900">Your Rewards</h3>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {userReferrals.rewards.map(reward => (
                <div key={reward.id} className="flex items-start gap-3 p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border">
                  <div className="text-purple-600 mt-1">
                    {getRewardIcon(reward.reward_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 text-sm">{reward.reward_title}</p>
                    <p className="text-xs text-gray-600">{reward.reward_description}</p>
                    {reward.reward_value && (
                      <p className="text-xs text-green-600 font-semibold">Value: {reward.reward_value}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">
                      Earned {formatDate(reward.awarded_at)}
                    </p>
                  </div>
                </div>
              ))}
              
              {userReferrals.rewards.length === 0 && (
                <div className="text-center py-6">
                  <Trophy className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">No rewards earned yet</p>
                  <p className="text-xs text-gray-400">Refer volunteers to earn rewards!</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-6 border border-blue-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">How the Referral Program Works</h3>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-semibold">1</div>
            <div>
              <p className="font-semibold text-gray-900">Share Your Link</p>
              <p className="text-sm text-gray-600">Create and share your unique referral link with friends and family</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-semibold">2</div>
            <div>
              <p className="font-semibold text-gray-900">They Join & Volunteer</p>
              <p className="text-sm text-gray-600">When they sign up and start volunteering, you both benefit</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center text-sm font-semibold">3</div>
            <div>
              <p className="font-semibold text-gray-900">Earn Rewards</p>
              <p className="text-sm text-gray-600">Get recognition badges, bonus hours, and other exciting rewards</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}