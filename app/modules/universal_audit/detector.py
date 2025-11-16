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
    Main coordinator for universal audit system - ORM-based detection

    This class:
    - Discovers all Odoo models
    - Classifies them by importance
    - Manages webhook configurations in Odoo
    - Monitors change detection via Odoo's enhanced webhook module

    Note: Uses ORM-based detection through Odoo webhook module
    (no PostgreSQL triggers required)
    """

    def __init__(self, odoo_client: OdooClient):
        self.odoo = odoo_client
        self.discovery = ModelDiscovery(odoo_client)
        self.classifier = ModelClassifier()
        self.monitored_models = {}
        self.initialized = False

    async def initialize(self) -> int:
        """
        Initialize the universal audit system (ORM-based)

        Returns:
            Number of models discovered and configured
        """

        if self.initialized:
            logger.warning("Universal audit detector already initialized")
            return len(self.monitored_models)

        logger.info("Initializing Universal Audit Detector (ORM-based)...")

        try:
            # 1. Discover all models
            logger.info("Step 1: Discovering all Odoo models...")
            models = await self.discovery.discover_all_models()

            # 2. Classify models
            logger.info("Step 2: Classifying models by importance...")
            classifications = self.classifier.classify_models(models)

            # 3. Setup webhook configs in Odoo
            logger.info("Step 3: Setting up webhook configurations in Odoo...")
            await self._setup_webhook_configs(classifications)

            # 4. Verify webhook module installation
            logger.info("Step 4: Verifying Odoo webhook module...")
            await self._verify_webhook_module()

            self.initialized = True

            # Summary
            summary = self.classifier.get_summary()
            logger.info("=" * 60)
            logger.info("Universal Audit Detector Initialized Successfully")
            logger.info("Detection Method: ORM-based (via Odoo webhook module)")
            logger.info("=" * 60)
            logger.info(f"Total models discovered: {len(models)}")
            logger.info(f"Critical models: {summary.get('critical', 0)}")
            logger.info(f"Important models: {summary.get('important', 0)}")
            logger.info(f"Standard models: {summary.get('standard', 0)}")
            logger.info(f"Transient models: {summary.get('transient', 0)}")
            logger.info(f"Ignored models: {summary.get('ignored', 0)}")
            logger.info(f"Webhook configs created: {len(self.monitored_models)}")
            logger.info("=" * 60)

            return len(models)

        except Exception as e:
            logger.error(f"Error initializing Universal Audit Detector: {e}")
            raise

    async def _setup_webhook_configs(
        self,
        classifications: Dict[str, List[str]]
    ) -> None:
        """
        Setup webhook configurations in Odoo for classified models
        Creates or updates webhook.config records in Odoo
        """

        for category, models in classifications.items():
            if category in ["transient", "ignored"]:
                continue

            for model_name in models:
                try:
                    # Get monitoring config
                    config = self.classifier.get_monitoring_config(model_name)

                    # Check if config already exists in Odoo
                    existing_configs = self.odoo.search_read(
                        "webhook.config",
                        domain=[["model_name", "=", model_name]],
                        fields=["id"],
                        limit=1
                    )

                    config_data = {
                        "name": f"{model_name} Webhook Config",
                        "model_name": model_name,
                        "enabled": True,
                        "priority": config.get("priority", "medium"),
                        "category": category if category in ["business", "system"] else "business",
                        "events": ["create", "write", "unlink"],
                        "batch_enabled": category != "critical",  # Critical models: no batch
                        "batch_size": 50 if category != "critical" else None,
                        "active": True
                    }

                    if existing_configs:
                        # Update existing config
                        config_id = existing_configs[0]["id"]
                        self.odoo.write("webhook.config", [config_id], config_data)
                        logger.debug(f"Updated webhook config for {model_name}")
                    else:
                        # Create new config
                        # Get model_id first
                        model_recs = self.odoo.search_read(
                            "ir.model",
                            domain=[["model", "=", model_name]],
                            fields=["id"],
                            limit=1
                        )

                        if model_recs:
                            config_data["model_id"] = model_recs[0]["id"]
                            config_id = self.odoo.create("webhook.config", config_data)
                            logger.debug(f"Created webhook config for {model_name}")
                        else:
                            logger.warning(f"Model {model_name} not found in ir.model, skipping")
                            continue

                    # Store locally
                    self.monitored_models[model_name] = {
                        "classification": category,
                        "config": config,
                        "enabled": True,
                        "odoo_config_id": config_id if isinstance(config_id, int) else existing_configs[0]["id"]
                    }

                except Exception as e:
                    logger.error(f"Error setting up webhook config for {model_name}: {e}")
                    continue

        logger.info(f"Webhook configs set up for {len(self.monitored_models)} models")

    async def _verify_webhook_module(self) -> bool:
        """
        Verify that the enhanced webhook module is installed in Odoo

        Returns:
            True if module is installed, False otherwise
        """

        try:
            # Check if webhook.event model exists
            webhook_models = self.odoo.search_read(
                "ir.model",
                domain=[["model", "=", "webhook.event"]],
                fields=["id", "name"],
                limit=1
            )

            if not webhook_models:
                logger.error(
                    "Enhanced webhook module not installed in Odoo! "
                    "Please install the auto-webhook-odoo module first."
                )
                return False

            # Check if webhook.config model exists
            config_models = self.odoo.search_read(
                "ir.model",
                domain=[["model", "=", "webhook.config"]],
                fields=["id", "name"],
                limit=1
            )

            if not config_models:
                logger.warning(
                    "webhook.config model not found - module may be outdated. "
                    "Please update to the latest version."
                )
                return False

            logger.info("✓ Enhanced webhook module verified successfully")
            return True

        except Exception as e:
            logger.error(f"Error verifying webhook module: {e}")
            return False

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
                "webhook.event",  # Updated model name
                domain=domain,
                fields=["id", "model", "record_id", "event", "timestamp", "priority", "status"],
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
                "webhook.event",  # Updated model name
                domain=[],
                limit=1
            )
            total_events = len(all_events)

            # Get events by model (if method exists)
            try:
                events_summary = self.odoo.get_updates_summary(limit=1000)
            except:
                events_summary = {"summary": [], "last_update_at": None}

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
