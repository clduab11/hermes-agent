import React, { useEffect, useState } from 'react';
import { TrendingUp, Target, Award, Calendar as CalendarIcon } from 'lucide-react';
import { useStore } from '../store/useStore';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { format, subDays, eachDayOfInterval } from 'date-fns';
import { calculateCompletionRate, getCategoryColor } from '../utils/habitHelpers';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

export const AnalyticsPage: React.FC = () => {
  const { user, habits, entries } = useStore();
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('month');

  // Calculate date range
  const endDate = new Date();
  const startDate = timeRange === 'week'
    ? subDays(endDate, 7)
    : timeRange === 'month'
    ? subDays(endDate, 30)
    : subDays(endDate, 365);

  // Filter entries by date range
  const filteredEntries = entries.filter(e => {
    const entryDate = new Date(e.completedAt);
    return entryDate >= startDate && entryDate <= endDate;
  });

  // Calculate completion trend data
  const days = eachDayOfInterval({ start: startDate, end: endDate });
  const trendData = {
    labels: days.map(d => format(d, 'MMM dd')),
    datasets: [
      {
        label: 'Completions',
        data: days.map(day => {
          return filteredEntries.filter(e => {
            const entryDate = new Date(e.completedAt);
            return format(entryDate, 'yyyy-MM-dd') === format(day, 'yyyy-MM-dd');
          }).length;
        }),
        borderColor: 'rgb(99, 102, 241)',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        tension: 0.4,
      },
    ],
  };

  // Calculate category breakdown
  const categoryData: Record<string, number> = {};
  filteredEntries.forEach(entry => {
    const habit = habits.find(h => h.id === entry.habitId);
    if (habit) {
      categoryData[habit.category] = (categoryData[habit.category] || 0) + 1;
    }
  });

  const categoryChartData = {
    labels: Object.keys(categoryData),
    datasets: [
      {
        data: Object.values(categoryData),
        backgroundColor: Object.keys(categoryData).map(cat => getCategoryColor(cat)),
      },
    ],
  };

  // Calculate completion rates per habit
  const habitCompletionData = {
    labels: habits.slice(0, 5).map(h => h.title),
    datasets: [
      {
        label: 'Completion Rate (%)',
        data: habits.slice(0, 5).map(habit => {
          const habitEntries = entries.filter(e => e.habitId === habit.id);
          return calculateCompletionRate(habit, habitEntries);
        }),
        backgroundColor: habits.slice(0, 5).map(h => h.color),
      },
    ],
  };

  // Calculate stats
  const totalCompletions = filteredEntries.length;
  const avgPerDay = totalCompletions / days.length;
  const bestDay = days.reduce((best, day) => {
    const count = filteredEntries.filter(e => {
      const entryDate = new Date(e.completedAt);
      return format(entryDate, 'yyyy-MM-dd') === format(day, 'yyyy-MM-dd');
    }).length;
    return count > best.count ? { day, count } : best;
  }, { day: days[0], count: 0 });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
              <p className="text-gray-600 mt-1">
                Track your progress and insights
              </p>
            </div>

            {/* Time Range Selector */}
            <div className="flex gap-2">
              {(['week', 'month', 'year'] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    timeRange === range
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {range.charAt(0).toUpperCase() + range.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="text-indigo-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Completions</p>
                <p className="text-2xl font-bold text-gray-900">{totalCompletions}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Target className="text-green-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Avg Per Day</p>
                <p className="text-2xl font-bold text-gray-900">{avgPerDay.toFixed(1)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <Award className="text-yellow-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Best Day</p>
                <p className="text-2xl font-bold text-gray-900">{bestDay.count}</p>
                <p className="text-xs text-gray-500">{format(bestDay.day, 'MMM dd')}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <CalendarIcon className="text-purple-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Active Habits</p>
                <p className="text-2xl font-bold text-gray-900">{habits.length}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Completion Trend */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Completion Trend
            </h2>
            <Line
              data={trendData}
              options={{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                  legend: { display: false },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                  },
                },
              }}
            />
          </div>

          {/* Category Breakdown */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Category Breakdown
            </h2>
            {Object.keys(categoryData).length > 0 ? (
              <div className="flex items-center justify-center">
                <div className="w-64 h-64">
                  <Doughnut
                    data={categoryChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: true,
                      plugins: {
                        legend: {
                          position: 'bottom',
                        },
                      },
                    }}
                  />
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-12">No data available</p>
            )}
          </div>
        </div>

        {/* Habit Performance */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Habit Performance
          </h2>
          {habits.length > 0 ? (
            <Bar
              data={habitCompletionData}
              options={{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                  legend: { display: false },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                      callback: (value) => `${value}%`,
                    },
                  },
                },
              }}
            />
          ) : (
            <p className="text-gray-500 text-center py-12">
              Create some habits to see analytics
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
