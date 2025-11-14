"""
Enhanced Version Handler for Odoo 13.0 -> 19.0

Supports automatic multi-hop migration
"""
from typing import Dict, Any, Optional, List
from loguru import logger
from app.services.odoo_versions import ODOO_VERSION_RULES, get_migration_path


class EnhancedVersionHandler:
    """
    Enhanced Version Handler with Multi-Hop Migration Support

    Features:
    - Odoo 13.0 -> 19.0 support
    - Automatic multi-hop migration (e.g., 13.0 -> 19.0 goes through 14, 15, 16, 17, 18)
    - Smart caching of migration paths
    - Detailed migration logs
    """

    def __init__(self):
        self.version_rules = {"odoo": ODOO_VERSION_RULES}
        self.migration_cache = {}

    async def migrate_data(
        self,
        data: Dict[str, Any],
        system_type: str,
        from_version: str,
        to_version: str,
        model: str,
        auto_multi_hop: bool = True
    ) -> Dict[str, Any]:
        """
        Migrate data between versions with automatic multi-hop support

        Args:
            data: Original data
            system_type: System type (odoo, sap, etc.)
            from_version: Source version (e.g., "13.0")
            to_version: Target version (e.g., "19.0")
            model: Model name
            auto_multi_hop: Automatically perform multi-hop migration if direct path not found

        Returns:
            Migrated data

        Example:
            # Direct migration 13.0 -> 19.0
            migrated = await handler.migrate_data(
                data={'name': 'Ahmed', 'customer': True, 'phone': '+966501234567'},
                system_type='odoo',
                from_version='13.0',
                to_version='19.0',
                model='res.partner'
            )
            # Automatically migrates through: 13->14->15->16->17->18->19
        """
        if from_version == to_version:
            return data

        migration_key = f"{from_version}_to_{to_version}"

        # Try direct migration first
        rules = self._get_migration_rules(system_type, model, migration_key)

        if rules:
            logger.info(f"Direct migration: {from_version} -> {to_version}")
            return await self._apply_migration_rules(data, rules)

        # Try multi-hop migration
        if auto_multi_hop and system_type == "odoo":
            return await self._multi_hop_migration(
                data, from_version, to_version, model
            )

        logger.warning(
            f"No migration path found for {system_type} {model} "
            f"{from_version} -> {to_version}"
        )
        return data

    async def _multi_hop_migration(
        self,
        data: Dict[str, Any],
        from_version: str,
        to_version: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Perform multi-hop migration through intermediate versions

        Args:
            data: Data to migrate
            from_version: Start version
            to_version: End version
            model: Model name

        Returns:
            Migrated data
        """
        migration_path = get_migration_path(from_version, to_version)

        if not migration_path or len(migration_path) < 2:
            logger.error(f"Invalid migration path: {from_version} -> {to_version}")
            return data

        logger.info(f"Multi-hop migration path: {' -> '.join(migration_path)}")

        migrated_data = data.copy()

        # Migrate step by step
        for i in range(len(migration_path) - 1):
            current_version = migration_path[i]
            next_version = migration_path[i + 1]

            migration_key = f"{current_version}_to_{next_version}"
            rules = self._get_migration_rules("odoo", model, migration_key)

            if rules:
                logger.debug(f"Applying migration: {current_version} -> {next_version}")
                migrated_data = await self._apply_migration_rules(migrated_data, rules)
            else:
                logger.debug(f"No rules for {current_version} -> {next_version}, skipping")

        return migrated_data

    def _get_migration_rules(
        self,
        system_type: str,
        model: str,
        migration_key: str
    ) -> Optional[Dict]:
        """Get migration rules for specific path"""
        return (
            self.version_rules
            .get(system_type, {})
            .get(model, {})
            .get(migration_key, None)
        )

    async def _apply_migration_rules(
        self,
        data: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply migration rules to data

        Args:
            data: Data to migrate
            rules: Migration rules

        Returns:
            Migrated data
        """
        migrated_data = data.copy()

        for old_field, rule in rules.items():
            if old_field not in migrated_data:
                continue

            old_value = migrated_data[old_field]

            # Handle field rename
            if rule.get("rename_to"):
                new_field = rule["rename_to"]
                migrated_data[new_field] = old_value
                del migrated_data[old_field]
                logger.debug(f"Renamed: {old_field} -> {new_field}")

            # Handle field removal
            elif rule.get("removed"):
                del migrated_data[old_field]
                logger.debug(f"Removed: {old_field}")

                # Apply replacement if provided
                if rule.get("replace_with"):
                    migrated_data.update(rule["replace_with"])

            # Handle value mapping
            elif rule.get("value_mapping"):
                value_map = rule["value_mapping"]
                if old_value in value_map:
                    migrated_data[old_field] = value_map[old_value]
                    logger.debug(f"Mapped: {old_field} {old_value} -> {value_map[old_value]}")

            # Handle warnings
            if rule.get("warning"):
                logger.warning(f"Migration warning for {old_field}: {rule['warning']}")

        return migrated_data

    async def get_migration_plan(
        self,
        system_type: str,
        from_version: str,
        to_version: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Get detailed migration plan without executing

        Args:
            system_type: System type
            from_version: Source version
            to_version: Target version
            model: Model name

        Returns:
            Migration plan with steps and changes

        Example:
            plan = await handler.get_migration_plan(
                system_type='odoo',
                from_version='13.0',
                to_version='19.0',
                model='res.partner'
            )
        """
        migration_path = get_migration_path(from_version, to_version)

        if not migration_path:
            return {
                "success": False,
                "error": "Invalid version range"
            }

        steps = []
        total_changes = {
            "renamed_fields": [],
            "removed_fields": [],
            "value_mappings": [],
            "warnings": []
        }

        for i in range(len(migration_path) - 1):
            current_version = migration_path[i]
            next_version = migration_path[i + 1]
            migration_key = f"{current_version}_to_{next_version}"

            rules = self._get_migration_rules(system_type, model, migration_key)

            if rules:
                step_changes = self._analyze_rules(rules)
                steps.append({
                    "from": current_version,
                    "to": next_version,
                    "changes": step_changes
                })

                # Aggregate changes
                total_changes["renamed_fields"].extend(step_changes["renamed_fields"])
                total_changes["removed_fields"].extend(step_changes["removed_fields"])
                total_changes["value_mappings"].extend(step_changes["value_mappings"])
                total_changes["warnings"].extend(step_changes["warnings"])

        return {
            "success": True,
            "from_version": from_version,
            "to_version": to_version,
            "migration_path": migration_path,
            "steps": steps,
            "total_changes": total_changes,
            "complexity": len(steps)
        }

    def _analyze_rules(self, rules: Dict[str, Any]) -> Dict[str, List]:
        """Analyze rules and categorize changes"""
        changes = {
            "renamed_fields": [],
            "removed_fields": [],
            "value_mappings": [],
            "warnings": []
        }

        for field, rule in rules.items():
            if rule.get("rename_to"):
                changes["renamed_fields"].append({
                    "old": field,
                    "new": rule["rename_to"]
                })
            if rule.get("removed"):
                changes["removed_fields"].append(field)
            if rule.get("value_mapping"):
                changes["value_mappings"].append({
                    "field": field,
                    "mapping": rule["value_mapping"]
                })
            if rule.get("warning"):
                changes["warnings"].append({
                    "field": field,
                    "message": rule["warning"]
                })

        return changes

    def get_supported_versions(self, system_type: str = "odoo") -> List[str]:
        """
        Get list of supported versions

        Returns:
            List of version strings
        """
        if system_type == "odoo":
            from app.services.odoo_versions import ODOO_VERSION_SEQUENCE
            return ODOO_VERSION_SEQUENCE

        return []

    async def validate_version(
        self,
        system_type: str,
        version: str
    ) -> bool:
        """
        Validate if version is supported

        Args:
            system_type: System type
            version: Version string

        Returns:
            True if supported
        """
        supported = self.get_supported_versions(system_type)
        return version in supported
