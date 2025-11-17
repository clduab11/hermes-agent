import Stripe from 'stripe';
import { createClient } from '@supabase/supabase-js';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export default async function handler(req: any, res: any) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { priceId, userId, successUrl, cancelUrl } = req.body;

  if (!priceId || !userId) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  try {
    // Get user's email
    const { data: profile, error: profileError } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single();

    if (profileError || !profile) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Check if user already has a Stripe customer ID
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('stripe_customer_id')
      .eq('user_id', userId)
      .single();

    let customerId = subscription?.stripe_customer_id;

    // Create Stripe customer if doesn't exist
    if (!customerId) {
      const customer = await stripe.customers.create({
        email: profile.email,
        metadata: {
          userId: userId,
          username: profile.username,
        },
      });

      customerId = customer.id;

      // Update subscription with customer ID
      await supabase
        .from('subscriptions')
        .update({ stripe_customer_id: customerId })
        .eq('user_id', userId);
    }

    // Create checkout session
    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      payment_method_types: ['card'],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      mode: 'subscription',
      success_url: successUrl || `${process.env.VITE_APP_URL}/billing?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: cancelUrl || `${process.env.VITE_APP_URL}/pricing`,
      subscription_data: {
        trial_period_days: 14, // 14-day free trial
        metadata: {
          userId: userId,
        },
      },
      allow_promotion_codes: true,
    });

    res.status(200).json({ sessionId: session.id });
  } catch (error: any) {
    console.error('Checkout session creation failed:', error);
    res.status(500).json({ error: error.message || 'Failed to create checkout session' });
  }
}
