import React from 'react';
import { X, Crown, Sparkles, Zap } from 'lucide-react';
import { stripeHelpers } from '../../services/stripe';
import { PRICING_PLANS } from '../../types/subscription';

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId?: string;
  reason?: 'habit_limit' | 'ai_limit' | 'social_feature' | 'analytics' | 'export';
}

export const UpgradeModal: React.FC<UpgradeModalProps> = ({
  isOpen,
  onClose,
  userId,
  reason,
}) => {
  if (!isOpen) return null;

  const proPlan = PRICING_PLANS.find(p => p.tier === 'pro')!;

  const messages = {
    habit_limit: {
      title: "You've reached your habit limit! 🎯",
      description: "Upgrade to Pro to track unlimited habits and unlock:",
    },
    ai_limit: {
      title: 'Want more AI recommendations? 🤖',
      description: 'Upgrade to get personalized coaching:',
    },
    social_feature: {
      title: 'Share Your Success! 📱',
      description: 'Upgrade to Pro to post and engage:',
    },
    analytics: {
      title: 'Unlock Lifetime Analytics! 📊',
      description: 'Upgrade to see all your progress:',
    },
    export: {
      title: 'Export Your Data 💾',
      description: 'Upgrade to Pro to export your habits:',
    },
  };

  const message = messages[reason || 'habit_limit'];

  const handleUpgrade = async () => {
    if (!userId) return;

    try {
      await stripeHelpers.redirectToCheckout(proPlan.stripePriceIds.monthly, userId);
    } catch (error) {
      console.error('Upgrade failed:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full overflow-hidden">
        {/* Header */}
        <div className="relative bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-8">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-lg transition"
          >
            <X size={24} />
          </button>

          <div className="flex items-center gap-4 mb-4">
            <Crown size={48} />
            <div>
              <h2 className="text-3xl font-bold">{message.title}</h2>
              <p className="text-indigo-100">{message.description}</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-8">
          {/* Features */}
          <div className="space-y-4 mb-8">
            {[
              { icon: <Sparkles size={24} className="text-indigo-600" />, text: 'Unlimited habits and categories' },
              { icon: <Zap size={24} className="text-yellow-500" />, text: '10 AI recommendations per month' },
              { icon: <Crown size={24} className="text-purple-600" />, text: 'Lifetime analytics and insights' },
              { icon: '📊', text: 'Export your data anytime' },
              { icon: '💬', text: 'Share achievements with friends' },
              { icon: '🏆', text: 'Join community challenges' },
            ].map((feature, index) => (
              <div key={index} className="flex items-center gap-4">
                <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  {typeof feature.icon === 'string' ? (
                    <span className="text-2xl">{feature.icon}</span>
                  ) : (
                    feature.icon
                  )}
                </div>
                <span className="text-gray-700 font-medium">{feature.text}</span>
              </div>
            ))}
          </div>

          {/* Pricing */}
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 mb-8">
            <div className="flex items-baseline justify-between mb-2">
              <div>
                <span className="text-4xl font-bold text-gray-900">$9.99</span>
                <span className="text-gray-600">/month</span>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600">or save 17%</div>
                <div className="text-2xl font-bold text-gray-900">$99/year</div>
              </div>
            </div>
            <p className="text-sm text-green-600 font-semibold">
              ✨ 14-day free trial • Cancel anytime
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex gap-4">
            <button
              onClick={onClose}
              className="flex-1 px-6 py-3 rounded-lg border-2 border-gray-300 font-semibold text-gray-700 hover:bg-gray-50 transition"
            >
              Maybe Later
            </button>
            <button
              onClick={handleUpgrade}
              className="flex-1 px-6 py-3 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 font-semibold text-white hover:shadow-xl transition"
            >
              Start Free Trial
            </button>
          </div>

          {/* Trust Signals */}
          <div className="mt-6 text-center text-sm text-gray-500">
            <p>🔒 Secure payment • 💳 Cancel anytime • 💯 30-day money-back guarantee</p>
          </div>
        </div>
      </div>
    </div>
  );
};
