import React, { useState } from 'react';
import { Check, Flame, Target, MoreVertical, Edit, Trash } from 'lucide-react';
import type { Habit, HabitEntry } from '../../types';
import { calculateStreak, formatStreakText, getHabitColor, getCategoryIcon } from '../../utils/habitHelpers';
import { format } from 'date-fns';

interface HabitCardProps {
  habit: Habit;
  entries: HabitEntry[];
  onComplete: (habitId: string) => void;
  onEdit?: (habit: Habit) => void;
  onDelete?: (habitId: string) => void;
  isCompleted: boolean;
}

export const HabitCard: React.FC<HabitCardProps> = ({
  habit,
  entries,
  onComplete,
  onEdit,
  onDelete,
  isCompleted,
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const streak = calculateStreak(entries);

  return (
    <div
      className="relative bg-white rounded-xl shadow-md hover:shadow-lg transition-all overflow-hidden group"
      style={{
        borderLeft: `4px solid ${habit.color}`,
      }}
    >
      {/* Menu */}
      {(onEdit || onDelete) && (
        <div className="absolute top-3 right-3 z-10">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 rounded-lg hover:bg-gray-100 transition opacity-0 group-hover:opacity-100"
          >
            <MoreVertical size={18} className="text-gray-600" />
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 py-1">
              {onEdit && (
                <button
                  onClick={() => {
                    onEdit(habit);
                    setShowMenu(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                >
                  <Edit size={16} />
                  Edit Habit
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to delete this habit?')) {
                      onDelete(habit.id);
                    }
                    setShowMenu(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <Trash size={16} />
                  Delete Habit
                </button>
              )}
            </div>
          )}
        </div>
      )}

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
              style={{
                backgroundColor: getHabitColor(habit.color, 0.1),
              }}
            >
              {habit.icon || getCategoryIcon(habit.category)}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 text-lg">
                {habit.title}
              </h3>
              {habit.description && (
                <p className="text-sm text-gray-500 mt-0.5 line-clamp-1">
                  {habit.description}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 mb-4 text-sm">
          <div className="flex items-center gap-1.5 text-orange-600">
            <Flame size={16} />
            <span className="font-semibold">{streak.currentStreak}</span>
            <span className="text-gray-500">day streak</span>
          </div>
          {habit.goalValue && (
            <div className="flex items-center gap-1.5 text-indigo-600">
              <Target size={16} />
              <span className="font-semibold">
                {habit.goalValue} {habit.goalUnit}
              </span>
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>This week</span>
            <span>
              {entries.filter(e => {
                const entryDate = new Date(e.completedAt);
                const weekAgo = new Date();
                weekAgo.setDate(weekAgo.getDate() - 7);
                return entryDate >= weekAgo;
              }).length}{' '}
              / 7 days
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="h-2 rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(
                  100,
                  (entries.filter(e => {
                    const entryDate = new Date(e.completedAt);
                    const weekAgo = new Date();
                    weekAgo.setDate(weekAgo.getDate() - 7);
                    return entryDate >= weekAgo;
                  }).length /
                    7) *
                    100
                )}%`,
                backgroundColor: habit.color,
              }}
            ></div>
          </div>
        </div>

        {/* Complete Button */}
        <button
          onClick={() => onComplete(habit.id)}
          disabled={isCompleted}
          className={`w-full py-3 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 ${
            isCompleted
              ? 'bg-green-100 text-green-700 cursor-default'
              : 'hover:shadow-md'
          }`}
          style={{
            backgroundColor: isCompleted ? undefined : getHabitColor(habit.color, 0.1),
            color: isCompleted ? undefined : habit.color,
          }}
        >
          <Check size={20} />
          {isCompleted ? 'Completed Today!' : 'Mark as Complete'}
        </button>
      </div>
    </div>
  );
};
