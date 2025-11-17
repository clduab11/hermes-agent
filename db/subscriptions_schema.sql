-- Subscription & Billing Schema for HabitFlow
-- PostgreSQL / Supabase

-- Subscription tiers enum
CREATE TYPE subscription_tier AS ENUM ('free', 'pro', 'premium', 'enterprise');

-- Subscription status enum
CREATE TYPE subscription_status AS ENUM ('active', 'canceled', 'past_due', 'trialing', 'paused');

-- Subscriptions table
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT UNIQUE,
    tier subscription_tier NOT NULL DEFAULT 'free',
    status subscription_status NOT NULL DEFAULT 'active',
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Usage tracking table
CREATE TABLE IF NOT EXISTS public.usage_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    metric TEXT NOT NULL, -- 'habits_created', 'ai_recommendations_used', etc.
    count INTEGER DEFAULT 0,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payment history table
CREATE TABLE IF NOT EXISTS public.payment_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    stripe_payment_intent_id TEXT UNIQUE,
    stripe_invoice_id TEXT,
    amount DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'usd',
    status TEXT NOT NULL, -- 'succeeded', 'failed', 'pending', 'refunded'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature usage limits per tier
CREATE TABLE IF NOT EXISTS public.tier_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tier subscription_tier NOT NULL UNIQUE,
    max_habits INTEGER,
    analytics_history_days INTEGER,
    ai_recommendations_per_month INTEGER,
    can_post_social BOOLEAN DEFAULT FALSE,
    can_create_challenges BOOLEAN DEFAULT FALSE,
    can_export_data BOOLEAN DEFAULT FALSE,
    can_use_custom_categories BOOLEAN DEFAULT FALSE,
    can_access_api BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Referral codes table
CREATE TABLE IF NOT EXISTS public.referral_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    code TEXT UNIQUE NOT NULL,
    uses INTEGER DEFAULT 0,
    max_uses INTEGER DEFAULT NULL, -- NULL = unlimited
    reward_months INTEGER DEFAULT 1, -- How many free months both parties get
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Referral redemptions table
CREATE TABLE IF NOT EXISTS public.referral_redemptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referrer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    referee_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    referral_code_id UUID NOT NULL REFERENCES public.referral_codes(id) ON DELETE CASCADE,
    reward_applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(referee_id) -- Each user can only use one referral code
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer_id ON public.subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_id ON public.usage_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_metric ON public.usage_tracking(metric);
CREATE INDEX IF NOT EXISTS idx_payment_history_user_id ON public.payment_history(user_id);
CREATE INDEX IF NOT EXISTS idx_referral_codes_code ON public.referral_codes(code);

-- Row Level Security
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_redemptions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own subscription" ON public.subscriptions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own usage" ON public.usage_tracking
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own payment history" ON public.payment_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own referral codes" ON public.referral_codes
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own referral codes" ON public.referral_codes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Seed tier limits
INSERT INTO public.tier_limits (tier, max_habits, analytics_history_days, ai_recommendations_per_month, can_post_social, can_create_challenges, can_export_data, can_use_custom_categories, can_access_api) VALUES
    ('free', 3, 30, 0, FALSE, FALSE, FALSE, FALSE, FALSE),
    ('pro', NULL, NULL, 10, TRUE, FALSE, TRUE, TRUE, FALSE),
    ('premium', NULL, NULL, NULL, TRUE, TRUE, TRUE, TRUE, TRUE),
    ('enterprise', NULL, NULL, NULL, TRUE, TRUE, TRUE, TRUE, TRUE)
ON CONFLICT (tier) DO NOTHING;

-- Function to create free subscription for new users
CREATE OR REPLACE FUNCTION public.create_free_subscription()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.subscriptions (user_id, tier, status)
    VALUES (NEW.id, 'free', 'active');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create subscription on user signup
DROP TRIGGER IF EXISTS on_user_created_subscription ON public.profiles;
CREATE TRIGGER on_user_created_subscription
    AFTER INSERT ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.create_free_subscription();

-- Function to check feature access
CREATE OR REPLACE FUNCTION public.has_feature_access(
    p_user_id UUID,
    p_feature TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_tier subscription_tier;
    v_has_access BOOLEAN;
BEGIN
    -- Get user's tier
    SELECT tier INTO v_tier
    FROM public.subscriptions
    WHERE user_id = p_user_id AND status IN ('active', 'trialing');

    IF v_tier IS NULL THEN
        v_tier := 'free';
    END IF;

    -- Check feature access based on tier
    CASE p_feature
        WHEN 'social_posting' THEN
            SELECT can_post_social INTO v_has_access FROM public.tier_limits WHERE tier = v_tier;
        WHEN 'create_challenges' THEN
            SELECT can_create_challenges INTO v_has_access FROM public.tier_limits WHERE tier = v_tier;
        WHEN 'data_export' THEN
            SELECT can_export_data INTO v_has_access FROM public.tier_limits WHERE tier = v_tier;
        WHEN 'custom_categories' THEN
            SELECT can_use_custom_categories INTO v_has_access FROM public.tier_limits WHERE tier = v_tier;
        WHEN 'api_access' THEN
            SELECT can_access_api INTO v_has_access FROM public.tier_limits WHERE tier = v_tier;
        ELSE
            v_has_access := FALSE;
    END CASE;

    RETURN COALESCE(v_has_access, FALSE);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get remaining habit slots
CREATE OR REPLACE FUNCTION public.get_remaining_habit_slots(p_user_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_tier subscription_tier;
    v_max_habits INTEGER;
    v_current_habits INTEGER;
BEGIN
    -- Get user's tier and max habits
    SELECT s.tier, tl.max_habits INTO v_tier, v_max_habits
    FROM public.subscriptions s
    JOIN public.tier_limits tl ON tl.tier = s.tier
    WHERE s.user_id = p_user_id AND s.status IN ('active', 'trialing');

    IF v_max_habits IS NULL THEN
        RETURN 999999; -- Unlimited
    END IF;

    -- Get current habit count
    SELECT COUNT(*) INTO v_current_habits
    FROM public.habits
    WHERE user_id = p_user_id AND is_archived = FALSE;

    RETURN GREATEST(0, v_max_habits - v_current_habits);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to track usage
CREATE OR REPLACE FUNCTION public.track_usage(
    p_user_id UUID,
    p_metric TEXT,
    p_increment INTEGER DEFAULT 1
)
RETURNS VOID AS $$
DECLARE
    v_period_start TIMESTAMP WITH TIME ZONE;
    v_period_end TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Calculate current period (monthly)
    v_period_start := DATE_TRUNC('month', NOW());
    v_period_end := v_period_start + INTERVAL '1 month';

    -- Upsert usage tracking
    INSERT INTO public.usage_tracking (user_id, metric, count, period_start, period_end)
    VALUES (p_user_id, p_metric, p_increment, v_period_start, v_period_end)
    ON CONFLICT (user_id, metric, period_start)
    DO UPDATE SET
        count = public.usage_tracking.count + p_increment,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create unique constraint for usage tracking
CREATE UNIQUE INDEX IF NOT EXISTS idx_usage_tracking_unique
ON public.usage_tracking(user_id, metric, period_start);
