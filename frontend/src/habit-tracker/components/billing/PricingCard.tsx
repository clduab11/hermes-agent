import React, { useState } from 'react';
import { Check, Crown, Sparkles } from 'lucide-react';
import type { PricingPlan } from '../../types/subscription';
import { stripeHelpers } from '../../services/stripe';
import toast from 'react-hot-toast';

interface PricingCardProps {
  plan: PricingPlan;
  userId?: string;
  currentTier?: string;
  billingPeriod: 'monthly' | 'annual';
}

export const PricingCard: React.FC<PricingCardProps> = ({
  plan,
  userId,
  currentTier,
  billingPeriod,
}) => {
  const [loading, setLoading] = useState(false);

  const price = billingPeriod === 'monthly' ? plan.price.monthly : plan.price.annual;
  const priceId = billingPeriod === 'monthly'
    ? plan.stripePriceIds.monthly
    : plan.stripePriceIds.annual;

  const isCurrentPlan = currentTier === plan.tier;
  const isFree = plan.tier === 'free';

  const handleSelectPlan = async () => {
    if (isFree || isCurrentPlan || !userId) return;

    try {
      setLoading(true);
      await stripeHelpers.redirectToCheckout(priceId, userId);
    } catch (error: any) {
      toast.error('Failed to start checkout. Please try again.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className={`relative bg-white rounded-2xl shadow-lg overflow-hidden transition-all hover:shadow-xl ${
        plan.highlighted ? 'ring-4 ring-indigo-500 scale-105' : ''
      }`}
    >
      {/* Popular Badge */}
      {plan.popular && (
        <div className="absolute top-0 right-0 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-1 text-sm font-semibold rounded-bl-lg">
          Most Popular
        </div>
      )}

      <div className="p-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          {plan.tier === 'premium' && (
            <Crown className="text-yellow-500" size={32} />
          )}
          {plan.tier === 'pro' && (
            <Sparkles className="text-indigo-500" size={32} />
          )}
          {plan.tier === 'free' && (
            <div className="text-3xl">🎯</div>
          )}
          <div>
            <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
          </div>
        </div>

        {/* Price */}
        <div className="mb-6">
          <div className="flex items-baseline gap-2">
            <span className="text-5xl font-bold text-gray-900">
              ${price}
            </span>
            {!isFree && (
              <span className="text-gray-500">
                /{billingPeriod === 'monthly' ? 'month' : 'year'}
              </span>
            )}
          </div>
          {billingPeriod === 'annual' && !isFree && (
            <p className="text-sm text-green-600 mt-1">
              Save ${(plan.price.monthly * 12 - plan.price.annual).toFixed(0)}/year
            </p>
          )}
        </div>

        {/* Features */}
        <ul className="space-y-3 mb-8">
          {plan.features.map((feature, index) => (
            <li key={index} className="flex items-start gap-3">
              <Check className="text-green-500 flex-shrink-0 mt-0.5" size={20} />
              <span className="text-gray-700">{feature}</span>
            </li>
          ))}
        </ul>

        {/* CTA Button */}
        <button
          onClick={handleSelectPlan}
          disabled={loading || isCurrentPlan || !userId}
          className={`w-full py-3 px-6 rounded-lg font-semibold transition-all ${
            isCurrentPlan
              ? 'bg-gray-200 text-gray-500 cursor-default'
              : plan.highlighted
              ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:shadow-xl'
              : 'bg-indigo-600 text-white hover:bg-indigo-700'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading
            ? 'Loading...'
            : isCurrentPlan
            ? 'Current Plan'
            : plan.buttonText}
        </button>

        {isFree && !userId && (
          <p className="text-center text-sm text-gray-500 mt-3">
            Sign up to get started
          </p>
        )}
      </div>
    </div>
  );
};
