"""
Referral System for YMCA Volunteer PathFinder
Handles referral links, tracking, and rewards
"""
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from enum import Enum

class ReferralStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    EXPIRED = "expired"

class RewardType(Enum):
    VOLUNTEER_HOURS = "volunteer_hours"
    YMCA_MEMBERSHIP_DISCOUNT = "membership_discount"
    RECOGNITION_BADGE = "recognition_badge"
    GIFT_CARD = "gift_card"

class ReferralSystem:
    def __init__(self, database):
        self.database = database
        
    def generate_referral_code(self, user_id: str) -> str:
        """Generate a unique referral code for a user"""
        timestamp = str(int(datetime.now().timestamp()))
        random_part = secrets.token_urlsafe(8)
        data = f"{user_id}:{timestamp}:{random_part}"
        
        # Create a hash and take first 8 characters for readability
        hash_object = hashlib.sha256(data.encode())
        referral_code = hash_object.hexdigest()[:8].upper()
        
        return referral_code
    
    def generate_invite_link(self, user_id: str, referral_code: str, base_url: str = "https://ymca-volunteer-pathfinder.com") -> str:
        """Generate a unique invite link"""
        return f"{base_url}/join?ref={referral_code}"
    
    async def create_referral_link(self, user_id: str, expires_in_days: int = 30) -> Dict[str, Any]:
        """Create a new referral link for a user"""
        try:
            referral_code = self.generate_referral_code(user_id)
            expiry_date = datetime.now() + timedelta(days=expires_in_days)
            
            referral_data = {
                'user_id': user_id,
                'referral_code': referral_code,
                'invite_link': self.generate_invite_link(user_id, referral_code),
                'expires_at': expiry_date.isoformat(),
                'status': ReferralStatus.PENDING.value,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Save to database
            result = self.database.supabase.table('referral_links').insert(referral_data).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"❌ Error creating referral link: {e}")
            return None
    
    async def validate_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Validate a referral code and return referral info if valid"""
        try:
            result = self.database.supabase.table('referral_links')\
                .select('*')\
                .eq('referral_code', referral_code)\
                .eq('status', ReferralStatus.PENDING.value)\
                .execute()
            
            if result.data:
                referral = result.data[0]
                expiry_date = datetime.fromisoformat(referral['expires_at'].replace('Z', '+00:00'))
                
                if datetime.now(expiry_date.tzinfo) > expiry_date:
                    # Mark as expired
                    await self.expire_referral(referral['id'])
                    return None
                
                return referral
            return None
            
        except Exception as e:
            print(f"❌ Error validating referral code: {e}")
            return None
    
    async def track_referral_conversion(self, referral_code: str, new_user_id: str, 
                                      conversion_data: Dict[str, Any] = None) -> bool:
        """Track when a referral converts (new user signs up)"""
        try:
            # Validate referral code
            referral = await self.validate_referral_code(referral_code)
            if not referral:
                return False
            
            # Create conversion record
            conversion_record = {
                'referral_id': referral['id'],
                'referrer_user_id': referral['user_id'],
                'referred_user_id': new_user_id,
                'conversion_type': 'user_signup',
                'conversion_data': json.dumps(conversion_data or {}),
                'converted_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.database.supabase.table('referral_conversions').insert(conversion_record).execute()
            
            if result.data:
                # Update referral stats
                await self.update_referral_stats(referral['id'])
                
                # Check if referral should be marked as completed
                await self.check_referral_completion(referral['id'])
                
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error tracking conversion: {e}")
            return False
    
    async def track_volunteer_activity(self, user_id: str, activity_data: Dict[str, Any]) -> bool:
        """Track when a referred user volunteers (for reward calculation)"""
        try:
            # Check if user was referred
            referral_conversion = self.database.supabase.table('referral_conversions')\
                .select('*')\
                .eq('referred_user_id', user_id)\
                .execute()
            
            if referral_conversion.data:
                conversion = referral_conversion.data[0]
                
                # Track volunteer activity
                activity_record = {
                    'conversion_id': conversion['id'],
                    'referred_user_id': user_id,
                    'activity_type': 'volunteer_activity',
                    'activity_data': json.dumps(activity_data),
                    'activity_date': datetime.now().isoformat(),
                    'created_at': datetime.now().isoformat()
                }
                
                result = self.database.supabase.table('referral_activities').insert(activity_record).execute()
                
                if result.data:
                    # Check if this qualifies for rewards
                    await self.check_reward_eligibility(conversion['referral_id'])
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error tracking volunteer activity: {e}")
            return False
    
    async def calculate_rewards(self, referral_id: str) -> Dict[str, Any]:
        """Calculate rewards for a successful referral"""
        try:
            # Get referral details
            referral_result = self.database.supabase.table('referral_links')\
                .select('*')\
                .eq('id', referral_id)\
                .execute()
            
            if not referral_result.data:
                return {}
            
            referral = referral_result.data[0]
            
            # Get conversions
            conversions_result = self.database.supabase.table('referral_conversions')\
                .select('*')\
                .eq('referral_id', referral_id)\
                .execute()
            
            # Get volunteer activities
            activities_result = self.database.supabase.table('referral_activities')\
                .select('*')\
                .eq('conversion_id', 'ANY(SELECT id FROM referral_conversions WHERE referral_id = ?)', referral_id)\
                .execute()
            
            conversion_count = len(conversions_result.data) if conversions_result.data else 0
            activity_count = len(activities_result.data) if activities_result.data else 0
            
            rewards = []
            
            # Reward tiers
            if conversion_count >= 1:
                rewards.append({
                    'type': RewardType.RECOGNITION_BADGE.value,
                    'title': 'Volunteer Recruiter',
                    'description': 'Successfully referred someone to volunteer',
                    'value': None
                })
            
            if conversion_count >= 3:
                rewards.append({
                    'type': RewardType.VOLUNTEER_HOURS.value,
                    'title': 'Bonus Volunteer Hours',
                    'description': 'Extra volunteer hours credited to your record',
                    'value': 5
                })
            
            if conversion_count >= 5:
                rewards.append({
                    'type': RewardType.YMCA_MEMBERSHIP_DISCOUNT.value,
                    'title': 'YMCA Membership Discount',
                    'description': '10% off next membership renewal',
                    'value': 10
                })
            
            if activity_count >= 10:  # Referred users have volunteered 10+ times
                rewards.append({
                    'type': RewardType.GIFT_CARD.value,
                    'title': 'Gift Card Reward',
                    'description': '$25 gift card to local restaurant',
                    'value': 25
                })
            
            return {
                'referral_id': referral_id,
                'user_id': referral['user_id'],
                'conversion_count': conversion_count,
                'activity_count': activity_count,
                'rewards': rewards,
                'total_reward_value': sum(r.get('value', 0) for r in rewards if r.get('value'))
            }
            
        except Exception as e:
            print(f"❌ Error calculating rewards: {e}")
            return {}
    
    async def award_reward(self, user_id: str, reward_data: Dict[str, Any]) -> bool:
        """Award a reward to a user"""
        try:
            reward_record = {
                'user_id': user_id,
                'referral_id': reward_data.get('referral_id'),
                'reward_type': reward_data['type'],
                'reward_title': reward_data['title'],
                'reward_description': reward_data['description'],
                'reward_value': reward_data.get('value'),
                'status': 'awarded',
                'awarded_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.database.supabase.table('referral_rewards').insert(reward_record).execute()
            
            if result.data:
                # Track reward event
                await self.database.track_event(
                    'reward_awarded',
                    reward_data,
                    user_id
                )
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error awarding reward: {e}")
            return False
    
    async def get_user_referrals(self, user_id: str) -> Dict[str, Any]:
        """Get all referral data for a user"""
        try:
            # Get referral links
            links_result = self.database.supabase.table('referral_links')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            
            # Get conversions
            conversions_result = self.database.supabase.table('referral_conversions')\
                .select('*')\
                .eq('referrer_user_id', user_id)\
                .order('converted_at', desc=True)\
                .execute()
            
            # Get rewards
            rewards_result = self.database.supabase.table('referral_rewards')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('awarded_at', desc=True)\
                .execute()
            
            # Calculate total stats
            total_conversions = len(conversions_result.data) if conversions_result.data else 0
            total_rewards = len(rewards_result.data) if rewards_result.data else 0
            
            return {
                'referral_links': links_result.data or [],
                'conversions': conversions_result.data or [],
                'rewards': rewards_result.data or [],
                'stats': {
                    'total_links': len(links_result.data) if links_result.data else 0,
                    'total_conversions': total_conversions,
                    'total_rewards': total_rewards,
                    'active_links': len([l for l in (links_result.data or []) if l['status'] == 'pending'])
                }
            }
            
        except Exception as e:
            print(f"❌ Error getting user referrals: {e}")
            return {}
    
    async def get_referral_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get referral program analytics"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Total referral links created
            links_result = self.database.supabase.table('referral_links')\
                .select('id', count='exact')\
                .gte('created_at', start_date)\
                .execute()
            
            # Total conversions
            conversions_result = self.database.supabase.table('referral_conversions')\
                .select('id', count='exact')\
                .gte('converted_at', start_date)\
                .execute()
            
            # Total rewards awarded
            rewards_result = self.database.supabase.table('referral_rewards')\
                .select('id', count='exact')\
                .gte('awarded_at', start_date)\
                .execute()
            
            # Top referrers
            top_referrers_result = self.database.supabase.table('referral_conversions')\
                .select('referrer_user_id', count='exact')\
                .gte('converted_at', start_date)\
                .execute()
            
            conversion_rate = 0
            if links_result.count > 0:
                conversion_rate = (conversions_result.count / links_result.count) * 100
            
            return {
                'period_days': days,
                'total_links_created': links_result.count,
                'total_conversions': conversions_result.count,
                'total_rewards_awarded': rewards_result.count,
                'conversion_rate': round(conversion_rate, 2),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting referral analytics: {e}")
            return {}
    
    # Helper methods
    async def update_referral_stats(self, referral_id: str) -> bool:
        """Update referral link statistics"""
        try:
            # Count conversions
            conversions_result = self.database.supabase.table('referral_conversions')\
                .select('id', count='exact')\
                .eq('referral_id', referral_id)\
                .execute()
            
            # Update referral link
            result = self.database.supabase.table('referral_links')\
                .update({
                    'conversion_count': conversions_result.count,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', referral_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"❌ Error updating referral stats: {e}")
            return False
    
    async def check_referral_completion(self, referral_id: str) -> bool:
        """Check if referral should be marked as completed"""
        try:
            # For now, consider a referral completed after first conversion
            # This can be customized based on business rules
            result = self.database.supabase.table('referral_links')\
                .update({
                    'status': ReferralStatus.COMPLETED.value,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', referral_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"❌ Error checking referral completion: {e}")
            return False
    
    async def check_reward_eligibility(self, referral_id: str) -> bool:
        """Check if referral is eligible for rewards and award them"""
        try:
            rewards_data = await self.calculate_rewards(referral_id)
            
            if rewards_data and rewards_data.get('rewards'):
                user_id = rewards_data['user_id']
                
                # Award each eligible reward
                for reward in rewards_data['rewards']:
                    # Check if reward was already awarded
                    existing_reward = self.database.supabase.table('referral_rewards')\
                        .select('id')\
                        .eq('user_id', user_id)\
                        .eq('referral_id', referral_id)\
                        .eq('reward_type', reward['type'])\
                        .execute()
                    
                    if not existing_reward.data:
                        reward['referral_id'] = referral_id
                        await self.award_reward(user_id, reward)
                
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error checking reward eligibility: {e}")
            return False
    
    async def expire_referral(self, referral_id: str) -> bool:
        """Mark a referral as expired"""
        try:
            result = self.database.supabase.table('referral_links')\
                .update({
                    'status': ReferralStatus.EXPIRED.value,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', referral_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"❌ Error expiring referral: {e}")
            return False