import React, { useState, useEffect } from 'react';
import { Plus, TrendingUp, Award, Users, Calendar } from 'lucide-react';
import { HabitCard } from '../components/habits/HabitCard';
import { HabitForm } from '../components/habits/HabitForm';
import { useStore } from '../store/useStore';
import { habitsApi, entriesApi, userApi } from '../services/api';
import { isHabitCompletedOnDate, calculatePoints, calculateLevel } from '../utils/habitHelpers';
import toast from 'react-hot-toast';
import type { Habit } from '../types';

export const DashboardPage: React.FC = () => {
  const { user, habits, entries, setHabits, setEntries, addEntry, deleteHabit, updateHabit } = useStore();
  const [showForm, setShowForm] = useState(false);
  const [editingHabit, setEditingHabit] = useState<Habit | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user]);

  const loadData = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const [habitsData, entriesData] = await Promise.all([
        habitsApi.getHabits(user.id),
        entriesApi.getUserEntries(user.id),
      ]);
      setHabits(habitsData);
      setEntries(entriesData);
    } catch (error: any) {
      toast.error('Failed to load data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateHabit = async (habitData: any) => {
    if (!user) return;

    try {
      const newHabit = await habitsApi.createHabit({
        ...habitData,
        userId: user.id,
      });
      setHabits([...habits, newHabit]);
      setShowForm(false);
      toast.success('Habit created! 🎉');
    } catch (error: any) {
      toast.error('Failed to create habit');
      console.error(error);
    }
  };

  const handleEditHabit = async (habitData: any) => {
    if (!user || !editingHabit) return;

    try {
      const updated = await habitsApi.updateHabit(editingHabit.id, habitData);
      updateHabit(editingHabit.id, updated);
      setEditingHabit(null);
      toast.success('Habit updated!');
    } catch (error: any) {
      toast.error('Failed to update habit');
      console.error(error);
    }
  };

  const handleDeleteHabit = async (habitId: string) => {
    try {
      await habitsApi.deleteHabit(habitId);
      deleteHabit(habitId);
      toast.success('Habit deleted');
    } catch (error: any) {
      toast.error('Failed to delete habit');
      console.error(error);
    }
  };

  const handleCompleteHabit = async (habitId: string) => {
    if (!user) return;

    const habit = habits.find(h => h.id === habitId);
    if (!habit) return;

    // Check if already completed today
    const habitEntries = entries.filter(e => e.habitId === habitId);
    const isCompleted = isHabitCompletedOnDate(habitEntries, selectedDate);

    if (isCompleted) {
      toast.error('Already completed today!');
      return;
    }

    try {
      const entry = await entriesApi.createEntry({
        habitId,
        userId: user.id,
        completedAt: selectedDate,
      });

      addEntry(entry);

      // Calculate and award points
      const streak = habitEntries.length + 1; // Simplified
      const points = calculatePoints(habit, streak);

      // Update user stats
      const newTotalPoints = user.totalPoints + points;
      const newLevel = calculateLevel(newTotalPoints);
      await userApi.updateStats(user.id, {
        totalPoints: newTotalPoints,
        level: newLevel,
      });

      toast.success(`+${points} points! 🎉`);
    } catch (error: any) {
      toast.error('Failed to complete habit');
      console.error(error);
    }
  };

  const todayCompletions = entries.filter(e =>
    isHabitCompletedOnDate([e], selectedDate)
  ).length;

  const totalPoints = user?.totalPoints || 0;
  const level = user?.level || 1;
  const currentStreak = user?.currentStreak || 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your habits...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold mb-1">
                Welcome back, {user?.displayName}!
              </h1>
              <p className="text-indigo-100">
                {habits.length === 0
                  ? "Let's create your first habit!"
                  : `You have ${habits.length} active ${habits.length === 1 ? 'habit' : 'habits'}`}
              </p>
            </div>
            <button
              onClick={() => setShowForm(true)}
              className="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:bg-indigo-50 transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
            >
              <Plus size={20} />
              New Habit
            </button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <TrendingUp size={24} />
                </div>
                <div>
                  <p className="text-indigo-100 text-sm">Level</p>
                  <p className="text-2xl font-bold">{level}</p>
                </div>
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <Award size={24} />
                </div>
                <div>
                  <p className="text-indigo-100 text-sm">Total Points</p>
                  <p className="text-2xl font-bold">{totalPoints.toLocaleString()}</p>
                </div>
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  🔥
                </div>
                <div>
                  <p className="text-indigo-100 text-sm">Streak</p>
                  <p className="text-2xl font-bold">{currentStreak} days</p>
                </div>
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <Calendar size={24} />
                </div>
                <div>
                  <p className="text-indigo-100 text-sm">Today</p>
                  <p className="text-2xl font-bold">
                    {todayCompletions}/{habits.length}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {habits.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🎯</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              No habits yet
            </h2>
            <p className="text-gray-600 mb-6">
              Create your first habit to get started on your journey!
            </p>
            <button
              onClick={() => setShowForm(true)}
              className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-all inline-flex items-center gap-2"
            >
              <Plus size={20} />
              Create Your First Habit
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {habits.map((habit) => {
              const habitEntries = entries.filter(e => e.habitId === habit.id);
              const isCompleted = isHabitCompletedOnDate(habitEntries, selectedDate);

              return (
                <HabitCard
                  key={habit.id}
                  habit={habit}
                  entries={habitEntries}
                  onComplete={handleCompleteHabit}
                  onEdit={(h) => {
                    setEditingHabit(h);
                  }}
                  onDelete={handleDeleteHabit}
                  isCompleted={isCompleted}
                />
              );
            })}
          </div>
        )}
      </div>

      {/* Forms */}
      {showForm && (
        <HabitForm
          onSubmit={handleCreateHabit}
          onCancel={() => setShowForm(false)}
        />
      )}

      {editingHabit && (
        <HabitForm
          onSubmit={handleEditHabit}
          onCancel={() => setEditingHabit(null)}
          initialData={editingHabit}
        />
      )}
    </div>
  );
};
