"""
Field Mapping Service with Smart Fallback

Handles data transformation between different system schemas
"""
from typing import Dict, Any, List, Optional
from loguru import logger


class FieldMappingService:
    """
    Service for mapping fields between different systems

    Features:
    - Universal schema to system-specific mapping
    - System-specific to universal mapping
    - Smart field fallback
    - Version-aware transformations
    """

    def __init__(self):
        # Mapping configurations
        self.mappings = self._load_mappings()

        # Smart fallbacks (like gmobile)
        self.field_fallbacks = {
            'phone': ['mobile', 'phone_primary', 'phone_secondary', 'work_phone'],
            'mobile': ['phone', 'phone_primary', 'cell_phone'],
            'name': ['display_name', 'partner_name', 'complete_name', 'full_name'],
            'email': ['email_from', 'partner_email', 'work_email', 'email_address'],
            'price': ['list_price', 'standard_price', 'sale_price', 'unit_price'],
            'street': ['street', 'street1', 'address'],
            'street2': ['street2', 'address2', 'address_line2'],
            'city': ['city', 'city_id', 'town'],
            'state': ['state', 'state_id', 'province', 'region'],
            'zip': ['zip', 'postal_code', 'postcode'],
            'country': ['country', 'country_id', 'country_code'],
            'vat': ['vat', 'tax_id', 'tin', 'fiscal_number'],
        }

    def _load_mappings(self) -> Dict[str, Dict]:
        """
        Load mapping configurations

        Returns:
            Mapping configurations for different systems
        """
        return {
            "odoo_16": {
                "res.partner": {
                    "universal_to_odoo": {
                        "name": "name",
                        "email": "email",
                        "phone": "phone",
                        "mobile": "mobile",
                        "street": "street",
                        "street2": "street2",
                        "city": "city",
                        "state": "state_id",
                        "zip": "zip",
                        "country": "country_id",
                        "is_company": "is_company",
                        "vat": "vat",
                        "website": "website",
                    },
                    "odoo_to_universal": {
                        "name": "name",
                        "email": "email",
                        "phone": "phone",
                        "mobile": "mobile",
                        "street": "street",
                        "street2": "street2",
                        "city": "city",
                        "state_id": "state",
                        "zip": "zip",
                        "country_id": "country",
                        "is_company": "is_company",
                        "vat": "vat",
                        "website": "website",
                    }
                },
                "product.product": {
                    "universal_to_odoo": {
                        "name": "name",
                        "default_code": "default_code",
                        "barcode": "barcode",
                        "type": "type",
                        "categ": "categ_id",
                        "list_price": "list_price",
                        "standard_price": "standard_price",
                        "description": "description",
                        "description_sale": "description_sale",
                        "sale_ok": "sale_ok",
                        "purchase_ok": "purchase_ok",
                    },
                    "odoo_to_universal": {
                        "name": "name",
                        "default_code": "default_code",
                        "barcode": "barcode",
                        "type": "type",
                        "categ_id": "categ",
                        "list_price": "list_price",
                        "standard_price": "standard_price",
                        "description": "description",
                        "description_sale": "description_sale",
                        "sale_ok": "sale_ok",
                        "purchase_ok": "purchase_ok",
                        "qty_available": "qty_available",
                    }
                }
            },
            "odoo_18": {
                # Odoo 18 might have different field names
                "res.partner": {
                    "universal_to_odoo": {
                        "name": "name",
                        "email": "email",
                        "phone": "phone_primary",  # Changed in v18
                        "mobile": "phone_secondary",  # Changed in v18
                        "street": "street",
                        "street2": "street2",
                        "city": "city",
                        "state": "state_id",
                        "zip": "zip",
                        "country": "country_id",
                        "is_company": "is_company",
                        "vat": "vat",
                        "website": "website",
                    }
                }
            }
        }

    async def transform_to_universal(
        self,
        data: Dict[str, Any],
        system_type: str,
        system_version: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Transform system-specific data to universal schema

        Args:
            data: System-specific data
            system_type: System type (odoo, sap, etc.)
            system_version: System version
            model: Model name

        Returns:
            Universal schema data
        """
        mapping_key = f"{system_type}_{system_version.replace('.', '_')}"
        mapping = self.mappings.get(mapping_key, {}).get(model, {}).get("odoo_to_universal", {})

        if not mapping:
            logger.warning(f"No mapping found for {system_type} {system_version} {model}")
            return data

        universal_data = {}

        for system_field, universal_field in mapping.items():
            # Try to get value
            value = self._get_field_value(data, system_field)

            # Apply smart fallback
            if value is None or value is False:
                value = self._apply_fallback(data, universal_field)

            if value is not None:
                universal_data[universal_field] = value

        return universal_data

    async def transform_to_system(
        self,
        data: Dict[str, Any],
        system_type: str,
        system_version: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Transform universal schema to system-specific data

        Args:
            data: Universal schema data
            system_type: System type (odoo, sap, etc.)
            system_version: System version
            model: Model name

        Returns:
            System-specific data
        """
        mapping_key = f"{system_type}_{system_version.replace('.', '_')}"
        mapping = self.mappings.get(mapping_key, {}).get(model, {}).get("universal_to_odoo", {})

        if not mapping:
            logger.warning(f"No mapping found for {system_type} {system_version} {model}")
            return data

        system_data = {}

        for universal_field, system_field in mapping.items():
            if universal_field in data:
                value = data[universal_field]

                # Handle relational fields (e.g., state_id, country_id)
                if system_field.endswith("_id") and isinstance(value, (str, int)):
                    # If it's a Many2one field in Odoo
                    if isinstance(value, str):
                        # Need to search for the ID
                        # For now, just pass the value
                        system_data[system_field] = value
                    else:
                        system_data[system_field] = value
                else:
                    system_data[system_field] = value

        return system_data

    def _get_field_value(self, data: Dict[str, Any], field: str) -> Any:
        """
        Get field value with support for nested fields

        Args:
            data: Data dictionary
            field: Field name (can be nested like 'country_id.name')

        Returns:
            Field value or None
        """
        if '.' in field:
            # Nested field (e.g., 'state_id.name')
            parts = field.split('.')
            value = data.get(parts[0])
            if isinstance(value, (list, tuple)) and len(value) > 1:
                # Many2one field in Odoo returns [id, name]
                return value[1] if len(parts) > 1 else value[0]
            return value
        else:
            return data.get(field)

    def _apply_fallback(
        self,
        data: Dict[str, Any],
        field: str
    ) -> Any:
        """
        Apply smart field fallback

        Args:
            data: Data dictionary
            field: Field name

        Returns:
            Fallback value or None
        """
        if field in self.field_fallbacks:
            for fallback_field in self.field_fallbacks[field]:
                value = self._get_field_value(data, fallback_field)
                if value is not None and value is not False:
                    logger.debug(f"Applied fallback: {fallback_field} -> {field}")
                    return value

        return None

    def add_custom_mapping(
        self,
        system_type: str,
        system_version: str,
        model: str,
        mapping: Dict[str, str],
        direction: str = "both"
    ):
        """
        Add custom field mapping

        Args:
            system_type: System type
            system_version: System version
            model: Model name
            mapping: Field mapping dictionary
            direction: 'to_universal', 'to_system', or 'both'
        """
        mapping_key = f"{system_type}_{system_version.replace('.', '_')}"

        if mapping_key not in self.mappings:
            self.mappings[mapping_key] = {}

        if model not in self.mappings[mapping_key]:
            self.mappings[mapping_key][model] = {}

        if direction in ["to_universal", "both"]:
            self.mappings[mapping_key][model]["odoo_to_universal"] = mapping

        if direction in ["to_system", "both"]:
            # Reverse the mapping
            reverse_mapping = {v: k for k, v in mapping.items()}
            self.mappings[mapping_key][model]["universal_to_odoo"] = reverse_mapping

        logger.info(f"Added custom mapping for {system_type} {system_version} {model}")

    def add_fallback_field(self, field: str, fallbacks: List[str]):
        """
        Add custom fallback fields

        Args:
            field: Primary field name
            fallbacks: List of fallback field names
        """
        self.field_fallbacks[field] = fallbacks
        logger.info(f"Added fallback for {field}: {fallbacks}")
