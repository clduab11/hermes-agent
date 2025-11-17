import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { User, Habit, HabitEntry, Achievement, UserAchievement, SocialPost, Challenge, Notification } from '../types';

interface AppState {
  // User state
  user: User | null;
  setUser: (user: User | null) => void;

  // Habits state
  habits: Habit[];
  setHabits: (habits: Habit[]) => void;
  addHabit: (habit: Habit) => void;
  updateHabit: (id: string, updates: Partial<Habit>) => void;
  deleteHabit: (id: string) => void;

  // Habit entries state
  entries: HabitEntry[];
  setEntries: (entries: HabitEntry[]) => void;
  addEntry: (entry: HabitEntry) => void;

  // Achievements state
  achievements: Achievement[];
  userAchievements: UserAchievement[];
  setAchievements: (achievements: Achievement[]) => void;
  setUserAchievements: (userAchievements: UserAchievement[]) => void;

  // Social state
  socialFeed: SocialPost[];
  setSocialFeed: (posts: SocialPost[]) => void;
  addPost: (post: SocialPost) => void;

  // Challenges state
  challenges: Challenge[];
  setChallenges: (challenges: Challenge[]) => void;

  // Notifications state
  notifications: Notification[];
  setNotifications: (notifications: Notification[]) => void;
  markNotificationRead: (id: string) => void;

  // UI state
  selectedDate: Date;
  setSelectedDate: (date: Date) => void;
  viewMode: 'list' | 'grid' | 'calendar';
  setViewMode: (mode: 'list' | 'grid' | 'calendar') => void;

  // Loading states
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export const useStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        user: null,
        habits: [],
        entries: [],
        achievements: [],
        userAchievements: [],
        socialFeed: [],
        challenges: [],
        notifications: [],
        selectedDate: new Date(),
        viewMode: 'list',
        isLoading: false,

        // User actions
        setUser: (user) => set({ user }),

        // Habits actions
        setHabits: (habits) => set({ habits }),
        addHabit: (habit) => set((state) => ({ habits: [...state.habits, habit] })),
        updateHabit: (id, updates) =>
          set((state) => ({
            habits: state.habits.map((h) => (h.id === id ? { ...h, ...updates } : h)),
          })),
        deleteHabit: (id) =>
          set((state) => ({
            habits: state.habits.filter((h) => h.id !== id),
          })),

        // Entries actions
        setEntries: (entries) => set({ entries }),
        addEntry: (entry) => set((state) => ({ entries: [...state.entries, entry] })),

        // Achievements actions
        setAchievements: (achievements) => set({ achievements }),
        setUserAchievements: (userAchievements) => set({ userAchievements }),

        // Social actions
        setSocialFeed: (socialFeed) => set({ socialFeed }),
        addPost: (post) => set((state) => ({ socialFeed: [post, ...state.socialFeed] })),

        // Challenges actions
        setChallenges: (challenges) => set({ challenges }),

        // Notifications actions
        setNotifications: (notifications) => set({ notifications }),
        markNotificationRead: (id) =>
          set((state) => ({
            notifications: state.notifications.map((n) =>
              n.id === id ? { ...n, read: true } : n
            ),
          })),

        // UI actions
        setSelectedDate: (selectedDate) => set({ selectedDate }),
        setViewMode: (viewMode) => set({ viewMode }),

        // Loading actions
        setIsLoading: (isLoading) => set({ isLoading }),
      }),
      {
        name: 'habit-tracker-storage',
        partialize: (state) => ({
          user: state.user,
          selectedDate: state.selectedDate,
          viewMode: state.viewMode,
        }),
      }
    )
  )
);
