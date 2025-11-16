"""
Query Optimizer for Odoo Operations

Optimizes Odoo queries to prevent N+1 queries and improve performance
"""
from typing import List, Dict, Any, Optional
from loguru import logger


class QueryOptimizer:
    """
    Optimize Odoo queries for better performance

    Features:
    - Field optimization to prevent N+1 queries
    - Domain optimization for better indexing
    - Limit optimization to prevent huge queries
    - Related field expansion
    """

    # Common relation fields and their suggested expansions
    RELATION_FIELDS = {
        'partner_id': ['partner_id.name', 'partner_id.email', 'partner_id.phone', 'partner_id.vat'],
        'user_id': ['user_id.name', 'user_id.email', 'user_id.login'],
        'company_id': ['company_id.name', 'company_id.currency_id'],
        'product_id': ['product_id.name', 'product_id.default_code', 'product_id.barcode'],
        'category_id': ['category_id.name', 'category_id.complete_name'],
        'product_tmpl_id': ['product_tmpl_id.name', 'product_tmpl_id.default_code'],
        'warehouse_id': ['warehouse_id.name', 'warehouse_id.code'],
        'location_id': ['location_id.name', 'location_id.complete_name'],
        'picking_type_id': ['picking_type_id.name', 'picking_type_id.code'],
        'currency_id': ['currency_id.name', 'currency_id.symbol'],
        'pricelist_id': ['pricelist_id.name', 'pricelist_id.currency_id'],
        'sale_order_id': ['sale_order_id.name', 'sale_order_id.state'],
        'purchase_order_id': ['purchase_order_id.name', 'purchase_order_id.state'],
        'invoice_id': ['invoice_id.name', 'invoice_id.state'],
        'account_id': ['account_id.name', 'account_id.code'],
        'journal_id': ['journal_id.name', 'journal_id.code'],
        'tax_id': ['tax_id.name', 'tax_id.amount'],
        'state_id': ['state_id.name', 'state_id.code'],
        'country_id': ['country_id.name', 'country_id.code'],
    }

    # Indexed fields that should be prioritized in domain
    INDEXED_FIELDS = [
        'id', 'create_date', 'write_date', 'name',
        'active', 'state', 'company_id'
    ]

    # Maximum limits for different operations
    MAX_LIMITS = {
        'search_read': 200,
        'read': 100,
        'search': 500,
        'name_search': 50,
        'web_search_read': 200,
        'fields_get': None,  # No limit
        'search_count': None,  # No limit
    }

    @staticmethod
    def optimize_fields(
        model: str,
        fields: Optional[List[str]],
        expand_relations: bool = True
    ) -> Optional[List[str]]:
        """
        Optimize fields list by adding related fields to prevent N+1 queries

        Args:
            model: Odoo model name
            fields: List of fields to read
            expand_relations: Whether to expand relation fields

        Returns:
            Optimized fields list or None if all fields requested

        Example:
            Input: ['id', 'name', 'partner_id']
            Output: ['id', 'name', 'partner_id', 'partner_id.name', 'partner_id.email', ...]
        """
        if not fields:
            # None means all fields
            return None

        if not expand_relations:
            return fields

        optimized_fields = set(fields)

        # Add related fields for many2one relations
        for field in fields:
            if field in QueryOptimizer.RELATION_FIELDS:
                related_fields = QueryOptimizer.RELATION_FIELDS[field]
                optimized_fields.update(related_fields)
                logger.debug(
                    f"Expanded {field} with related fields: {related_fields}"
                )

        return list(optimized_fields)

    @staticmethod
    def optimize_domain(domain: List) -> List:
        """
        Optimize search domain for better performance

        Odoo evaluates domains left-to-right, so putting indexed fields first
        improves query performance.

        Args:
            domain: Odoo domain (list of tuples/lists)

        Returns:
            Optimized domain

        Example:
            Input: [('name', 'ilike', 'test'), ('id', '>', 100), '|', ('active', '=', True)]
            Output: [('id', '>', 100), ('active', '=', True), '|', ('name', 'ilike', 'test')]
        """
        if not domain:
            return []

        indexed_criteria = []
        other_criteria = []
        operators = []

        for criterion in domain:
            # Check if it's an operator ('&', '|', '!')
            if isinstance(criterion, str):
                operators.append(criterion)
            # Check if it's a criterion tuple/list
            elif isinstance(criterion, (list, tuple)) and len(criterion) >= 3:
                field_name = criterion[0]
                if field_name in QueryOptimizer.INDEXED_FIELDS:
                    indexed_criteria.append(criterion)
                else:
                    other_criteria.append(criterion)
            else:
                # Keep unknown formats as is
                other_criteria.append(criterion)

        # Reconstruct domain: operators first, then indexed, then others
        optimized = []

        # Add operators at the beginning (they affect the criteria that follow)
        optimized.extend(operators)

        # Add indexed criteria first for better performance
        optimized.extend(indexed_criteria)

        # Add other criteria
        optimized.extend(other_criteria)

        if optimized != domain:
            logger.debug(f"Optimized domain from {domain} to {optimized}")

        return optimized

    @staticmethod
    def optimize_limit(
        limit: Optional[int],
        operation: str,
        custom_max: Optional[int] = None
    ) -> Optional[int]:
        """
        Optimize limit to prevent huge queries

        Args:
            limit: Requested limit
            operation: Operation name
            custom_max: Custom maximum limit (overrides default)

        Returns:
            Optimized limit

        Example:
            optimize_limit(1000, 'search_read') -> 200
        """
        max_limit = custom_max or QueryOptimizer.MAX_LIMITS.get(operation)

        # If operation has no limit restriction
        if max_limit is None:
            return limit

        # If no limit specified, use max
        if limit is None:
            return max_limit

        # Return minimum of requested and max
        optimized = min(limit, max_limit)

        if optimized != limit:
            logger.debug(
                f"Optimized limit for {operation} from {limit} to {optimized}"
            )

        return optimized

    @staticmethod
    def optimize_order(order: Optional[str], model: str) -> Optional[str]:
        """
        Optimize order clause for better performance

        Args:
            order: Order clause (e.g., "name ASC, id DESC")
            model: Odoo model name

        Returns:
            Optimized order clause
        """
        if not order:
            # Use default order (id DESC for most cases)
            return "id DESC"

        # Ensure indexed fields are used when possible
        return order

    @staticmethod
    def should_cache(operation: str) -> bool:
        """
        Determine if operation result should be cached

        Args:
            operation: Operation name

        Returns:
            True if should cache
        """
        cacheable_operations = [
            'search_read', 'read', 'search', 'search_count',
            'fields_get', 'name_search', 'name_get',
            'web_search_read', 'web_read'
        ]

        return operation in cacheable_operations

    @staticmethod
    def get_cache_ttl(operation: str) -> int:
        """
        Get cache TTL for operation

        Args:
            operation: Operation name

        Returns:
            TTL in seconds
        """
        cache_ttls = {
            'fields_get': 3600,      # 1 hour - field metadata rarely changes
            'name_search': 600,       # 10 minutes
            'name_get': 600,          # 10 minutes
            'search_count': 300,      # 5 minutes
            'search_read': 300,       # 5 minutes
            'read': 300,              # 5 minutes
            'search': 300,            # 5 minutes
            'web_search_read': 300,   # 5 minutes
            'web_read': 300,          # 5 minutes
        }

        return cache_ttls.get(operation, 300)  # Default 5 minutes

    @staticmethod
    def generate_cache_key(
        system_id: str,
        operation: str,
        model: str,
        **kwargs
    ) -> str:
        """
        Generate cache key for operation

        Args:
            system_id: System identifier
            operation: Operation name
            model: Model name
            **kwargs: Additional parameters

        Returns:
            Cache key string
        """
        import hashlib
        import json

        # Create deterministic key from parameters
        params = {
            'system_id': system_id,
            'operation': operation,
            'model': model,
            **kwargs
        }

        # Sort for consistency
        sorted_params = json.dumps(params, sort_keys=True)

        # Create hash
        hash_value = hashlib.md5(sorted_params.encode()).hexdigest()[:16]

        # Return formatted key
        return f"odoo:{system_id}:{operation}:{model}:{hash_value}"

    @staticmethod
    def get_invalidation_patterns(
        system_id: str,
        model: str,
        operation: str
    ) -> List[str]:
        """
        Get cache invalidation patterns for write operations

        Args:
            system_id: System identifier
            model: Model name
            operation: Operation that was performed (create, write, unlink)

        Returns:
            List of cache key patterns to invalidate

        Example:
            For write on 'product.product':
            - 'odoo:system1:search_read:product.product:*'
            - 'odoo:system1:read:product.product:*'
            - 'odoo:system1:search:product.product:*'
        """
        patterns = []

        # Invalidate all cached queries for this model
        cache_operations = [
            'search_read', 'read', 'search', 'search_count',
            'name_search', 'name_get', 'web_search_read', 'web_read'
        ]

        for cache_op in cache_operations:
            pattern = f"odoo:{system_id}:{cache_op}:{model}:*"
            patterns.append(pattern)

        return patterns


# Singleton instance
query_optimizer = QueryOptimizer()
