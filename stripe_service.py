"""Stripe payment service for Météo Martinique subscriptions."""
import logging
from datetime import datetime
from typing import Optional

import stripe

from config import (
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    SUBSCRIPTION_PRICES
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stripe.api_key = STRIPE_SECRET_KEY


class StripeService:
    """Handle Stripe payment operations."""

    def __init__(self):
        self.prices = SUBSCRIPTION_PRICES

    def create_payment_intent(
        self,
        plan_type: str,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None
    ) -> dict:
        """Create PaymentIntent for embedded payment form."""
        if plan_type not in self.prices:
            raise ValueError(f"Invalid plan type: {plan_type}")

        price_config = self.prices[plan_type]

        try:
            # Create or retrieve customer
            customer = None

            # Try to find existing customer by email or phone
            if customer_email:
                customers = stripe.Customer.list(email=customer_email, limit=1)
                if customers.data:
                    customer = customers.data[0]

            if not customer and customer_phone:
                # Search by phone in metadata
                customers = stripe.Customer.list(limit=100)
                for c in customers.data:
                    if c.phone == customer_phone:
                        customer = c
                        break

            # Create new customer if not found
            if not customer:
                customer_data = {}
                if customer_email:
                    customer_data["email"] = customer_email
                if customer_phone:
                    customer_data["phone"] = customer_phone

                # For SMS-only subscriptions, use phone as description
                if not customer_email and customer_phone:
                    customer_data["description"] = f"SMS subscription: {customer_phone}"

                customer = stripe.Customer.create(**customer_data)

            # Create PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=price_config["amount"],
                currency=price_config["currency"],
                customer=customer.id,
                metadata={
                    "plan_type": plan_type,
                    "customer_phone": customer_phone or "",
                    "customer_email": customer_email or ""
                },
                automatic_payment_methods={"enabled": True}
            )

            contact_info = customer_email or customer_phone or "unknown"
            logger.info(f"PaymentIntent created: {intent.id} for {contact_info}")
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "customer_id": customer.id,
                "amount": price_config["amount"],
                "currency": price_config["currency"]
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return {"success": False, "error": str(e)}

    def confirm_payment_intent(self, payment_intent_id: str) -> dict:
        """Verify a PaymentIntent was successful and activate subscription."""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if intent.status == "succeeded":
                # Create a subscription for recurring billing
                plan_type = intent.metadata.get("plan_type")
                price_config = self.prices.get(plan_type, {})

                subscription = stripe.Subscription.create(
                    customer=intent.customer,
                    items=[{
                        "price_data": {
                            "currency": price_config.get("currency", "eur"),
                            "unit_amount": price_config.get("amount", 499),
                            "product_data": {"name": price_config.get("name", "Alertes Météo")},
                            "recurring": {"interval": price_config.get("interval", "month")}
                        }
                    }],
                    metadata=intent.metadata
                )

                return {
                    "success": True,
                    "paid": True,
                    "payment_intent_id": payment_intent_id,
                    "subscription_id": subscription.id,
                    "customer_id": intent.customer,
                    "plan_type": plan_type,
                    "customer_phone": intent.metadata.get("customer_phone"),
                    "customer_email": intent.metadata.get("customer_email")
                }
            else:
                return {"success": True, "paid": False, "status": intent.status}

        except stripe.error.StripeError as e:
            logger.error(f"PaymentIntent verification error: {e}")
            return {"success": False, "error": str(e)}

    def create_checkout_session(
        self,
        plan_type: str,
        customer_email: str,
        customer_phone: Optional[str] = None,
        success_url: str = "https://meteo-martinique.onrender.com/success",
        cancel_url: str = "https://meteo-martinique.onrender.com/"
    ) -> dict:
        """Create Stripe Checkout session for subscription."""
        if plan_type not in self.prices:
            raise ValueError(f"Invalid plan type: {plan_type}")

        price_config = self.prices[plan_type]

        try:
            # Create or retrieve customer
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if customers.data:
                customer = customers.data[0]
            else:
                customer_data = {"email": customer_email}
                if customer_phone:
                    customer_data["phone"] = customer_phone
                customer = stripe.Customer.create(**customer_data)

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": price_config["currency"],
                        "unit_amount": price_config["amount"],
                        "product_data": {
                            "name": price_config["name"],
                            "description": f"Abonnement {price_config['name']} - Météo Martinique"
                        },
                        "recurring": {"interval": price_config["interval"]}
                    },
                    "quantity": 1
                }],
                mode="subscription",
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                metadata={
                    "plan_type": plan_type,
                    "customer_phone": customer_phone or ""
                }
            )

            logger.info(f"Checkout session created: {session.id} for {customer_email}")
            return {
                "success": True,
                "session_id": session.id,
                "checkout_url": session.url,
                "customer_id": customer.id
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return {"success": False, "error": str(e)}

    def verify_session(self, session_id: str) -> dict:
        """Verify checkout session and return subscription details."""
        try:
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == "paid":
                subscription = stripe.Subscription.retrieve(session.subscription)
                return {
                    "success": True,
                    "paid": True,
                    "customer_id": session.customer,
                    "subscription_id": session.subscription,
                    "plan_type": session.metadata.get("plan_type"),
                    "customer_phone": session.metadata.get("customer_phone"),
                    "status": subscription.status,
                    "current_period_end": datetime.fromtimestamp(
                        subscription.current_period_end
                    ).isoformat()
                }
            else:
                return {"success": True, "paid": False, "status": session.payment_status}

        except stripe.error.StripeError as e:
            logger.error(f"Session verification error: {e}")
            return {"success": False, "error": str(e)}

    def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a subscription."""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            logger.info(f"Subscription cancelled: {subscription_id}")
            return {"success": True, "status": subscription.status}
        except stripe.error.StripeError as e:
            logger.error(f"Cancellation error: {e}")
            return {"success": False, "error": str(e)}

    def get_subscription_status(self, customer_email: str) -> dict:
        """Get subscription status for a customer."""
        try:
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if not customers.data:
                return {"success": True, "has_subscription": False}

            customer = customers.data[0]
            subscriptions = stripe.Subscription.list(customer=customer.id, status="active")

            if subscriptions.data:
                sub = subscriptions.data[0]
                return {
                    "success": True,
                    "has_subscription": True,
                    "subscription_id": sub.id,
                    "status": sub.status,
                    "current_period_end": datetime.fromtimestamp(
                        sub.current_period_end
                    ).isoformat()
                }
            else:
                return {"success": True, "has_subscription": False}

        except stripe.error.StripeError as e:
            logger.error(f"Status check error: {e}")
            return {"success": False, "error": str(e)}

    def handle_webhook(self, payload: bytes, sig_header: str) -> dict:
        """Handle Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return {"success": False, "error": "Invalid payload"}
        except stripe.error.SignatureVerificationError:
            return {"success": False, "error": "Invalid signature"}

        event_type = event["type"]
        data = event["data"]["object"]

        logger.info(f"Webhook received: {event_type}")

        if event_type == "checkout.session.completed":
            return {
                "success": True,
                "event": "checkout_completed",
                "customer_id": data.get("customer"),
                "subscription_id": data.get("subscription"),
                "metadata": data.get("metadata", {})
            }

        elif event_type == "customer.subscription.deleted":
            return {
                "success": True,
                "event": "subscription_cancelled",
                "subscription_id": data.get("id"),
                "customer_id": data.get("customer")
            }

        elif event_type == "invoice.payment_failed":
            return {
                "success": True,
                "event": "payment_failed",
                "customer_id": data.get("customer"),
                "subscription_id": data.get("subscription")
            }

        return {"success": True, "event": event_type, "handled": False}


# Singleton instance
stripe_service = StripeService()
