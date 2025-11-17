-- Habit Tracking Platform Database Schema
-- PostgreSQL / Supabase

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    avatar TEXT,
    bio TEXT,
    level INTEGER DEFAULT 1,
    total_points INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    settings JSONB DEFAULT '{"notificationsEnabled": true, "theme": "auto", "privacyMode": "public"}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habits table
CREATE TABLE IF NOT EXISTS public.habits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    frequency JSONB NOT NULL,
    color TEXT DEFAULT '#6366f1',
    icon TEXT,
    goal_value INTEGER,
    goal_unit TEXT,
    reminder_time TIME,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habit entries (completions)
CREATE TABLE IF NOT EXISTS public.habit_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    habit_id UUID NOT NULL REFERENCES public.habits(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    value INTEGER,
    note TEXT,
    mood TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Achievements
CREATE TABLE IF NOT EXISTS public.achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    icon TEXT NOT NULL,
    category TEXT NOT NULL,
    requirement INTEGER NOT NULL,
    points INTEGER NOT NULL,
    rarity TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User achievements
CREATE TABLE IF NOT EXISTS public.user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES public.achievements(id) ON DELETE CASCADE,
    unlocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    shared BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, achievement_id)
);

-- Challenges
CREATE TABLE IF NOT EXISTS public.challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    goal INTEGER NOT NULL,
    reward INTEGER NOT NULL,
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Challenge participants
CREATE TABLE IF NOT EXISTS public.challenge_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    challenge_id UUID NOT NULL REFERENCES public.challenges(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(challenge_id, user_id)
);

-- Social posts
CREATE TABLE IF NOT EXISTS public.social_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Post likes
CREATE TABLE IF NOT EXISTS public.post_likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES public.social_posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(post_id, user_id)
);

-- Comments
CREATE TABLE IF NOT EXISTS public.comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES public.social_posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Friendships
CREATE TABLE IF NOT EXISTS public.friendships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    friend_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, friend_id),
    CHECK (user_id != friend_id)
);

-- AI recommendations
CREATE TABLE IF NOT EXISTS public.ai_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence DECIMAL(3,2),
    metadata JSONB,
    dismissed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notifications
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    action_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_habits_user_id ON public.habits(user_id);
CREATE INDEX IF NOT EXISTS idx_habit_entries_habit_id ON public.habit_entries(habit_id);
CREATE INDEX IF NOT EXISTS idx_habit_entries_user_id ON public.habit_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_habit_entries_completed_at ON public.habit_entries(completed_at);
CREATE INDEX IF NOT EXISTS idx_social_posts_user_id ON public.social_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_social_posts_created_at ON public.social_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_friendships_user_id ON public.friendships(user_id);
CREATE INDEX IF NOT EXISTS idx_friendships_friend_id ON public.friendships(friend_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_challenge_participants_challenge_id ON public.challenge_participants(challenge_id);

-- Row Level Security (RLS) Policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.habit_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.challenge_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.social_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.post_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.friendships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can read public profiles, update their own
CREATE POLICY "Public profiles are viewable by everyone" ON public.profiles
    FOR SELECT USING (true);

CREATE POLICY "Users can update their own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Habits: Users can only see and modify their own habits
CREATE POLICY "Users can view their own habits" ON public.habits
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own habits" ON public.habits
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own habits" ON public.habits
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own habits" ON public.habits
    FOR DELETE USING (auth.uid() = user_id);

-- Habit entries: Users can only see and modify their own entries
CREATE POLICY "Users can view their own habit entries" ON public.habit_entries
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own habit entries" ON public.habit_entries
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own habit entries" ON public.habit_entries
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own habit entries" ON public.habit_entries
    FOR DELETE USING (auth.uid() = user_id);

-- Social posts: Everyone can read, users can create/update/delete their own
CREATE POLICY "Social posts are viewable by everyone" ON public.social_posts
    FOR SELECT USING (true);

CREATE POLICY "Users can create their own posts" ON public.social_posts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own posts" ON public.social_posts
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own posts" ON public.social_posts
    FOR DELETE USING (auth.uid() = user_id);

-- Functions
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, username, display_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', 'user_' || SUBSTR(NEW.id::text, 1, 8)),
        COALESCE(NEW.raw_user_meta_data->>'display_name', 'New User')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on user signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to calculate streak
CREATE OR REPLACE FUNCTION public.calculate_habit_streak(p_habit_id UUID, p_user_id UUID)
RETURNS TABLE(current_streak INT, longest_streak INT, total_completions BIGINT) AS $$
DECLARE
    v_current_streak INT := 0;
    v_longest_streak INT := 0;
    v_temp_streak INT := 0;
    v_prev_date DATE;
    v_current_date DATE;
BEGIN
    -- Get all completion dates for the habit
    FOR v_current_date IN
        SELECT DATE(completed_at) as completion_date
        FROM public.habit_entries
        WHERE habit_id = p_habit_id AND user_id = p_user_id
        ORDER BY completed_at DESC
    LOOP
        IF v_prev_date IS NULL THEN
            v_temp_streak := 1;
        ELSIF v_current_date = v_prev_date - INTERVAL '1 day' THEN
            v_temp_streak := v_temp_streak + 1;
        ELSE
            IF v_prev_date = CURRENT_DATE OR v_prev_date = CURRENT_DATE - INTERVAL '1 day' THEN
                v_current_streak := v_temp_streak;
            END IF;
            IF v_temp_streak > v_longest_streak THEN
                v_longest_streak := v_temp_streak;
            END IF;
            v_temp_streak := 1;
        END IF;
        v_prev_date := v_current_date;
    END LOOP;

    -- Final check
    IF v_temp_streak > v_longest_streak THEN
        v_longest_streak := v_temp_streak;
    END IF;

    IF v_prev_date = CURRENT_DATE OR v_prev_date = CURRENT_DATE - INTERVAL '1 day' THEN
        v_current_streak := v_temp_streak;
    END IF;

    -- Get total completions
    SELECT COUNT(*) INTO total_completions
    FROM public.habit_entries
    WHERE habit_id = p_habit_id AND user_id = p_user_id;

    RETURN QUERY SELECT v_current_streak, v_longest_streak, total_completions;
END;
$$ LANGUAGE plpgsql;

-- Seed some achievements
INSERT INTO public.achievements (title, description, icon, category, requirement, points, rarity) VALUES
    ('First Step', 'Complete your first habit', '🎯', 'consistency', 1, 10, 'common'),
    ('Week Warrior', 'Maintain a 7-day streak', '🔥', 'streak', 7, 50, 'common'),
    ('Month Master', 'Maintain a 30-day streak', '💪', 'streak', 30, 200, 'rare'),
    ('Century Club', 'Maintain a 100-day streak', '👑', 'streak', 100, 1000, 'epic'),
    ('Legendary', 'Maintain a 365-day streak', '⭐', 'streak', 365, 5000, 'legendary'),
    ('Social Butterfly', 'Share 10 achievements', '🦋', 'social', 10, 100, 'common'),
    ('Habit Collector', 'Create 5 different habits', '📚', 'variety', 5, 75, 'common'),
    ('Consistency King', 'Complete habits 30 days in a row', '👑', 'consistency', 30, 250, 'rare'),
    ('Early Bird', 'Complete a habit before 8 AM', '🌅', 'special', 1, 25, 'common'),
    ('Night Owl', 'Complete a habit after 10 PM', '🦉', 'special', 1, 25, 'common')
ON CONFLICT DO NOTHING;
