"""
Universal Schema for common business entities

These schemas provide a unified interface across different ERP/CRM systems
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


class UniversalPartner(BaseModel):
    """
    Universal Partner/Contact schema

    Compatible with:
    - Odoo: res.partner
    - SAP: Business Partner
    - Salesforce: Account/Contact
    """
    id: Optional[int] = None
    name: str = Field(..., description="Partner name")
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None

    # Address
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None

    # Business info
    is_company: bool = False
    vat: Optional[str] = Field(None, description="Tax ID")
    company_registry: Optional[str] = None

    # Categories
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None

    # Metadata
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UniversalProduct(BaseModel):
    """
    Universal Product schema

    Compatible with:
    - Odoo: product.product / product.template
    - SAP: Material Master
    - Salesforce: Product
    """
    id: Optional[int] = None
    name: str = Field(..., description="Product name")
    display_name: Optional[str] = None
    description: Optional[str] = None
    description_sale: Optional[str] = None

    # Identification
    default_code: Optional[str] = Field(None, description="Internal reference/SKU")
    barcode: Optional[str] = None

    # Type
    type: str = Field(default="product", description="product/service/consu")
    categ: Optional[str] = Field(None, description="Product category")

    # Pricing
    list_price: Decimal = Field(default=Decimal("0.0"), description="Sales price")
    standard_price: Decimal = Field(default=Decimal("0.0"), description="Cost price")
    currency: str = Field(default="USD")

    # Inventory
    qty_available: Optional[Decimal] = Field(None, description="Quantity on hand")
    virtual_available: Optional[Decimal] = Field(None, description="Forecasted quantity")
    uom: Optional[str] = Field(None, description="Unit of measure")

    # Sales/Purchase
    sale_ok: bool = True
    purchase_ok: bool = True

    # Metadata
    active: bool = True
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UniversalSaleOrderLine(BaseModel):
    """Universal Sale Order Line"""
    id: Optional[int] = None
    product_id: int
    product_name: str
    description: Optional[str] = None
    quantity: Decimal = Field(default=Decimal("1.0"))
    unit_price: Decimal = Field(default=Decimal("0.0"))
    discount: Decimal = Field(default=Decimal("0.0"))
    tax_amount: Decimal = Field(default=Decimal("0.0"))
    subtotal: Decimal = Field(default=Decimal("0.0"))
    total: Decimal = Field(default=Decimal("0.0"))


class UniversalSaleOrder(BaseModel):
    """
    Universal Sale Order schema

    Compatible with:
    - Odoo: sale.order
    - SAP: Sales Order
    - Salesforce: Opportunity/Order
    """
    id: Optional[int] = None
    name: str = Field(..., description="Order reference")
    partner_id: int = Field(..., description="Customer ID")
    partner_name: str

    # Dates
    date_order: datetime = Field(default_factory=datetime.utcnow)
    validity_date: Optional[date] = None
    delivery_date: Optional[date] = None

    # Status
    state: str = Field(default="draft", description="draft/sent/sale/done/cancel")
    invoice_status: Optional[str] = Field(None, description="to_invoice/invoiced/no")

    # Lines
    order_lines: List[UniversalSaleOrderLine] = Field(default_factory=list)

    # Amounts
    amount_untaxed: Decimal = Field(default=Decimal("0.0"))
    amount_tax: Decimal = Field(default=Decimal("0.0"))
    amount_total: Decimal = Field(default=Decimal("0.0"))
    currency: str = Field(default="USD")

    # Payment
    payment_term: Optional[str] = None
    payment_status: Optional[str] = None

    # Additional info
    notes: Optional[str] = None
    customer_reference: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[int] = Field(None, description="Salesperson ID")
    team_id: Optional[int] = Field(None, description="Sales team ID")

    class Config:
        from_attributes = True


class UniversalInvoice(BaseModel):
    """
    Universal Invoice schema

    Compatible with:
    - Odoo: account.move (invoice)
    - SAP: Invoice
    - Salesforce: Invoice
    """
    id: Optional[int] = None
    name: str = Field(..., description="Invoice number")
    partner_id: int
    partner_name: str

    # Type
    move_type: str = Field(default="out_invoice", description="out_invoice/in_invoice/out_refund/in_refund")

    # Dates
    invoice_date: date
    invoice_date_due: Optional[date] = None

    # Status
    state: str = Field(default="draft", description="draft/posted/cancel")
    payment_state: str = Field(default="not_paid", description="not_paid/in_payment/paid/partial")

    # Amounts
    amount_untaxed: Decimal = Field(default=Decimal("0.0"))
    amount_tax: Decimal = Field(default=Decimal("0.0"))
    amount_total: Decimal = Field(default=Decimal("0.0"))
    amount_residual: Decimal = Field(default=Decimal("0.0"), description="Amount due")
    currency: str = Field(default="USD")

    # Reference
    ref: Optional[str] = Field(None, description="Reference/Description")
    payment_reference: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UniversalInventoryMove(BaseModel):
    """
    Universal Inventory/Stock Move schema

    Compatible with:
    - Odoo: stock.move / stock.picking
    - SAP: Goods Movement
    """
    id: Optional[int] = None
    name: str = Field(..., description="Move reference")
    product_id: int
    product_name: str

    # Locations
    location_from: str
    location_to: str

    # Quantity
    quantity: Decimal = Field(default=Decimal("1.0"))
    uom: str = Field(default="Unit")

    # Type
    picking_type: str = Field(default="internal", description="internal/incoming/outgoing")

    # Status
    state: str = Field(default="draft", description="draft/confirmed/assigned/done/cancel")

    # Dates
    scheduled_date: Optional[datetime] = None
    date_done: Optional[datetime] = None

    # Reference
    origin: Optional[str] = Field(None, description="Source document")
    partner_id: Optional[int] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UniversalUser(BaseModel):
    """
    Universal User schema

    Compatible with most systems' user models
    """
    id: Optional[int] = None
    name: str
    login: str
    email: Optional[EmailStr] = None
    active: bool = True

    # Groups/Roles
    groups: List[str] = Field(default_factory=list)
    is_admin: bool = False

    # Company
    company_id: Optional[int] = None
    company_name: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
