// Core Types for Habit Tracking Platform

export interface User {
  id: string;
  email: string;
  username: string;
  displayName: string;
  avatar?: string;
  bio?: string;
  level: number;
  totalPoints: number;
  currentStreak: number;
  longestStreak: number;
  joinedAt: Date;
  settings: UserSettings;
}

export interface UserSettings {
  notificationsEnabled: boolean;
  dailyReminderTime?: string;
  theme: 'light' | 'dark' | 'auto';
  privacyMode: 'public' | 'friends' | 'private';
}

export interface Habit {
  id: string;
  userId: string;
  title: string;
  description?: string;
  category: HabitCategory;
  frequency: HabitFrequency;
  color: string;
  icon?: string;
  goalValue?: number;
  goalUnit?: string;
  reminderTime?: string;
  isArchived: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export type HabitCategory =
  | 'health'
  | 'fitness'
  | 'productivity'
  | 'mindfulness'
  | 'learning'
  | 'social'
  | 'creativity'
  | 'finance'
  | 'other';

export interface HabitFrequency {
  type: 'daily' | 'weekly' | 'custom';
  customDays?: number[]; // 0 = Sunday, 1 = Monday, etc.
  timesPerDay?: number;
  timesPerWeek?: number;
}

export interface HabitEntry {
  id: string;
  habitId: string;
  userId: string;
  completedAt: Date;
  value?: number; // For trackable habits (e.g., 30 minutes of exercise)
  note?: string;
  mood?: 'great' | 'good' | 'okay' | 'poor';
}

export interface HabitStreak {
  habitId: string;
  currentStreak: number;
  longestStreak: number;
  lastCompletedDate?: Date;
  totalCompletions: number;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  category: 'streak' | 'consistency' | 'variety' | 'social' | 'special';
  requirement: number;
  points: number;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
}

export interface UserAchievement {
  id: string;
  userId: string;
  achievementId: string;
  unlockedAt: Date;
  shared: boolean;
}

export interface Challenge {
  id: string;
  title: string;
  description: string;
  category: HabitCategory;
  startDate: Date;
  endDate: Date;
  goal: number;
  participants: number;
  reward: number; // Points
  createdBy: string;
  isPublic: boolean;
}

export interface ChallengeParticipant {
  id: string;
  challengeId: string;
  userId: string;
  progress: number;
  joinedAt: Date;
  completedAt?: Date;
}

export interface SocialPost {
  id: string;
  userId: string;
  type: 'achievement' | 'streak' | 'challenge' | 'milestone' | 'general';
  content: string;
  metadata?: {
    achievementId?: string;
    habitId?: string;
    streakCount?: number;
    challengeId?: string;
  };
  likes: number;
  comments: number;
  createdAt: Date;
}

export interface Comment {
  id: string;
  postId: string;
  userId: string;
  content: string;
  createdAt: Date;
}

export interface Friendship {
  id: string;
  userId: string;
  friendId: string;
  status: 'pending' | 'accepted' | 'blocked';
  createdAt: Date;
  acceptedAt?: Date;
}

export interface Leaderboard {
  userId: string;
  username: string;
  displayName: string;
  avatar?: string;
  points: number;
  level: number;
  rank: number;
  currentStreak: number;
}

export interface AIRecommendation {
  id: string;
  userId: string;
  type: 'habit' | 'time' | 'strategy' | 'motivation';
  content: string;
  confidence: number;
  metadata?: {
    suggestedHabit?: string;
    optimalTime?: string;
    reason?: string;
  };
  createdAt: Date;
  dismissed: boolean;
}

export interface Analytics {
  userId: string;
  period: 'week' | 'month' | 'year' | 'all';
  completionRate: number;
  totalCompletions: number;
  activeHabits: number;
  bestStreak: number;
  pointsEarned: number;
  bestDays: string[]; // Day names
  worstDays: string[];
  categoryBreakdown: Record<HabitCategory, number>;
  trends: TrendData[];
}

export interface TrendData {
  date: string;
  completions: number;
  points: number;
  streak: number;
}

export interface Notification {
  id: string;
  userId: string;
  type: 'reminder' | 'achievement' | 'social' | 'challenge' | 'milestone';
  title: string;
  message: string;
  read: boolean;
  actionUrl?: string;
  createdAt: Date;
}
