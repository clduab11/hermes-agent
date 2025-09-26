"""
Enterprise SaaS Pricing Configuration for Law Firm Clients
Enforces $2,497/month pricing tier with usage limits
"""

from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

class EnterpriseTier(Enum):
    """Enterprise pricing tiers for law firms."""

    ENTERPRISE = "enterprise"  # Only tier available in SaaS mode


@dataclass
class PricingPlan:
    """Enterprise pricing plan definition."""

    tier: EnterpriseTier
    monthly_price: int  # in cents
    monthly_interactions: int
    overage_rate: float  # per interaction over limit
    features: list[str]
    support_level: str
    compliance_included: bool
    api_rate_limit: int  # requests per minute


class EnterprisePricingManager:
    """Manages enterprise SaaS pricing for law firm clients."""

    # Enterprise SaaS pricing - single tier only
    ENTERPRISE_PLAN = PricingPlan(
        tier=EnterpriseTier.ENTERPRISE,
        monthly_price=249700,  # $2,497.00 in cents
        monthly_interactions=10000,
        overage_rate=0.25,  # $0.25 per interaction
        features=[
            "AI Voice Reception",
            "Legal NLP Processing",
            "Client Intake Automation",
            "Clio Integration",
            "Multi-language Support",
            "Real-time Analytics",
            "HIPAA Compliance",
            "SOC2 Compliance",
            "24/7 Enterprise Support",
            "Custom API Access",
            "Advanced Reporting",
            "White-label Dashboard"
        ],
        support_level="Enterprise 24/7",
        compliance_included=True,
        api_rate_limit=1000  # requests per minute
    )

    @classmethod
    def get_enterprise_plan(cls) -> PricingPlan:
        """Get the enterprise pricing plan."""
        return cls.ENTERPRISE_PLAN

    @classmethod
    def calculate_monthly_cost(cls, interactions_used: int) -> Dict[str, any]:
        """Calculate total monthly cost including overages."""

        plan = cls.ENTERPRISE_PLAN
        base_cost = plan.monthly_price / 100  # Convert to dollars

        # Calculate overage
        overage_interactions = max(0, interactions_used - plan.monthly_interactions)
        overage_cost = overage_interactions * plan.overage_rate

        total_cost = base_cost + overage_cost

        return {
            "base_monthly_fee": base_cost,
            "included_interactions": plan.monthly_interactions,
            "interactions_used": interactions_used,
            "overage_interactions": overage_interactions,
            "overage_rate": plan.overage_rate,
            "overage_cost": overage_cost,
            "total_monthly_cost": total_cost,
            "currency": "USD"
        }

    @classmethod
    def get_pricing_display(cls) -> Dict[str, any]:
        """Get pricing information for display to law firms."""

        plan = cls.ENTERPRISE_PLAN

        return {
            "plan_name": "Enterprise Law Firm",
            "monthly_price": f"${plan.monthly_price / 100:,.2f}",
            "billing_period": "Monthly",
            "included_interactions": f"{plan.monthly_interactions:,}",
            "overage_rate": f"${plan.overage_rate:.2f} per interaction",
            "features": plan.features,
            "support": plan.support_level,
            "compliance": [
                "HIPAA Compliant",
                "SOC2 Type II",
                "Attorney-Client Privilege Protection",
                "Legal Industry Certified"
            ],
            "setup_fee": "None",
            "contract_terms": "Month-to-month",
            "enterprise_support": True,
            "sla_uptime": "99.9%"
        }

    @classmethod
    def validate_usage_limits(cls, law_firm_id: str, current_usage: int) -> Dict[str, any]:
        """Validate usage against enterprise limits."""

        plan = cls.ENTERPRISE_PLAN

        # Calculate usage percentage
        usage_percentage = (current_usage / plan.monthly_interactions) * 100

        # Determine status
        if current_usage <= plan.monthly_interactions:
            status = "within_limits"
            warning = None
        elif current_usage <= plan.monthly_interactions * 1.2:  # 20% grace period
            status = "overage_warning"
            warning = "Approaching overage charges"
        else:
            status = "overage_billing"
            warning = f"Overage charges apply: ${(current_usage - plan.monthly_interactions) * plan.overage_rate:.2f}"

        return {
            "law_firm_id": law_firm_id,
            "plan_tier": plan.tier.value,
            "current_usage": current_usage,
            "usage_limit": plan.monthly_interactions,
            "usage_percentage": round(usage_percentage, 1),
            "status": status,
            "warning": warning,
            "remaining_interactions": max(0, plan.monthly_interactions - current_usage),
            "overage_rate": plan.overage_rate
        }

    @classmethod
    def get_billing_summary(cls, law_firm_id: str, usage_data: Dict) -> Dict[str, any]:
        """Generate billing summary for law firm client."""

        plan = cls.ENTERPRISE_PLAN
        current_month = datetime.now().strftime("%B %Y")

        # Calculate costs
        cost_breakdown = cls.calculate_monthly_cost(usage_data.get("interactions_used", 0))

        return {
            "law_firm_id": law_firm_id,
            "billing_period": current_month,
            "plan": {
                "name": "Enterprise Law Firm",
                "tier": plan.tier.value,
                "monthly_fee": plan.monthly_price / 100
            },
            "usage": {
                "interactions_used": usage_data.get("interactions_used", 0),
                "interactions_included": plan.monthly_interactions,
                "voice_sessions": usage_data.get("voice_sessions", 0),
                "api_calls": usage_data.get("api_calls", 0),
                "storage_gb": usage_data.get("storage_gb", 0)
            },
            "costs": cost_breakdown,
            "features_used": [
                "AI Voice Reception",
                "Legal NLP Processing",
                "Client Intake",
                "Analytics Dashboard"
            ],
            "compliance": {
                "hipaa_status": "Compliant",
                "soc2_status": "Type II Certified",
                "audit_logs_enabled": True,
                "encryption_status": "End-to-end"
            },
            "support": {
                "level": plan.support_level,
                "tickets_this_month": usage_data.get("support_tickets", 0),
                "response_time_sla": "< 1 hour"
            },
            "next_billing_date": usage_data.get("next_billing_date"),
            "payment_method": "Enterprise Net-30"
        }


# Enterprise configuration constants
ENTERPRISE_CONFIG = {
    "pricing_model": "subscription",
    "billing_cycle": "monthly",
    "currency": "USD",
    "tax_calculation": "included",
    "enterprise_discount": False,  # No discounts in SaaS mode
    "volume_pricing": False,  # Single tier only
    "custom_contracts": True,  # Available for enterprise clients
    "payment_terms": [
        "Credit Card (immediate)",
        "ACH (Net-15)",
        "Wire Transfer (Net-30)",
        "Enterprise Invoice (Net-30)"
    ],
    "supported_regions": [
        "US",
        "CA",
        "UK",
        "EU",
        "AU"
    ]
}

def get_enterprise_pricing_config() -> Dict[str, any]:
    """Get complete enterprise pricing configuration."""

    manager = EnterprisePricingManager()

    return {
        "plan": manager.get_pricing_display(),
        "config": ENTERPRISE_CONFIG,
        "compliance": [
            "HIPAA Business Associate Agreement included",
            "SOC2 Type II audit reports available",
            "Attorney-client privilege protection",
            "Data residency options available",
            "Custom security requirements supported"
        ],
        "onboarding": {
            "setup_time": "24-48 hours",
            "dedicated_manager": True,
            "training_included": True,
            "migration_assistance": True
        },
        "contact": {
            "sales": "enterprise@hermes-ai.com",
            "support": "support@hermes-ai.com",
            "legal": "legal@hermes-ai.com"
        }
    }