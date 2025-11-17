// Subscription & Billing Types

export type SubscriptionTier = 'free' | 'pro' | 'premium' | 'enterprise';

export type SubscriptionStatus = 'active' | 'canceled' | 'past_due' | 'trialing' | 'paused';

export interface Subscription {
  id: string;
  userId: string;
  stripeCustomerId?: string;
  stripeSubscriptionId?: string;
  tier: SubscriptionTier;
  status: SubscriptionStatus;
  currentPeriodStart?: Date;
  currentPeriodEnd?: Date;
  cancelAtPeriodEnd: boolean;
  canceledAt?: Date;
  trialStart?: Date;
  trialEnd?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface TierLimits {
  id: string;
  tier: SubscriptionTier;
  maxHabits: number | null; // null = unlimited
  analyticsHistoryDays: number | null; // null = unlimited
  aiRecommendationsPerMonth: number | null; // null = unlimited
  canPostSocial: boolean;
  canCreateChallenges: boolean;
  canExportData: boolean;
  canUseCustomCategories: boolean;
  canAccessApi: boolean;
}

export interface UsageTracking {
  id: string;
  userId: string;
  metric: string;
  count: number;
  periodStart: Date;
  periodEnd: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface PaymentHistory {
  id: string;
  userId: string;
  stripePaymentIntentId?: string;
  stripeInvoiceId?: string;
  amount: number;
  currency: string;
  status: 'succeeded' | 'failed' | 'pending' | 'refunded';
  description?: string;
  createdAt: Date;
}

export interface ReferralCode {
  id: string;
  userId: string;
  code: string;
  uses: number;
  maxUses?: number; // undefined = unlimited
  rewardMonths: number;
  expiresAt?: Date;
  createdAt: Date;
}

export interface PricingPlan {
  id: string;
  name: string;
  tier: SubscriptionTier;
  price: {
    monthly: number;
    annual: number;
  };
  stripePriceIds: {
    monthly: string;
    annual: string;
  };
  features: string[];
  highlighted?: boolean;
  buttonText: string;
  popular?: boolean;
}

export const PRICING_PLANS: PricingPlan[] = [
  {
    id: 'free',
    name: 'Starter',
    tier: 'free',
    price: {
      monthly: 0,
      annual: 0,
    },
    stripePriceIds: {
      monthly: '',
      annual: '',
    },
    features: [
      'Up to 3 active habits',
      'Basic streak tracking',
      '30-day analytics history',
      'Public profile',
      'Social feed (view only)',
      'Community features',
    ],
    buttonText: 'Get Started Free',
  },
  {
    id: 'pro',
    name: 'Achiever',
    tier: 'pro',
    price: {
      monthly: 9.99,
      annual: 99,
    },
    stripePriceIds: {
      monthly: 'price_habitflow_pro_monthly',
      annual: 'price_habitflow_pro_annual',
    },
    features: [
      'Unlimited habits',
      '10 AI recommendations/month',
      'Unlimited analytics history',
      'Custom categories & icons',
      'Data export (CSV/JSON)',
      'Social posting & engagement',
      'Join challenges',
      'Ad-free experience',
      'Priority support',
    ],
    highlighted: true,
    popular: true,
    buttonText: 'Start 14-Day Free Trial',
  },
  {
    id: 'premium',
    name: 'Champion',
    tier: 'premium',
    price: {
      monthly: 19.99,
      annual: 199,
    },
    stripePriceIds: {
      monthly: 'price_habitflow_premium_monthly',
      annual: 'price_habitflow_premium_annual',
    },
    features: [
      'Everything in Pro',
      'Unlimited AI recommendations',
      'AI coaching sessions',
      'Create custom challenges',
      'Private accountability groups',
      'Advanced habit stacking',
      'Habit correlation analysis',
      'API access',
      'White-label option',
      'Dedicated account manager',
    ],
    buttonText: 'Start 14-Day Free Trial',
  },
];

export const TIER_FEATURES = {
  free: {
    maxHabits: 3,
    analyticsHistory: 30,
    aiRecommendations: 0,
    socialPosting: false,
    createChallenges: false,
    dataExport: false,
    customCategories: false,
    apiAccess: false,
  },
  pro: {
    maxHabits: Infinity,
    analyticsHistory: Infinity,
    aiRecommendations: 10,
    socialPosting: true,
    createChallenges: false,
    dataExport: true,
    customCategories: true,
    apiAccess: false,
  },
  premium: {
    maxHabits: Infinity,
    analyticsHistory: Infinity,
    aiRecommendations: Infinity,
    socialPosting: true,
    createChallenges: true,
    dataExport: true,
    customCategories: true,
    apiAccess: true,
  },
  enterprise: {
    maxHabits: Infinity,
    analyticsHistory: Infinity,
    aiRecommendations: Infinity,
    socialPosting: true,
    createChallenges: true,
    dataExport: true,
    customCategories: true,
    apiAccess: true,
  },
};
