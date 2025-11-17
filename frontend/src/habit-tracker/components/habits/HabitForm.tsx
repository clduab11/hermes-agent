import React, { useState, memo } from 'react';
import { X } from 'lucide-react';
import type { Habit, HabitCategory, HabitFrequency } from '../../types';
import { getCategoryIcon } from '../../utils/habitHelpers';

interface HabitFormProps {
  onSubmit: (habit: Omit<Habit, 'id' | 'createdAt' | 'updatedAt' | 'userId'>) => void;
  onCancel: () => void;
  initialData?: Partial<Habit>;
}

const CATEGORIES: { value: HabitCategory; label: string }[] = [
  { value: 'health', label: 'Health' },
  { value: 'fitness', label: 'Fitness' },
  { value: 'productivity', label: 'Productivity' },
  { value: 'mindfulness', label: 'Mindfulness' },
  { value: 'learning', label: 'Learning' },
  { value: 'social', label: 'Social' },
  { value: 'creativity', label: 'Creativity' },
  { value: 'finance', label: 'Finance' },
  { value: 'other', label: 'Other' },
];

const PRESET_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#10b981', '#14b8a6',
  '#3b82f6', '#6366f1', '#8b5cf6', '#ec4899', '#64748b',
];

const HabitFormComponent: React.FC<HabitFormProps> = ({ onSubmit, onCancel, initialData }) => {
  const [title, setTitle] = useState(initialData?.title || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [category, setCategory] = useState<HabitCategory>(initialData?.category || 'health');
  const [color, setColor] = useState(initialData?.color || '#6366f1');
  const [frequencyType, setFrequencyType] = useState<'daily' | 'weekly' | 'custom'>(
    initialData?.frequency?.type || 'daily'
  );
  const [customDays, setCustomDays] = useState<number[]>(
    initialData?.frequency?.customDays || []
  );
  const [timesPerWeek, setTimesPerWeek] = useState(
    initialData?.frequency?.timesPerWeek || 3
  );
  const [goalValue, setGoalValue] = useState(initialData?.goalValue?.toString() || '');
  const [goalUnit, setGoalUnit] = useState(initialData?.goalUnit || '');

  const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const frequency: HabitFrequency = {
      type: frequencyType,
      customDays: frequencyType === 'custom' ? customDays : undefined,
      timesPerWeek: frequencyType === 'weekly' ? timesPerWeek : undefined,
    };

    onSubmit({
      title,
      description: description || undefined,
      category,
      frequency,
      color,
      goalValue: goalValue ? parseInt(goalValue) : undefined,
      goalUnit: goalUnit || undefined,
      isArchived: false,
    } as any);
  };

  const toggleDay = (day: number) => {
    if (customDays.includes(day)) {
      setCustomDays(customDays.filter(d => d !== day));
    } else {
      setCustomDays([...customDays, day].sort());
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">
            {initialData ? 'Edit Habit' : 'Create New Habit'}
          </h2>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Title */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Habit Name *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
              placeholder="e.g., Morning meditation"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition resize-none"
              placeholder="Add more details about your habit..."
              rows={3}
            />
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Category *
            </label>
            <div className="grid grid-cols-3 gap-2">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.value}
                  type="button"
                  onClick={() => setCategory(cat.value)}
                  className={`px-4 py-3 rounded-lg border-2 transition flex items-center gap-2 ${
                    category === cat.value
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span>{getCategoryIcon(cat.value)}</span>
                  <span className="text-sm font-medium">{cat.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Color */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Color
            </label>
            <div className="flex gap-2 flex-wrap">
              {PRESET_COLORS.map((presetColor) => (
                <button
                  key={presetColor}
                  type="button"
                  onClick={() => setColor(presetColor)}
                  className={`w-10 h-10 rounded-lg transition-all ${
                    color === presetColor ? 'ring-4 ring-offset-2 ring-gray-400' : ''
                  }`}
                  style={{ backgroundColor: presetColor }}
                />
              ))}
            </div>
          </div>

          {/* Frequency */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Frequency *
            </label>
            <div className="space-y-3">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setFrequencyType('daily')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 transition font-medium ${
                    frequencyType === 'daily'
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  Daily
                </button>
                <button
                  type="button"
                  onClick={() => setFrequencyType('weekly')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 transition font-medium ${
                    frequencyType === 'weekly'
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  Weekly
                </button>
                <button
                  type="button"
                  onClick={() => setFrequencyType('custom')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 transition font-medium ${
                    frequencyType === 'custom'
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  Custom
                </button>
              </div>

              {frequencyType === 'weekly' && (
                <div>
                  <label className="block text-sm text-gray-600 mb-2">
                    Times per week: {timesPerWeek}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="7"
                    value={timesPerWeek}
                    onChange={(e) => setTimesPerWeek(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>
              )}

              {frequencyType === 'custom' && (
                <div>
                  <label className="block text-sm text-gray-600 mb-2">
                    Select days
                  </label>
                  <div className="flex gap-2">
                    {DAY_NAMES.map((day, index) => (
                      <button
                        key={index}
                        type="button"
                        onClick={() => toggleDay(index)}
                        className={`flex-1 py-2 rounded-lg border-2 transition font-medium ${
                          customDays.includes(index)
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        {day}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Goal */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Goal (optional)
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                value={goalValue}
                onChange={(e) => setGoalValue(e.target.value)}
                className="w-1/3 px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                placeholder="30"
                min="1"
              />
              <input
                type="text"
                value={goalUnit}
                onChange={(e) => setGoalUnit(e.target.value)}
                className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                placeholder="e.g., minutes, pages, reps"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-6 py-3 rounded-lg border-2 border-gray-300 font-semibold text-gray-700 hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-6 py-3 rounded-lg bg-indigo-600 font-semibold text-white hover:bg-indigo-700 transition shadow-lg hover:shadow-xl"
            >
              {initialData ? 'Save Changes' : 'Create Habit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Memoize to prevent re-renders when parent state changes
export const HabitForm = memo(HabitFormComponent);
