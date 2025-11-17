import supabase from './supabase';
import type { Subscription, UsageTracking, PaymentHistory, ReferralCode, SubscriptionTier } from '../types/subscription';

/**
 * Subscription API
 */
export const subscriptionApi = {
  // Get user's subscription
  async getSubscription(userId: string): Promise<Subscription | null> {
    const { data, error } = await supabase
      .from('subscriptions')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error) {
      if (error.code === 'PGRST116') return null; // No subscription found
      throw error;
    }

    return data;
  },

  // Create or update subscription
  async upsertSubscription(subscription: Partial<Subscription>): Promise<Subscription> {
    const { data, error } = await supabase
      .from('subscriptions')
      .upsert({
        user_id: subscription.userId,
        stripe_customer_id: subscription.stripeCustomerId,
        stripe_subscription_id: subscription.stripeSubscriptionId,
        tier: subscription.tier,
        status: subscription.status,
        current_period_start: subscription.currentPeriodStart,
        current_period_end: subscription.currentPeriodEnd,
        cancel_at_period_end: subscription.cancelAtPeriodEnd,
        canceled_at: subscription.canceledAt,
        trial_start: subscription.trialStart,
        trial_end: subscription.trialEnd,
        updated_at: new Date().toISOString(),
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Check if user has feature access
  async hasFeatureAccess(userId: string, feature: string): Promise<boolean> {
    const { data, error } = await supabase.rpc('has_feature_access', {
      p_user_id: userId,
      p_feature: feature,
    });

    if (error) throw error;
    return data;
  },

  // Get remaining habit slots
  async getRemainingHabitSlots(userId: string): Promise<number> {
    const { data, error } = await supabase.rpc('get_remaining_habit_slots', {
      p_user_id: userId,
    });

    if (error) throw error;
    return data || 0;
  },

  // Check if user can create habit
  async canCreateHabit(userId: string): Promise<boolean> {
    const remaining = await subscriptionApi.getRemainingHabitSlots(userId);
    return remaining > 0;
  },

  // Upgrade to tier
  async upgradeTier(userId: string, tier: SubscriptionTier): Promise<Subscription> {
    const { data, error } = await supabase
      .from('subscriptions')
      .update({
        tier,
        status: 'active',
        updated_at: new Date().toISOString(),
      })
      .eq('user_id', userId)
      .select()
      .single();

    if (error) throw error;
    return data;
  },
};

/**
 * Usage Tracking API
 */
export const usageApi = {
  // Track usage
  async trackUsage(userId: string, metric: string, increment: number = 1): Promise<void> {
    const { error } = await supabase.rpc('track_usage', {
      p_user_id: userId,
      p_metric: metric,
      p_increment: increment,
    });

    if (error) throw error;
  },

  // Get usage for current period
  async getCurrentUsage(userId: string, metric: string): Promise<number> {
    const now = new Date();
    const periodStart = new Date(now.getFullYear(), now.getMonth(), 1);

    const { data, error } = await supabase
      .from('usage_tracking')
      .select('count')
      .eq('user_id', userId)
      .eq('metric', metric)
      .gte('period_start', periodStart.toISOString())
      .single();

    if (error) {
      if (error.code === 'PGRST116') return 0; // No usage yet
      throw error;
    }

    return data?.count || 0;
  },

  // Check if usage is within limits
  async isWithinLimits(userId: string, metric: string, limit: number | null): Promise<boolean> {
    if (limit === null) return true; // Unlimited

    const currentUsage = await usageApi.getCurrentUsage(userId, metric);
    return currentUsage < limit;
  },
};

/**
 * Payment History API
 */
export const paymentApi = {
  // Get payment history
  async getPaymentHistory(userId: string): Promise<PaymentHistory[]> {
    const { data, error } = await supabase
      .from('payment_history')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  },

  // Add payment record
  async addPayment(payment: Omit<PaymentHistory, 'id' | 'createdAt'>): Promise<PaymentHistory> {
    const { data, error } = await supabase
      .from('payment_history')
      .insert([{
        user_id: payment.userId,
        stripe_payment_intent_id: payment.stripePaymentIntentId,
        stripe_invoice_id: payment.stripeInvoiceId,
        amount: payment.amount,
        currency: payment.currency,
        status: payment.status,
        description: payment.description,
      }])
      .select()
      .single();

    if (error) throw error;
    return data;
  },
};

/**
 * Referral API
 */
export const referralApi = {
  // Generate referral code for user
  async generateReferralCode(userId: string): Promise<ReferralCode> {
    // Generate random code
    const code = `HABIT${Math.random().toString(36).substr(2, 6).toUpperCase()}`;

    const { data, error} = await supabase
      .from('referral_codes')
      .insert([{
        user_id: userId,
        code,
        reward_months: 1,
      }])
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Get user's referral code
  async getReferralCode(userId: string): Promise<ReferralCode | null> {
    const { data, error } = await supabase
      .from('referral_codes')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error) {
      if (error.code === 'PGRST116') return null; // No code yet
      throw error;
    }

    return data;
  },

  // Redeem referral code
  async redeemReferralCode(userId: string, code: string): Promise<void> {
    // Validate code exists
    const { data: referralCode, error: codeError } = await supabase
      .from('referral_codes')
      .select('*')
      .eq('code', code)
      .single();

    if (codeError) throw new Error('Invalid referral code');

    // Check if already redeemed
    const { data: existing } = await supabase
      .from('referral_redemptions')
      .select('*')
      .eq('referee_id', userId)
      .single();

    if (existing) throw new Error('You have already used a referral code');

    // Create redemption
    const { error: redemptionError } = await supabase
      .from('referral_redemptions')
      .insert([{
        referrer_id: referralCode.user_id,
        referee_id: userId,
        referral_code_id: referralCode.id,
      }]);

    if (redemptionError) throw redemptionError;

    // Update code usage count
    await supabase
      .from('referral_codes')
      .update({ uses: referralCode.uses + 1 })
      .eq('id', referralCode.id);
  },

  // Get referral stats
  async getReferralStats(userId: string): Promise<{ totalReferrals: number; rewardMonths: number }> {
    const { data, error } = await supabase
      .from('referral_redemptions')
      .select('*')
      .eq('referrer_id', userId);

    if (error) throw error;

    const totalReferrals = data?.length || 0;
    const rewardMonths = totalReferrals; // 1 month per referral

    return { totalReferrals, rewardMonths };
  },
};
