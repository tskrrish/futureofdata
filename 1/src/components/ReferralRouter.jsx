import React from 'react';
import { ReferralSignup } from './ReferralSignup';

export function ReferralRouter() {
  // Simple URL parameter parsing for referral code
  const urlParams = new URLSearchParams(window.location.search);
  const referralCode = urlParams.get('ref');

  if (referralCode) {
    return <ReferralSignup referralCode={referralCode} />;
  }

  // If no referral code, redirect to main app
  window.location.href = '/';
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <p className="text-gray-600">Redirecting to main application...</p>
      </div>
    </div>
  );
}