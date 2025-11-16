"""
Model Classifier - Classify models by importance and priority
"""

from typing import List, Dict, Any
from loguru import logger


class ModelClassifier:
    """Classify Odoo models by importance for monitoring priority"""

    # Critical patterns - highest priority, real-time tracking
    CRITICAL_PATTERNS = [
        "sale.order",
        "purchase.order",
        "account.move",
        "stock.picking",
        "res.partner",
        "account.payment"
    ]

    # Important prefixes - medium priority
    IMPORTANT_PREFIXES = [
        "sale.",
        "purchase.",
        "stock.",
        "account.",
        "product.",
        "hr.",
        "project.",
        "crm."
    ]

    # Ignore patterns - don't track these
    IGNORE_PATTERNS = [
        "ir.",
        "base.",
        "mail.message",
        "mail.followers",
        "mail.activity",
        "bus.bus",
        "report.",
        "wizard."
    ]

    def __init__(self):
        self.classifications = {
            "critical": [],
            "important": [],
            "standard": [],
            "transient": [],
            "ignored": []
        }

    def classify_models(
        self,
        models: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Classify models by importance

        Args:
            models: List of model dictionaries from discovery

        Returns:
            Dictionary with models grouped by classification
        """

        logger.info(f"Classifying {len(models)} models...")

        for model in models:
            name = model.get("name", "")
            is_transient = model.get("is_transient", False)

            # Skip empty names
            if not name:
                continue

            # Transient models (temporary, wizard-like)
            if is_transient:
                self.classifications["transient"].append(name)
                continue

            # Ignored patterns
            if self._should_ignore(name):
                self.classifications["ignored"].append(name)
                continue

            # Critical models
            if name in self.CRITICAL_PATTERNS:
                self.classifications["critical"].append(name)
                continue

            # Important models (by prefix)
            if self._is_important(name):
                self.classifications["important"].append(name)
                continue

            # Standard models (everything else)
            self.classifications["standard"].append(name)

        # Log summary
        for category, models in self.classifications.items():
            logger.info(f"{category.upper()}: {len(models)} models")

        return self.classifications

    def _should_ignore(self, model_name: str) -> bool:
        """Check if model should be ignored"""
        for pattern in self.IGNORE_PATTERNS:
            if pattern in model_name:
                return True
        return False

    def _is_important(self, model_name: str) -> bool:
        """Check if model is important (medium priority)"""
        for prefix in self.IMPORTANT_PREFIXES:
            if model_name.startswith(prefix):
                return True
        return False

    def get_monitoring_config(
        self,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Get recommended monitoring configuration for a model

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with monitoring settings
        """

        # Find classification
        classification = "standard"
        for category, models in self.classifications.items():
            if model_name in models:
                classification = category
                break

        # Monitoring configurations by classification
        configs = {
            "critical": {
                "strategy": "database_trigger",
                "polling_interval": None,  # Real-time only
                "cache_ttl": 30,
                "priority": "high"
            },
            "important": {
                "strategy": "hybrid",  # Trigger + polling
                "polling_interval": 300,  # 5 minutes
                "cache_ttl": 60,
                "priority": "medium"
            },
            "standard": {
                "strategy": "polling",
                "polling_interval": 900,  # 15 minutes
                "cache_ttl": 300,
                "priority": "low"
            },
            "transient": {
                "strategy": "none",
                "polling_interval": None,
                "cache_ttl": 0,
                "priority": "none"
            },
            "ignored": {
                "strategy": "none",
                "polling_interval": None,
                "cache_ttl": 0,
                "priority": "none"
            }
        }

        return configs.get(classification, configs["standard"])

    def get_summary(self) -> Dict[str, int]:
        """Get classification summary"""
        return {
            category: len(models)
            for category, models in self.classifications.items()
        }
