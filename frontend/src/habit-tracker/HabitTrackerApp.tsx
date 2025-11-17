import React, { useEffect, useState } from 'react';
import { Home, TrendingUp, Users, Trophy, Menu, X, LogOut } from 'lucide-react';
import { DashboardPage } from './pages/DashboardPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SocialPage } from './pages/SocialPage';
import { AuthPage } from './components/auth/AuthPage';
import { useStore } from './store/useStore';
import { authHelpers } from './services/supabase';
import { userApi } from './services/api';
import { Toaster } from 'react-hot-toast';

type Page = 'dashboard' | 'analytics' | 'social' | 'challenges';

export const HabitTrackerApp: React.FC = () => {
  const { user, setUser } = useStore();
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    checkUser();

    // Listen for auth changes
    const { data } = authHelpers.onAuthStateChange(async (authUser) => {
      if (authUser) {
        const profile = await userApi.getProfile(authUser.id);
        if (profile) {
          setUser(profile);
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => {
      data?.subscription?.unsubscribe();
    };
  }, []);

  const checkUser = async () => {
    const { user: authUser } = await authHelpers.getCurrentUser();
    if (authUser) {
      const profile = await userApi.getProfile(authUser.id);
      if (profile) {
        setUser(profile);
      }
    }
    setLoading(false);
  };

  const handleSignOut = async () => {
    await authHelpers.signOut();
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading HabitFlow...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  const navigation = [
    { id: 'dashboard' as Page, name: 'Dashboard', icon: Home },
    { id: 'analytics' as Page, name: 'Analytics', icon: TrendingUp },
    { id: 'social' as Page, name: 'Social', icon: Users },
    { id: 'challenges' as Page, name: 'Challenges', icon: Trophy },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />

      {/* Desktop Sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-gradient-to-b from-indigo-600 to-purple-600 overflow-y-auto">
          {/* Logo */}
          <div className="flex items-center flex-shrink-0 px-6 py-6">
            <h1 className="text-2xl font-bold text-white">
              🎯 HabitFlow
            </h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-all ${
                    isActive
                      ? 'bg-white/20 text-white font-semibold'
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <Icon size={20} />
                  <span>{item.name}</span>
                </button>
              );
            })}
          </nav>

          {/* User Profile */}
          <div className="flex-shrink-0 px-3 py-4 border-t border-white/20">
            <div className="flex items-center gap-3 px-3 py-2 text-white">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center font-bold">
                {user.displayName?.charAt(0) || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold truncate">{user.displayName}</p>
                <p className="text-xs text-white/70 truncate">Level {user.level}</p>
              </div>
              <button
                onClick={handleSignOut}
                className="p-2 hover:bg-white/10 rounded-lg transition"
                title="Sign out"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 bg-gradient-to-r from-indigo-600 to-purple-600 text-white z-40">
        <div className="flex items-center justify-between px-4 py-4">
          <h1 className="text-xl font-bold">🎯 HabitFlow</h1>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 hover:bg-white/10 rounded-lg transition"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="border-t border-white/20 px-4 py-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setCurrentPage(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-all ${
                    isActive
                      ? 'bg-white/20 text-white font-semibold'
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <Icon size={20} />
                  <span>{item.name}</span>
                </button>
              );
            })}
            <button
              onClick={handleSignOut}
              className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left text-white/70 hover:bg-white/10 hover:text-white transition-all"
            >
              <LogOut size={20} />
              <span>Sign Out</span>
            </button>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="lg:pl-64 pt-16 lg:pt-0">
        {currentPage === 'dashboard' && <DashboardPage />}
        {currentPage === 'analytics' && <AnalyticsPage />}
        {currentPage === 'social' && <SocialPage />}
        {currentPage === 'challenges' && (
          <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
              <Trophy size={64} className="text-indigo-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Challenges Coming Soon!
              </h2>
              <p className="text-gray-600">
                Compete with friends and join community challenges.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
