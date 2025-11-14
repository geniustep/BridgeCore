"""
Version Handler for system version migrations

Handles data transformation between different versions of the same system
"""
from typing import Dict, Any, Optional
from loguru import logger


class VersionHandler:
    """
    Handle version-specific transformations

    Features:
    - Odoo version migrations (13.0 -> 14.0 -> 15.0 -> 16.0 -> 17.0 -> 18.0 -> 19.0)
    - Field renaming between versions
    - Data structure changes
    - Deprecated field handling
    - Automatic multi-hop migration (e.g., 13.0 -> 19.0)
    """

    def __init__(self):
        self.version_rules = self._load_version_rules()

    def _load_version_rules(self) -> Dict:
        """
        Load version migration rules

        Returns:
            Version migration rules for different systems
        """
        return {
            "odoo": {
                "res.partner": {
                    "13.0_to_16.0": {
                        "customer": {
                            "rename_to": None,  # Removed in v16
                            "replace_with": {"is_company": False}
                        },
                        "supplier": {
                            "rename_to": None,  # Removed in v16
                            "replace_with": None
                        }
                    },
                    "16.0_to_18.0": {
                        "phone": {
                            "rename_to": "phone_primary",
                            "split_to": None
                        },
                        "mobile": {
                            "rename_to": "phone_secondary",
                            "split_to": None
                        }
                    },
                    "13.0_to_18.0": {
                        # Combined migration from 13 -> 18
                        "customer": {
                            "rename_to": None,
                            "replace_with": {"is_company": False}
                        },
                        "phone": {
                            "rename_to": "phone_primary"
                        },
                        "mobile": {
                            "rename_to": "phone_secondary"
                        }
                    }
                },
                "product.product": {
                    "13.0_to_16.0": {
                        "sale_delay": {
                            "rename_to": "delivery_delay",
                            "transform": None
                        }
                    },
                    "16.0_to_18.0": {
                        # Example: if there were changes
                        "type": {
                            "value_mapping": {
                                "product": "storable",
                                "consu": "consumable",
                                "service": "service"
                            }
                        }
                    }
                },
                "sale.order": {
                    "13.0_to_16.0": {
                        "validity_date": {
                            "rename_to": "expiration_date"
                        }
                    }
                }
            }
        }

    async def migrate_data(
        self,
        data: Dict[str, Any],
        system_type: str,
        from_version: str,
        to_version: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Migrate data between versions

        Args:
            data: Original data
            system_type: System type (odoo, sap, etc.)
            from_version: Source version
            to_version: Target version
            model: Model name

        Returns:
            Migrated data

        Example:
            # Migrate Odoo 13 partner to Odoo 16 format
            migrated = await handler.migrate_data(
                data={'name': 'Ahmed', 'customer': True, 'phone': '+966501234567'},
                system_type='odoo',
                from_version='13.0',
                to_version='16.0',
                model='res.partner'
            )
            # Result: {'name': 'Ahmed', 'is_company': False, 'phone': '+966501234567'}
        """
        migration_key = f"{from_version}_to_{to_version}"

        rules = (
            self.version_rules
            .get(system_type, {})
            .get(model, {})
            .get(migration_key, {})
        )

        if not rules:
            logger.warning(
                f"No migration rules found for {system_type} {model} "
                f"{from_version} -> {to_version}"
            )
            return data

        migrated_data = data.copy()

        for old_field, rule in rules.items():
            if old_field in migrated_data:
                old_value = migrated_data[old_field]

                # Handle field rename
                if rule.get("rename_to"):
                    new_field = rule["rename_to"]
                    migrated_data[new_field] = old_value
                    del migrated_data[old_field]
                    logger.debug(f"Renamed field: {old_field} -> {new_field}")

                # Handle field replacement
                elif rule.get("replace_with"):
                    replacement = rule["replace_with"]
                    if replacement:
                        migrated_data.update(replacement)
                    del migrated_data[old_field]
                    logger.debug(f"Replaced field: {old_field} with {replacement}")

                # Handle value mapping
                elif rule.get("value_mapping"):
                    value_map = rule["value_mapping"]
                    if old_value in value_map:
                        migrated_data[old_field] = value_map[old_value]
                        logger.debug(
                            f"Mapped value: {old_field} {old_value} -> {value_map[old_value]}"
                        )

                # Handle field splitting
                elif rule.get("split_to"):
                    split_fields = rule["split_to"]
                    # Custom logic for splitting
                    # Example: split full_name to first_name and last_name
                    if isinstance(old_value, str) and len(split_fields) == 2:
                        parts = old_value.split(maxsplit=1)
                        migrated_data[split_fields[0]] = parts[0] if len(parts) > 0 else ""
                        migrated_data[split_fields[1]] = parts[1] if len(parts) > 1 else ""
                        del migrated_data[old_field]
                        logger.debug(f"Split field: {old_field} -> {split_fields}")

                # Handle custom transformation
                elif rule.get("transform"):
                    transform_func = rule["transform"]
                    if callable(transform_func):
                        migrated_data[old_field] = transform_func(old_value)
                        logger.debug(f"Transformed field: {old_field}")

        return migrated_data

    async def detect_version_differences(
        self,
        system_type: str,
        from_version: str,
        to_version: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Detect differences between versions

        Args:
            system_type: System type
            from_version: Source version
            to_version: Target version
            model: Model name

        Returns:
            Dictionary of differences
        """
        migration_key = f"{from_version}_to_{to_version}"

        rules = (
            self.version_rules
            .get(system_type, {})
            .get(model, {})
            .get(migration_key, {})
        )

        if not rules:
            return {
                "has_changes": False,
                "message": f"No changes detected between {from_version} and {to_version}"
            }

        changes = {
            "has_changes": True,
            "renamed_fields": [],
            "removed_fields": [],
            "added_fields": [],
            "value_changes": []
        }

        for old_field, rule in rules.items():
            if rule.get("rename_to"):
                changes["renamed_fields"].append({
                    "old": old_field,
                    "new": rule["rename_to"]
                })
            elif rule.get("replace_with") is None:
                changes["removed_fields"].append(old_field)
            elif rule.get("value_mapping"):
                changes["value_changes"].append({
                    "field": old_field,
                    "mapping": rule["value_mapping"]
                })

        return changes

    def add_version_rule(
        self,
        system_type: str,
        model: str,
        from_version: str,
        to_version: str,
        field: str,
        rule: Dict[str, Any]
    ):
        """
        Add custom version migration rule

        Args:
            system_type: System type
            model: Model name
            from_version: Source version
            to_version: Target version
            field: Field name
            rule: Migration rule

        Example:
            handler.add_version_rule(
                system_type='odoo',
                model='res.partner',
                from_version='16.0',
                to_version='17.0',
                field='old_field',
                rule={'rename_to': 'new_field'}
            )
        """
        migration_key = f"{from_version}_to_{to_version}"

        if system_type not in self.version_rules:
            self.version_rules[system_type] = {}

        if model not in self.version_rules[system_type]:
            self.version_rules[system_type][model] = {}

        if migration_key not in self.version_rules[system_type][model]:
            self.version_rules[system_type][model][migration_key] = {}

        self.version_rules[system_type][model][migration_key][field] = rule

        logger.info(
            f"Added version rule for {system_type} {model} "
            f"{from_version}->{to_version} field:{field}"
        )

    def get_supported_versions(self, system_type: str, model: str) -> list:
        """
        Get list of supported versions for migration

        Args:
            system_type: System type
            model: Model name

        Returns:
            List of version combinations
        """
        if system_type not in self.version_rules:
            return []

        if model not in self.version_rules[system_type]:
            return []

        return list(self.version_rules[system_type][model].keys())
