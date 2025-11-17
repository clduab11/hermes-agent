import supabase from './supabase';
import type { Habit, HabitEntry, User, Challenge, SocialPost, Achievement, UserAchievement, Friendship, AIRecommendation, Notification } from '../types';

/**
 * Habits API
 */
export const habitsApi = {
  // Get all habits for the current user
  async getHabits(userId: string): Promise<Habit[]> {
    const { data, error } = await supabase
      .from('habits')
      .select('*')
      .eq('user_id', userId)
      .eq('is_archived', false)
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  },

  // Create a new habit
  async createHabit(habit: Omit<Habit, 'id' | 'createdAt' | 'updatedAt'>): Promise<Habit> {
    const { data, error } = await supabase
      .from('habits')
      .insert([{
        user_id: habit.userId,
        title: habit.title,
        description: habit.description,
        category: habit.category,
        frequency: habit.frequency,
        color: habit.color,
        icon: habit.icon,
        goal_value: habit.goalValue,
        goal_unit: habit.goalUnit,
        reminder_time: habit.reminderTime,
      }])
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Update a habit
  async updateHabit(id: string, updates: Partial<Habit>): Promise<Habit> {
    const { data, error } = await supabase
      .from('habits')
      .update({
        title: updates.title,
        description: updates.description,
        category: updates.category,
        frequency: updates.frequency,
        color: updates.color,
        icon: updates.icon,
        goal_value: updates.goalValue,
        goal_unit: updates.goalUnit,
        reminder_time: updates.reminderTime,
        is_archived: updates.isArchived,
        updated_at: new Date().toISOString(),
      })
      .eq('id', id)
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Delete a habit (soft delete by archiving)
  async deleteHabit(id: string): Promise<void> {
    const { error } = await supabase
      .from('habits')
      .update({ is_archived: true })
      .eq('id', id);

    if (error) throw error;
  },
};

/**
 * Habit Entries API
 */
export const entriesApi = {
  // Get entries for a habit
  async getEntries(habitId: string): Promise<HabitEntry[]> {
    const { data, error } = await supabase
      .from('habit_entries')
      .select('*')
      .eq('habit_id', habitId)
      .order('completed_at', { ascending: false });

    if (error) throw error;
    return data || [];
  },

  // Get all entries for a user
  async getUserEntries(userId: string, startDate?: Date, endDate?: Date): Promise<HabitEntry[]> {
    let query = supabase
      .from('habit_entries')
      .select('*')
      .eq('user_id', userId);

    if (startDate) {
      query = query.gte('completed_at', startDate.toISOString());
    }
    if (endDate) {
      query = query.lte('completed_at', endDate.toISOString());
    }

    const { data, error } = await query.order('completed_at', { ascending: false });

    if (error) throw error;
    return data || [];
  },

  // Create a habit entry (complete a habit)
  async createEntry(entry: Omit<HabitEntry, 'id' | 'createdAt'>): Promise<HabitEntry> {
    const { data, error } = await supabase
      .from('habit_entries')
      .insert([{
        habit_id: entry.habitId,
        user_id: entry.userId,
        completed_at: entry.completedAt || new Date().toISOString(),
        value: entry.value,
        note: entry.note,
        mood: entry.mood,
      }])
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Delete an entry
  async deleteEntry(id: string): Promise<void> {
    const { error } = await supabase
      .from('habit_entries')
      .delete()
      .eq('id', id);

    if (error) throw error;
  },
};

/**
 * User Profile API
 */
export const userApi = {
  // Get user profile
  async getProfile(userId: string): Promise<User | null> {
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single();

    if (error) throw error;
    return data;
  },

  // Update user profile
  async updateProfile(userId: string, updates: Partial<User>): Promise<User> {
    const { data, error } = await supabase
      .from('profiles')
      .update({
        username: updates.username,
        display_name: updates.displayName,
        avatar: updates.avatar,
        bio: updates.bio,
        settings: updates.settings,
        updated_at: new Date().toISOString(),
      })
      .eq('id', userId)
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Update user stats (points, level, streaks)
  async updateStats(userId: string, stats: { totalPoints?: number; level?: number; currentStreak?: number; longestStreak?: number }): Promise<void> {
    const { error } = await supabase
      .from('profiles')
      .update(stats)
      .eq('id', userId);

    if (error) throw error;
  },
};

/**
 * Achievements API
 */
export const achievementsApi = {
  // Get all achievements
  async getAchievements(): Promise<Achievement[]> {
    const { data, error } = await supabase
      .from('achievements')
      .select('*')
      .order('points', { ascending: true });

    if (error) throw error;
    return data || [];
  },

  // Get user achievements
  async getUserAchievements(userId: string): Promise<UserAchievement[]> {
    const { data, error } = await supabase
      .from('user_achievements')
      .select('*, achievements(*)')
      .eq('user_id', userId)
      .order('unlocked_at', { ascending: false });

    if (error) throw error;
    return data || [];
  },

  // Unlock achievement
  async unlockAchievement(userId: string, achievementId: string): Promise<UserAchievement> {
    const { data, error } = await supabase
      .from('user_achievements')
      .insert([{
        user_id: userId,
        achievement_id: achievementId,
      }])
      .select()
      .single();

    if (error) throw error;
    return data;
  },
};

/**
 * Challenges API
 */
export const challengesApi = {
  // Get active challenges
  async getActiveChallenges(): Promise<Challenge[]> {
    const now = new Date().toISOString();
    const { data, error } = await supabase
      .from('challenges')
      .select('*')
      .eq('is_public', true)
      .gte('end_date', now)
      .order('start_date', { ascending: true });

    if (error) throw error;
    return data || [];
  },

  // Join a challenge
  async joinChallenge(challengeId: string, userId: string): Promise<void> {
    const { error } = await supabase
      .from('challenge_participants')
      .insert([{
        challenge_id: challengeId,
        user_id: userId,
      }]);

    if (error) throw error;
  },

  // Update challenge progress
  async updateProgress(challengeId: string, userId: string, progress: number): Promise<void> {
    const { error } = await supabase
      .from('challenge_participants')
      .update({ progress })
      .eq('challenge_id', challengeId)
      .eq('user_id', userId);

    if (error) throw error;
  },

  // Get challenge leaderboard
  async getLeaderboard(challengeId: string): Promise<any[]> {
    const { data, error } = await supabase
      .from('challenge_participants')
      .select('*, profiles(username, display_name, avatar)')
      .eq('challenge_id', challengeId)
      .order('progress', { ascending: false })
      .limit(100);

    if (error) throw error;
    return data || [];
  },
};

/**
 * Social API
 */
export const socialApi = {
  // Get social feed
  async getFeed(userId: string, limit: number = 50): Promise<SocialPost[]> {
    // Get posts from user and their friends
    const { data, error } = await supabase
      .from('social_posts')
      .select('*, profiles(username, display_name, avatar)')
      .order('created_at', { ascending: false })
      .limit(limit);

    if (error) throw error;
    return data || [];
  },

  // Create a post
  async createPost(post: Omit<SocialPost, 'id' | 'createdAt' | 'likes' | 'comments'>): Promise<SocialPost> {
    const { data, error } = await supabase
      .from('social_posts')
      .insert([{
        user_id: post.userId,
        type: post.type,
        content: post.content,
        metadata: post.metadata,
      }])
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Like a post
  async likePost(postId: string, userId: string): Promise<void> {
    const { error } = await supabase
      .from('post_likes')
      .insert([{
        post_id: postId,
        user_id: userId,
      }]);

    if (error) {
      // Already liked
      if (error.code === '23505') return;
      throw error;
    }

    // Update like count
    await supabase.rpc('increment_post_likes', { post_id: postId });
  },

  // Get friends
  async getFriends(userId: string): Promise<any[]> {
    const { data, error } = await supabase
      .from('friendships')
      .select('*, profiles!friend_id(username, display_name, avatar)')
      .eq('user_id', userId)
      .eq('status', 'accepted');

    if (error) throw error;
    return data || [];
  },

  // Send friend request
  async sendFriendRequest(userId: string, friendId: string): Promise<void> {
    const { error } = await supabase
      .from('friendships')
      .insert([{
        user_id: userId,
        friend_id: friendId,
      }]);

    if (error) throw error;
  },
};

/**
 * AI Recommendations API
 */
export const aiApi = {
  // Get recommendations for user
  async getRecommendations(userId: string): Promise<AIRecommendation[]> {
    const { data, error } = await supabase
      .from('ai_recommendations')
      .select('*')
      .eq('user_id', userId)
      .eq('dismissed', false)
      .order('created_at', { ascending: false })
      .limit(10);

    if (error) throw error;
    return data || [];
  },

  // Generate AI recommendations (would call backend API)
  async generateRecommendations(userId: string, habits: Habit[], entries: HabitEntry[]): Promise<AIRecommendation[]> {
    // This would call your backend API that uses GPT-4
    const response = await fetch('/api/ai/recommendations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId, habits, entries }),
    });

    if (!response.ok) throw new Error('Failed to generate recommendations');
    return response.json();
  },

  // Dismiss a recommendation
  async dismissRecommendation(id: string): Promise<void> {
    const { error } = await supabase
      .from('ai_recommendations')
      .update({ dismissed: true })
      .eq('id', id);

    if (error) throw error;
  },
};

/**
 * Notifications API
 */
export const notificationsApi = {
  // Get notifications
  async getNotifications(userId: string): Promise<Notification[]> {
    const { data, error } = await supabase
      .from('notifications')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(50);

    if (error) throw error;
    return data || [];
  },

  // Mark as read
  async markAsRead(id: string): Promise<void> {
    const { error } = await supabase
      .from('notifications')
      .update({ read: true })
      .eq('id', id);

    if (error) throw error;
  },

  // Mark all as read
  async markAllAsRead(userId: string): Promise<void> {
    const { error } = await supabase
      .from('notifications')
      .update({ read: true })
      .eq('user_id', userId)
      .eq('read', false);

    if (error) throw error;
  },
};

/**
 * Analytics API
 */
export const analyticsApi = {
  // Get user analytics
  async getAnalytics(userId: string, period: 'week' | 'month' | 'year' = 'month') {
    // This would aggregate data from entries
    const endDate = new Date();
    let startDate = new Date();

    switch (period) {
      case 'week':
        startDate.setDate(endDate.getDate() - 7);
        break;
      case 'month':
        startDate.setMonth(endDate.getMonth() - 1);
        break;
      case 'year':
        startDate.setFullYear(endDate.getFullYear() - 1);
        break;
    }

    const entries = await entriesApi.getUserEntries(userId, startDate, endDate);
    const habits = await habitsApi.getHabits(userId);

    // Calculate analytics
    const totalCompletions = entries.length;
    const activeHabits = habits.filter(h => !h.isArchived).length;
    const completionRate = habits.length > 0 ? (totalCompletions / habits.length) * 100 : 0;

    // More detailed analytics would be calculated here
    return {
      userId,
      period,
      completionRate,
      totalCompletions,
      activeHabits,
      bestStreak: 0, // Would calculate from entries
      pointsEarned: totalCompletions * 10,
      bestDays: [],
      worstDays: [],
      categoryBreakdown: {},
      trends: [],
    };
  },
};
