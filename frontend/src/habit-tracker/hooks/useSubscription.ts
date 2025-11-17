import { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { subscriptionApi, usageApi } from '../services/subscriptionApi';
import type { Subscription, SubscriptionTier } from '../types/subscription';
import { TIER_FEATURES } from '../types/subscription';

export const useSubscription = () => {
  const { user } = useStore();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadSubscription();
    }
  }, [user]);

  const loadSubscription = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const sub = await subscriptionApi.getSubscription(user.id);
      setSubscription(sub);
    } catch (error) {
      console.error('Failed to load subscription:', error);
    } finally {
      setLoading(false);
    }
  };

  const tier = subscription?.tier || 'free';
  const status = subscription?.status || 'active';
  const features = TIER_FEATURES[tier];

  return {
    subscription,
    tier,
    status,
    features,
    loading,
    reload: loadSubscription,
    isPro: tier === 'pro' || tier === 'premium' || tier === 'enterprise',
    isPremium: tier === 'premium' || tier === 'enterprise',
    isEnterprise: tier === 'enterprise',
    isFree: tier === 'free',
  };
};

export const useFeatureAccess = (feature: string) => {
  const { user } = useStore();
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      checkAccess();
    }
  }, [user, feature]);

  const checkAccess = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const access = await subscriptionApi.hasFeatureAccess(user.id, feature);
      setHasAccess(access);
    } catch (error) {
      console.error('Failed to check feature access:', error);
      setHasAccess(false);
    } finally {
      setLoading(false);
    }
  };

  return { hasAccess, loading };
};

export const useHabitLimits = () => {
  const { user } = useStore();
  const { features } = useSubscription();
  const [remainingSlots, setRemainingSlots] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      checkLimits();
    }
  }, [user]);

  const checkLimits = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const slots = await subscriptionApi.getRemainingHabitSlots(user.id);
      setRemainingSlots(slots);
    } catch (error) {
      console.error('Failed to check habit limits:', error);
    } finally {
      setLoading(false);
    }
  };

  const canCreateHabit = remainingSlots > 0 || features.maxHabits === Infinity;

  return {
    maxHabits: features.maxHabits,
    remainingSlots,
    canCreateHabit,
    loading,
    reload: checkLimits,
  };
};

export const useUsageTracking = (metric: string) => {
  const { user } = useStore();
  const { features } = useSubscription();
  const [currentUsage, setCurrentUsage] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadUsage();
    }
  }, [user, metric]);

  const loadUsage = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const usage = await usageApi.getCurrentUsage(user.id, metric);
      setCurrentUsage(usage);
    } catch (error) {
      console.error('Failed to load usage:', error);
    } finally {
      setLoading(false);
    }
  };

  const trackUsage = async (increment: number = 1) => {
    if (!user) return false;

    try {
      // Check if within limits first
      const limit = getLimit();
      if (limit !== null && currentUsage >= limit) {
        return false; // Over limit
      }

      await usageApi.trackUsage(user.id, metric, increment);
      setCurrentUsage(prev => prev + increment);
      return true;
    } catch (error) {
      console.error('Failed to track usage:', error);
      return false;
    }
  };

  const getLimit = (): number | null => {
    switch (metric) {
      case 'ai_recommendations':
        return features.aiRecommendations === Infinity ? null : features.aiRecommendations;
      default:
        return null;
    }
  };

  const limit = getLimit();
  const isWithinLimits = limit === null || currentUsage < limit;
  const percentage = limit ? Math.min(100, (currentUsage / limit) * 100) : 0;

  return {
    currentUsage,
    limit,
    isWithinLimits,
    percentage,
    trackUsage,
    loading,
    reload: loadUsage,
  };
};
