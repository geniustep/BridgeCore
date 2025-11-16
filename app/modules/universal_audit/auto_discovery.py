"""
Model Auto-Discovery - Automatically discover all Odoo models
"""

from typing import List, Dict, Any
from loguru import logger

from app.utils.odoo_client import OdooClient


class ModelDiscovery:
    """Auto-discover all Odoo models from multiple sources"""

    def __init__(self, odoo_client: OdooClient):
        self.odoo = odoo_client

    async def discover_all_models(self) -> List[Dict[str, Any]]:
        """
        Discover all models from Odoo

        Returns:
            List of model information dictionaries
        """

        logger.info("Starting model discovery...")

        models = {}

        try:
            # Discover from ir.model (Odoo's model registry)
            odoo_models = self.odoo.search_read(
                "ir.model",
                domain=[],
                fields=["id", "model", "name", "transient", "field_id"],
                limit=10000
            )

            logger.info(f"Discovered {len(odoo_models)} models from ir.model")

            for model in odoo_models:
                model_name = model.get("model", "")
                models[model_name] = {
                    "name": model_name,
                    "display_name": model.get("name", ""),
                    "is_transient": model.get("transient", False),
                    "field_count": len(model.get("field_id", [])),
                    "source": "ir.model",
                    "odoo_id": model.get("id")
                }

        except Exception as e:
            logger.error(f"Error discovering models from Odoo: {e}")

        return list(models.values())

    async def get_model_details(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model

        Args:
            model_name: Name of the model (e.g., 'sale.order')

        Returns:
            Dictionary with model details
        """

        try:
            # Get model fields
            fields = self.odoo.fields_get(
                model_name,
                attributes=["string", "type", "required", "readonly"]
            )

            # Get record count (sample)
            count = self.odoo.search(
                model_name,
                domain=[],
                limit=1
            )

            return {
                "model": model_name,
                "fields": fields,
                "field_count": len(fields),
                "has_records": len(count) > 0
            }

        except Exception as e:
            logger.error(f"Error getting details for model {model_name}: {e}")
            return {
                "model": model_name,
                "error": str(e)
            }

    async def discover_related_models(
        self,
        model_name: str
    ) -> List[str]:
        """
        Discover models related to a given model through relationships

        Args:
            model_name: Name of the model

        Returns:
            List of related model names
        """

        try:
            fields = self.odoo.fields_get(model_name)
            related_models = set()

            for field_name, field_info in fields.items():
                field_type = field_info.get("type", "")

                # Many2one, One2many, Many2many relationships
                if field_type in ["many2one", "one2many", "many2many"]:
                    relation = field_info.get("relation")
                    if relation:
                        related_models.add(relation)

            return list(related_models)

        except Exception as e:
            logger.error(f"Error discovering related models for {model_name}: {e}")
            return []
