"""
Barcode Integration API

Endpoints for barcode scanning and product lookup
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from loguru import logger

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.system_service import SystemService
from app.api.routes.systems import get_system_service

router = APIRouter(prefix="/barcode", tags=["Barcode"])


@router.get("/{system_id}/lookup/{barcode}")
async def lookup_product_by_barcode(
    system_id: str,
    barcode: str,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Lookup product by barcode

    Args:
        system_id: System identifier
        barcode: Product barcode

    Returns:
        Product information

    Example:
        ```
        GET /barcode/odoo-prod/lookup/6281234567890
        ```

        Response:
        ```json
        {
            "success": true,
            "product": {
                "id": 123,
                "name": "Product Name",
                "barcode": "6281234567890",
                "list_price": 99.99,
                "qty_available": 50
            }
        }
        ```
    """
    try:
        # Search for product by barcode
        products = await service.read_records(
            user_id=current_user.id,
            system_id=system_id,
            model="product.product",
            domain=[["barcode", "=", barcode]],
            fields=[
                "id", "name", "barcode", "default_code",
                "list_price", "standard_price",
                "qty_available", "type",
                "categ_id", "uom_id"
            ],
            limit=1
        )

        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No product found with barcode: {barcode}"
            )

        product = products[0]

        return {
            "success": True,
            "product": product
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Barcode lookup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{system_id}/scan")
async def process_barcode_scan(
    system_id: str,
    barcode: str,
    action: str = "lookup",  # lookup, add_to_cart, inventory_check
    quantity: float = 1.0,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Process barcode scan with action

    Args:
        system_id: System identifier
        barcode: Scanned barcode
        action: Action to perform (lookup, add_to_cart, inventory_check)
        quantity: Quantity for inventory operations

    Returns:
        Action result

    Example:
        ```json
        POST /barcode/odoo-prod/scan
        {
            "barcode": "6281234567890",
            "action": "inventory_check",
            "quantity": 1.0
        }
        ```
    """
    try:
        # Lookup product first
        products = await service.read_records(
            user_id=current_user.id,
            system_id=system_id,
            model="product.product",
            domain=[["barcode", "=", barcode]],
            fields=["id", "name", "barcode", "qty_available", "list_price"],
            limit=1
        )

        if not products:
            return {
                "success": False,
                "error": "Product not found",
                "barcode": barcode
            }

        product = products[0]

        result = {
            "success": True,
            "product": product,
            "action": action
        }

        # Perform action
        if action == "lookup":
            # Just return product info
            pass

        elif action == "add_to_cart":
            # Add to cart (would need cart session management)
            result["added_to_cart"] = True
            result["quantity"] = quantity

        elif action == "inventory_check":
            # Return inventory info
            result["available_qty"] = product.get("qty_available", 0)
            result["in_stock"] = product.get("qty_available", 0) > 0

        return result

    except Exception as e:
        logger.error(f"Barcode scan error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{system_id}/search")
async def search_products_by_code(
    system_id: str,
    code: Optional[str] = None,
    barcode: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Search products by code, barcode, or name

    Args:
        system_id: System identifier
        code: Internal reference code
        barcode: Product barcode
        name: Product name (partial match)
        limit: Maximum results

    Returns:
        List of matching products

    Example:
        ```
        GET /barcode/odoo-prod/search?name=laptop&limit=5
        ```
    """
    try:
        domain = []

        if code:
            domain.append(["default_code", "ilike", code])
        if barcode:
            domain.append(["barcode", "ilike", barcode])
        if name:
            domain.append(["name", "ilike", name])

        if not domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one search parameter is required"
            )

        products = await service.read_records(
            user_id=current_user.id,
            system_id=system_id,
            model="product.product",
            domain=domain,
            fields=[
                "id", "name", "barcode", "default_code",
                "list_price", "qty_available"
            ],
            limit=limit
        )

        return {
            "success": True,
            "count": len(products),
            "products": products
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
