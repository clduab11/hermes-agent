import React, { useEffect, useState } from 'react';
import { Crown, CreditCard, Calendar, TrendingUp, Gift, ExternalLink } from 'lucide-react';
import { useStore } from '../store/useStore';
import { useSubscription, useUsageTracking } from '../hooks/useSubscription';
import { paymentApi, referralApi } from '../services/subscriptionApi';
import { stripeHelpers } from '../services/stripe';
import type { PaymentHistory, ReferralCode } from '../types/subscription';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

export const BillingPage: React.FC = () => {
  const { user } = useStore();
  const { subscription, tier, features, loading } = useSubscription();
  const aiUsage = useUsageTracking('ai_recommendations');

  const [payments, setPayments] = useState<PaymentHistory[]>([]);
  const [referralCode, setReferralCode] = useState<ReferralCode | null>(null);
  const [referralStats, setReferralStats] = useState({ totalReferrals: 0, rewardMonths: 0 });
  const [loadingPortal, setLoadingPortal] = useState(false);

  useEffect(() => {
    if (user) {
      loadBillingData();
    }
  }, [user]);

  const loadBillingData = async () => {
    if (!user) return;

    try {
      const [paymentsData, codeData, statsData] = await Promise.all([
        paymentApi.getPaymentHistory(user.id),
        referralApi.getReferralCode(user.id),
        referralApi.getReferralStats(user.id),
      ]);

      setPayments(paymentsData);
      setReferralCode(codeData);
      setReferralStats(statsData);
    } catch (error) {
      console.error('Failed to load billing data:', error);
    }
  };

  const handleGenerateReferralCode = async () => {
    if (!user) return;

    try {
      const code = await referralApi.generateReferralCode(user.id);
      setReferralCode(code);
      toast.success('Referral code generated!');
    } catch (error: any) {
      toast.error('Failed to generate code');
    }
  };

  const handleCopyReferralCode = () => {
    if (!referralCode) return;

    navigator.clipboard.writeText(referralCode.code);
    toast.success('Referral code copied!');
  };

  const handleManageSubscription = async () => {
    if (!user) return;

    try {
      setLoadingPortal(true);
      await stripeHelpers.redirectToPortal(user.id);
    } catch (error: any) {
      toast.error('Failed to open billing portal');
    } finally {
      setLoadingPortal(false);
    }
  };

  const getTierBadge = () => {
    const badges = {
      free: { color: 'bg-gray-100 text-gray-700', icon: '🎯' },
      pro: { color: 'bg-indigo-100 text-indigo-700', icon: '⭐' },
      premium: { color: 'bg-purple-100 text-purple-700', icon: '👑' },
      enterprise: { color: 'bg-blue-100 text-blue-700', icon: '🏢' },
    };

    const badge = badges[tier];

    return (
      <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-full font-semibold ${badge.color}`}>
        <span>{badge.icon}</span>
        <span>{tier.charAt(0).toUpperCase() + tier.slice(1)}</span>
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading billing information...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
              <p className="text-gray-600 mt-1">Manage your subscription and billing</p>
            </div>
            {getTierBadge()}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Subscription Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center gap-3 mb-4">
              <Crown className="text-indigo-600" size={24} />
              <h2 className="text-xl font-semibold text-gray-900">Current Plan</h2>
            </div>
            <p className="text-3xl font-bold text-gray-900 mb-2">
              {tier.charAt(0).toUpperCase() + tier.slice(1)}
            </p>
            {subscription?.currentPeriodEnd && (
              <p className="text-sm text-gray-600">
                Renews on {format(new Date(subscription.currentPeriodEnd), 'MMM dd, yyyy')}
              </p>
            )}
            {tier === 'free' && (
              <a
                href="/pricing"
                className="block mt-4 text-indigo-600 font-semibold hover:text-indigo-700"
              >
                Upgrade to Pro →
              </a>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center gap-3 mb-4">
              <TrendingUp className="text-green-600" size={24} />
              <h2 className="text-xl font-semibold text-gray-900">AI Usage</h2>
            </div>
            <div className="mb-3">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">This Month</span>
                <span className="font-semibold text-gray-900">
                  {aiUsage.currentUsage} / {aiUsage.limit || '∞'}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, aiUsage.percentage)}%` }}
                />
              </div>
            </div>
            {aiUsage.limit && aiUsage.percentage > 80 && (
              <p className="text-sm text-orange-600">
                {aiUsage.limit - aiUsage.currentUsage} recommendations remaining
              </p>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center gap-3 mb-4">
              <Calendar className="text-purple-600" size={24} />
              <h2 className="text-xl font-semibold text-gray-900">Billing Cycle</h2>
            </div>
            <p className="text-lg font-semibold text-gray-900 mb-1">
              {subscription?.currentPeriodStart && subscription?.currentPeriodEnd
                ? `${format(new Date(subscription.currentPeriodStart), 'MMM dd')} - ${format(
                    new Date(subscription.currentPeriodEnd),
                    'MMM dd'
                  )}`
                : 'N/A'}
            </p>
            <p className="text-sm text-gray-600">
              {subscription?.cancelAtPeriodEnd ? 'Cancels at period end' : 'Auto-renews'}
            </p>
          </div>
        </div>

        {/* Manage Subscription */}
        {tier !== 'free' && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Manage Subscription</h2>
            <p className="text-gray-600 mb-6">
              Update payment method, view invoices, or cancel your subscription
            </p>
            <button
              onClick={handleManageSubscription}
              disabled={loadingPortal}
              className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition disabled:opacity-50"
            >
              <CreditCard size={20} />
              {loadingPortal ? 'Loading...' : 'Manage Billing'}
              <ExternalLink size={16} />
            </button>
          </div>
        )}

        {/* Referral Program */}
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl shadow-md p-6 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Gift className="text-indigo-600" size={24} />
            <h2 className="text-xl font-semibold text-gray-900">Referral Program</h2>
          </div>
          <p className="text-gray-700 mb-6">
            Refer friends and both get 1 month free! You've referred <strong>{referralStats.totalReferrals}</strong>{' '}
            {referralStats.totalReferrals === 1 ? 'person' : 'people'}.
          </p>

          {referralCode ? (
            <div>
              <div className="flex gap-3 items-center mb-3">
                <div className="flex-1 bg-white rounded-lg px-4 py-3 border-2 border-indigo-200 font-mono text-lg font-bold text-gray-900">
                  {referralCode.code}
                </div>
                <button
                  onClick={handleCopyReferralCode}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition"
                >
                  Copy Code
                </button>
              </div>
              <p className="text-sm text-gray-600">
                Share this code with friends to give them (and you!) 1 month free.
              </p>
            </div>
          ) : (
            <button
              onClick={handleGenerateReferralCode}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition"
            >
              Generate Referral Code
            </button>
          )}
        </div>

        {/* Payment History */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Payment History</h2>

          {payments.length === 0 ? (
            <p className="text-gray-500 text-center py-12">No payment history yet</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                      Date
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                      Description
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                      Amount
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {payments.map((payment) => (
                    <tr key={payment.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {format(new Date(payment.createdAt), 'MMM dd, yyyy')}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {payment.description || 'Subscription payment'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 font-semibold">
                        ${payment.amount.toFixed(2)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                            payment.status === 'succeeded'
                              ? 'bg-green-100 text-green-700'
                              : payment.status === 'failed'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}
                        >
                          {payment.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
