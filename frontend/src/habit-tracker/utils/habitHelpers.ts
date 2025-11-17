import { format, isToday, isYesterday, differenceInDays, startOfDay, endOfDay, eachDayOfInterval, isSameDay } from 'date-fns';
import type { Habit, HabitEntry, HabitFrequency, HabitStreak } from '../types';

/**
 * Calculate streak data for a habit
 */
export function calculateStreak(entries: HabitEntry[]): HabitStreak {
  if (entries.length === 0) {
    return {
      habitId: '',
      currentStreak: 0,
      longestStreak: 0,
      totalCompletions: 0,
    };
  }

  // Sort entries by date (newest first)
  const sortedEntries = [...entries].sort((a, b) =>
    new Date(b.completedAt).getTime() - new Date(a.completedAt).getTime()
  );

  const habitId = sortedEntries[0].habitId;
  let currentStreak = 0;
  let longestStreak = 0;
  let tempStreak = 0;
  let lastDate: Date | null = null;

  // Get unique dates (one completion per day)
  const uniqueDates = Array.from(
    new Set(sortedEntries.map(e => format(new Date(e.completedAt), 'yyyy-MM-dd')))
  ).map(dateStr => new Date(dateStr));

  // Calculate current streak
  for (let i = 0; i < uniqueDates.length; i++) {
    const currentDate = uniqueDates[i];

    if (i === 0) {
      // First date - check if it's today or yesterday
      if (isToday(currentDate) || isYesterday(currentDate)) {
        tempStreak = 1;
        lastDate = currentDate;
      } else {
        // Streak is broken
        break;
      }
    } else {
      // Check if consecutive day
      const daysDiff = differenceInDays(lastDate!, currentDate);
      if (daysDiff === 1) {
        tempStreak++;
        lastDate = currentDate;
      } else {
        break;
      }
    }
  }

  currentStreak = tempStreak;

  // Calculate longest streak
  tempStreak = 0;
  lastDate = null;

  for (const currentDate of uniqueDates) {
    if (lastDate === null) {
      tempStreak = 1;
    } else {
      const daysDiff = differenceInDays(lastDate, currentDate);
      if (daysDiff === 1) {
        tempStreak++;
      } else {
        longestStreak = Math.max(longestStreak, tempStreak);
        tempStreak = 1;
      }
    }
    lastDate = currentDate;
  }

  longestStreak = Math.max(longestStreak, tempStreak);

  return {
    habitId,
    currentStreak,
    longestStreak,
    lastCompletedDate: sortedEntries.length > 0 ? new Date(sortedEntries[0].completedAt) : undefined,
    totalCompletions: sortedEntries.length,
  };
}

/**
 * Check if a habit is completed on a specific date
 */
export function isHabitCompletedOnDate(entries: HabitEntry[], date: Date): boolean {
  return entries.some(entry => isSameDay(new Date(entry.completedAt), date));
}

/**
 * Get completion status for a date range
 */
export function getCompletionCalendar(entries: HabitEntry[], startDate: Date, endDate: Date): Map<string, boolean> {
  const calendar = new Map<string, boolean>();
  const days = eachDayOfInterval({ start: startDate, end: endDate });

  days.forEach(day => {
    const dateKey = format(day, 'yyyy-MM-dd');
    calendar.set(dateKey, isHabitCompletedOnDate(entries, day));
  });

  return calendar;
}

/**
 * Calculate completion rate for a habit
 */
