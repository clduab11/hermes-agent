import React, { useState } from 'react';
import { PricingCard } from '../components/billing/PricingCard';
import { PRICING_PLANS } from '../types/subscription';
import { useStore } from '../store/useStore';
import { useSubscription } from '../hooks/useSubscription';
import { Check } from 'lucide-react';

export const PricingPage: React.FC = () => {
  const { user } = useStore();
  const { tier } = useSubscription();
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('annual');

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            Start building better habits today. Upgrade anytime to unlock more features.
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`px-6 py-2 rounded-lg font-semibold transition ${
                billingPeriod === 'monthly'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-600'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod('annual')}
              className={`px-6 py-2 rounded-lg font-semibold transition flex items-center gap-2 ${
                billingPeriod === 'annual'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-600'
              }`}
            >
              Annual
              <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                Save 17%
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {PRICING_PLANS.map((plan) => (
            <PricingCard
              key={plan.id}
              plan={plan}
              userId={user?.id}
              currentTier={tier}
              billingPeriod={billingPeriod}
            />
          ))}
        </div>
      </div>

      {/* FAQ Section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Frequently Asked Questions
        </h2>

        <div className="space-y-8">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Can I change plans at any time?
            </h3>
            <p className="text-gray-600">
              Yes! You can upgrade or downgrade your plan at any time. When upgrading, you'll be charged a prorated amount for the remainder of your billing period. When downgrading, the change will take effect at the end of your current billing period.
            </p>
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              What happens to my data if I downgrade?
            </h3>
            <p className="text-gray-600">
              Your data is never deleted. If you downgrade from Pro to Free, you'll keep all your habits and data, but you won't be able to create new habits beyond the free tier limit until you upgrade again.
            </p>
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Is there a free trial?
            </h3>
            <p className="text-gray-600">
              Yes! All paid plans come with a 14-day free trial. No credit card required for the free plan. You can cancel anytime during the trial period.
            </p>
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              How do AI recommendations work?
            </h3>
            <p className="text-gray-600">
              Our AI analyzes your habit completion patterns, optimal times, and success rates to provide personalized recommendations. Pro users get 10 recommendations per month, while Premium users get unlimited access.
            </p>
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              What payment methods do you accept?
            </h3>
            <p className="text-gray-600">
              We accept all major credit cards (Visa, MasterCard, American Express) and digital wallets through Stripe. All payments are secure and encrypted.
            </p>
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Can I get a refund?
            </h3>
            <p className="text-gray-600">
              We offer a 30-day money-back guarantee. If you're not satisfied with HabitFlow, contact support within 30 days of your purchase for a full refund.
            </p>
          </div>
        </div>
      </div>

      {/* Feature Comparison */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Compare Plans
        </h2>

        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                  Feature
                </th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-gray-900">
                  Starter
                </th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-gray-900 bg-indigo-50">
                  Achiever
                </th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-gray-900">
                  Champion
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {[
                { feature: 'Active Habits', free: '3', pro: 'Unlimited', premium: 'Unlimited' },
                { feature: 'Analytics History', free: '30 days', pro: 'Unlimited', premium: 'Unlimited' },
                { feature: 'AI Recommendations', free: '0', pro: '10/month', premium: 'Unlimited' },
                { feature: 'Social Posting', free: '—', pro: <Check className="text-green-500 mx-auto" />, premium: <Check className="text-green-500 mx-auto" /> },
                { feature: 'Data Export', free: '—', pro: <Check className="text-green-500 mx-auto" />, premium: <Check className="text-green-500 mx-auto" /> },
                { feature: 'Custom Categories', free: '—', pro: <Check className="text-green-500 mx-auto" />, premium: <Check className="text-green-500 mx-auto" /> },
                { feature: 'Create Challenges', free: '—', pro: '—', premium: <Check className="text-green-500 mx-auto" /> },
                { feature: 'API Access', free: '—', pro: '—', premium: <Check className="text-green-500 mx-auto" /> },
                { feature: 'Priority Support', free: '—', pro: <Check className="text-green-500 mx-auto" />, premium: <Check className="text-green-500 mx-auto" /> },
              ].map((row, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                    {row.feature}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 text-center">
                    {row.free}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 text-center bg-indigo-50/50">
                    {row.pro}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 text-center">
                    {row.premium}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
          <h2 className="text-4xl font-bold mb-4">
            Ready to Build Better Habits?
          </h2>
          <p className="text-xl text-indigo-100 mb-8">
            Join thousands of users transforming their lives, one habit at a time.
          </p>
          <button className="bg-white text-indigo-600 px-8 py-4 rounded-lg font-semibold text-lg hover:shadow-xl transition">
            Start Your Free Trial
          </button>
        </div>
      </div>
    </div>
  );
};
