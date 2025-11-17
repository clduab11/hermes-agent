import { loadStripe, Stripe } from '@stripe/stripe-js';

// Initialize Stripe
const stripePublishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '';

if (!stripePublishableKey) {
  console.warn('Stripe publishable key not configured. Set VITE_STRIPE_PUBLISHABLE_KEY');
}

let stripePromise: Promise<Stripe | null>;

export const getStripe = () => {
  if (!stripePromise) {
    stripePromise = loadStripe(stripePublishableKey);
  }
  return stripePromise;
};

// Stripe API helpers (these would call your backend API)
export const stripeHelpers = {
  /**
   * Create a checkout session for subscription
   */
  createCheckoutSession: async (priceId: string, userId: string) => {
    const response = await fetch('/api/stripe/create-checkout-session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        priceId,
        userId,
        successUrl: `${window.location.origin}/billing?session_id={CHECKOUT_SESSION_ID}`,
        cancelUrl: `${window.location.origin}/pricing`,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to create checkout session');
    }

    const { sessionId } = await response.json();
    return sessionId;
  },

  /**
   * Redirect to Stripe Checkout
   */
  redirectToCheckout: async (priceId: string, userId: string) => {
    try {
      const stripe = await getStripe();
      if (!stripe) throw new Error('Stripe not loaded');

      const sessionId = await stripeHelpers.createCheckoutSession(priceId, userId);

      const { error } = await stripe.redirectToCheckout({ sessionId });

      if (error) {
        throw error;
      }
    } catch (error) {
      console.error('Checkout error:', error);
      throw error;
    }
  },

  /**
   * Create portal session for subscription management
   */
  createPortalSession: async (userId: string) => {
    const response = await fetch('/api/stripe/create-portal-session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId,
        returnUrl: `${window.location.origin}/billing`,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to create portal session');
    }

    const { url } = await response.json();
    return url;
  },

  /**
   * Redirect to Stripe Customer Portal
   */
  redirectToPortal: async (userId: string) => {
    try {
      const url = await stripeHelpers.createPortalSession(userId);
      window.location.href = url;
    } catch (error) {
      console.error('Portal redirect error:', error);
      throw error;
    }
  },

  /**
   * Cancel subscription at period end
   */
  cancelSubscription: async (subscriptionId: string) => {
    const response = await fetch('/api/stripe/cancel-subscription', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ subscriptionId }),
    });

    if (!response.ok) {
      throw new Error('Failed to cancel subscription');
    }

    return response.json();
  },

  /**
   * Reactivate a canceled subscription
   */
  reactivateSubscription: async (subscriptionId: string) => {
    const response = await fetch('/api/stripe/reactivate-subscription', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ subscriptionId }),
    });

    if (!response.ok) {
      throw new Error('Failed to reactivate subscription');
    }

    return response.json();
  },

  /**
   * Update payment method (redirects to portal)
   */
  updatePaymentMethod: async (userId: string) => {
    return stripeHelpers.redirectToPortal(userId);
  },
};

export default stripeHelpers;