export function calculateCompletionRate(habit: Habit, entries: HabitEntry[]): number {
  const createdDate = new Date(habit.createdAt);
  const today = new Date();
  const totalDays = differenceInDays(today, createdDate) + 1;

  if (totalDays === 0) return 0;

  const { type, customDays } = habit.frequency;

  let expectedCompletions = 0;

  if (type === 'daily') {
    expectedCompletions = totalDays;
  } else if (type === 'weekly' && habit.frequency.timesPerWeek) {
    const weeks = Math.ceil(totalDays / 7);
    expectedCompletions = weeks * habit.frequency.timesPerWeek;
  } else if (type === 'custom' && customDays) {
    // Count how many times the custom days occurred
    const days = eachDayOfInterval({ start: createdDate, end: today });
    expectedCompletions = days.filter(day => customDays.includes(day.getDay())).length;
  }

  const actualCompletions = entries.length;
  return expectedCompletions > 0 ? (actualCompletions / expectedCompletions) * 100 : 0;
}

/**
 * Check if a habit should be done today
 */
export function shouldDoToday(habit: Habit): boolean {
  const today = new Date().getDay(); // 0 = Sunday, 1 = Monday, etc.
  const { type, customDays } = habit.frequency;

  if (type === 'daily') {
    return true;
  } else if (type === 'custom' && customDays) {
    return customDays.includes(today);
  } else if (type === 'weekly') {
    // For weekly habits, we'll assume they can be done any day
    return true;
  }

  return false;
}

/**
 * Get habit color with opacity
 */
export function getHabitColor(color: string, opacity: number = 1): string {
  // Convert hex to rgba if needed
  if (color.startsWith('#')) {
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }
  return color;
}

/**
 * Format streak text
 */
export function formatStreakText(streak: number): string {
  if (streak === 0) return 'Start your streak!';
  if (streak === 1) return '1 day streak';
  return `${streak} day streak`;
}

/**
 * Get motivational message based on streak
 */
export function getMotivationalMessage(streak: number): string {
  if (streak === 0) return "Let's get started! 💪";
  if (streak < 7) return "Great start! Keep going! 🌟";
  if (streak < 30) return "You're on fire! 🔥";
  if (streak < 100) return "Unstoppable! 🚀";
  if (streak < 365) return "Legendary dedication! 👑";
  return "You're a habit master! ⭐";
}

/**
 * Calculate points earned from a habit completion
 */
export function calculatePoints(habit: Habit, streak: number): number {
  let basePoints = 10;

  // Bonus points for streak
  if (streak >= 7) basePoints += 5;
  if (streak >= 30) basePoints += 10;
  if (streak >= 100) basePoints += 25;

  // Bonus for difficulty (goal value)
  if (habit.goalValue && habit.goalValue > 30) {
    basePoints += 5;
  }

  return basePoints;
}

/**
 * Calculate user level from total points
 */
export function calculateLevel(totalPoints: number): number {
  // Level formula: level = floor(sqrt(points / 100))
  return Math.floor(Math.sqrt(totalPoints / 100)) + 1;
}

/**
 * Calculate points needed for next level
 */
export function pointsForNextLevel(currentLevel: number): number {
  return (currentLevel * currentLevel) * 100;
}

/**
 * Get category icon
 */
export function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    health: '❤️',
    fitness: '💪',
    productivity: '📈',
    mindfulness: '🧘',
    learning: '📚',
    social: '👥',
    creativity: '🎨',
    finance: '💰',
    other: '⭐',
  };
  return icons[category] || '⭐';
}

/**
 * Get category color
 */
export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    health: '#ef4444',
    fitness: '#f97316',
    productivity: '#3b82f6',
    mindfulness: '#8b5cf6',
    learning: '#10b981',
    social: '#ec4899',
    creativity: '#f59e0b',
    finance: '#14b8a6',
    other: '#6366f1',
  };
  return colors[category] || '#6366f1';
}

/**
 * Format date for display
 */
export function formatDate(date: Date): string {
  if (isToday(date)) return 'Today';
  if (isYesterday(date)) return 'Yesterday';
  return format(date, 'MMM d, yyyy');
}

/**
 * Check if user has earned an achievement
 */
export function checkAchievement(
  achievementRequirement: number,
  currentProgress: number
): boolean {
  return currentProgress >= achievementRequirement;
}
