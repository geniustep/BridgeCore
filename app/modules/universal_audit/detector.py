"""
Universal Audit Detector - Main coordinator for universal change detection
"""

from typing import List, Dict, Any, Optional
from loguru import logger
import asyncio

from app.utils.odoo_client import OdooClient
from app.modules.universal_audit.auto_discovery import ModelDiscovery
from app.modules.universal_audit.classifier import ModelClassifier


class UniversalAuditDetector:
    """
    Main coordinator for universal audit system

    This class:
    - Discovers all Odoo models
    - Classifies them by importance
    - Sets up appropriate monitoring strategy for each
    - Coordinates real-time change detection
    """

    def __init__(self, odoo_client: OdooClient):
        self.odoo = odoo_client
        self.discovery = ModelDiscovery(odoo_client)
        self.classifier = ModelClassifier()
        self.monitored_models = {}
        self.initialized = False

    async def initialize(self) -> int:
        """
        Initialize the universal audit system

        Returns:
            Number of models discovered
        """

        if self.initialized:
            logger.warning("Universal audit detector already initialized")
            return len(self.monitored_models)

        logger.info("Initializing Universal Audit Detector...")

        try:
            # 1. Discover all models
            logger.info("Step 1: Discovering all Odoo models...")
            models = await self.discovery.discover_all_models()

            # 2. Classify models
            logger.info("Step 2: Classifying models by importance...")
            classifications = self.classifier.classify_models(models)

            # 3. Setup monitoring for each model
            logger.info("Step 3: Setting up monitoring strategies...")
            await self._setup_monitoring(classifications)

            self.initialized = True

            # Summary
            summary = self.classifier.get_summary()
            logger.info("=" * 60)
            logger.info("Universal Audit Detector Initialized Successfully")
            logger.info("=" * 60)
            logger.info(f"Total models discovered: {len(models)}")
            logger.info(f"Critical models: {summary.get('critical', 0)}")
            logger.info(f"Important models: {summary.get('important', 0)}")
            logger.info(f"Standard models: {summary.get('standard', 0)}")
            logger.info(f"Transient models: {summary.get('transient', 0)}")
            logger.info(f"Ignored models: {summary.get('ignored', 0)}")
            logger.info("=" * 60)

            return len(models)

        except Exception as e:
            logger.error(f"Error initializing Universal Audit Detector: {e}")
            raise

    async def _setup_monitoring(
        self,
        classifications: Dict[str, List[str]]
    ) -> None:
        """Setup monitoring for classified models"""

        for category, models in classifications.items():
            if category in ["transient", "ignored"]:
                continue

            for model_name in models:
                config = self.classifier.get_monitoring_config(model_name)
                self.monitored_models[model_name] = {
                    "classification": category,
                    "config": config,
                    "enabled": True
                }

        logger.info(f"Monitoring configured for {len(self.monitored_models)} models")

    async def get_recent_changes(
        self,
        model_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent changes for a model or all models

        Args:
            model_name: Specific model to query (None for all)
            limit: Max number of changes to return

        Returns:
            List of change events
        """

        try:
            domain = []
            if model_name:
                domain.append(["model", "=", model_name])

            changes = self.odoo.search_read(
                "update.webhook",
                domain=domain,
                fields=["id", "model", "record_id", "event", "timestamp"],
                limit=limit,
                order="timestamp desc"
            )

            return changes

        except Exception as e:
            logger.error(f"Error getting recent changes: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the audit system"""

        try:
            # Get total events count
            all_events = self.odoo.search(
                "update.webhook",
                domain=[],
                limit=1
            )
            total_events = len(all_events)

            # Get events by model
            events_summary = self.odoo.get_updates_summary(limit=1000)

            return {
                "initialized": self.initialized,
                "monitored_models_count": len(self.monitored_models),
                "total_events": total_events,
                "events_by_model": events_summary.get("summary", []),
                "last_event_at": events_summary.get("last_update_at"),
                "classifications": self.classifier.get_summary()
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "initialized": self.initialized,
                "error": str(e)
            }

    def is_model_monitored(self, model_name: str) -> bool:
        """Check if a model is being monitored"""
        return model_name in self.monitored_models

    def get_model_config(
        self,
        model_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get monitoring configuration for a model"""
        return self.monitored_models.get(model_name)

    def enable_model(self, model_name: str) -> bool:
        """Enable monitoring for a model"""
        if model_name in self.monitored_models:
            self.monitored_models[model_name]["enabled"] = True
            logger.info(f"Enabled monitoring for model: {model_name}")
            return True
        return False

    def disable_model(self, model_name: str) -> bool:
        """Disable monitoring for a model"""
        if model_name in self.monitored_models:
            self.monitored_models[model_name]["enabled"] = False
            logger.info(f"Disabled monitoring for model: {model_name}")
            return True
        return False
