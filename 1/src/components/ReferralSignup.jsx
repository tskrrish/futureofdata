import React, { useState, useEffect } from 'react';
import { Users, Heart, ArrowRight, CheckCircle } from 'lucide-react';

export function ReferralSignup({ referralCode }) {
  const [referralInfo, setReferralInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    age: '',
    city: '',
    state: 'OH',
    is_ymca_member: false
  });
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (referralCode) {
      validateReferralCode();
    }
  }, [referralCode]);

  const validateReferralCode = async () => {
    try {
      // In real app, this would call the API
      // For demo purposes, we'll use mock validation
      const mockReferralInfo = {
        valid: true,
        referral: {
          referral_code: referralCode,
          user_id: 'referrer-123',
          referrer_name: 'Jane Volunteer' // In real app, this would come from the API
        }
      };
      
      setReferralInfo(mockReferralInfo);
      setLoading(false);
    } catch (error) {
      console.error('Failed to validate referral code:', error);
      setReferralInfo({ valid: false });
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      // In real app, this would call the signup API with referral tracking
      await new Promise(resolve => setTimeout(resolve, 1500)); // Mock delay
      
      console.log('Signup data:', {
        referral_code: referralCode,
        user_data: formData
      });
      
      setSuccess(true);
    } catch (error) {
      console.error('Signup failed:', error);
      alert('Signup failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl p-8 shadow-lg border max-w-md w-full mx-4">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded mb-4"></div>
            <div className="h-4 bg-gray-200 rounded mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!referralInfo || !referralInfo.valid) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl p-8 shadow-lg border max-w-md w-full mx-4 text-center">
          <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <Users className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Invalid Referral Link</h1>
          <p className="text-gray-600 mb-6">
            This referral link is invalid or has expired. Please contact the person who shared it with you.
          </p>
          <button
            onClick={() => window.location.href = '/'}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors"
          >
            Go to Main Site
          </button>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl p-8 shadow-lg border max-w-md w-full mx-4 text-center">
          <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Welcome to YMCA!</h1>
          <p className="text-gray-600 mb-6">
            Your account has been created successfully! Thanks for joining through {referralInfo.referral.referrer_name}'s referral.
            You'll receive an email with next steps to start volunteering.
          </p>
          <button
            onClick={() => window.location.href = '/chat'}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
          >
            Start Your Journey <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-600 text-white rounded-xl flex items-center justify-center">
              <Heart className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">YMCA Volunteer PathFinder</h1>
              <p className="text-gray-600">Join our volunteer community</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Welcome Message */}
          <div className="bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-2xl p-8">
            <h2 className="text-3xl font-bold mb-4">You're Invited!</h2>
            <p className="text-blue-100 mb-6">
              {referralInfo.referral.referrer_name} has invited you to join the YMCA volunteer community. 
              By signing up through this referral, you're taking the first step toward making a meaningful 
              impact in your community.
            </p>
            
            <div className="bg-white/10 backdrop-blur rounded-xl p-6">
              <h3 className="font-semibold text-lg mb-3">What You'll Get:</h3>
              <ul className="space-y-2 text-blue-100">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Personalized volunteer matching
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  AI-powered guidance and support
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Access to exclusive volunteer opportunities
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Recognition for your contributions
                </li>
              </ul>
            </div>

            <div className="mt-6 p-4 bg-white/10 backdrop-blur rounded-xl">
              <p className="text-sm text-blue-100">
                <strong>Referral Code:</strong> {referralCode}
              </p>
            </div>
          </div>

          {/* Signup Form */}
          <div className="bg-white rounded-2xl p-8 shadow-lg border">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Create Your Account</h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    First Name *
                  </label>
                  <input
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your first name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Last Name *
                  </label>
                  <input
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your last name"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your email address"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Phone Number
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your phone number"
                />
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Age
                  </label>
                  <input
                    type="number"
                    name="age"
                    value={formData.age}
                    onChange={handleInputChange}
                    min="13"
                    max="120"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Your age"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    City
                  </label>
                  <input
                    type="text"
                    name="city"
                    value={formData.city}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Your city"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  name="is_ymca_member"
                  checked={formData.is_ymca_member}
                  onChange={handleInputChange}
                  className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label className="text-sm text-gray-700">
                  I am currently a YMCA member
                </label>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full px-6 py-4 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Creating Account...
                  </>
                ) : (
                  <>
                    Join YMCA Volunteers <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <p className="text-xs text-gray-500 mt-4 text-center">
              By creating an account, you agree to our Terms of Service and Privacy Policy.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}