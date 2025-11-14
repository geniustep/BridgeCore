"""
Odoo Version Migration Rules (13.0 -> 19.0)

Comprehensive migration rules for all Odoo versions from 13 to 19
"""

ODOO_VERSION_RULES = {
    "res.partner": {
        # Odoo 13 -> 14
        "13.0_to_14.0": {
            "customer": {
                "rename_to": None,
                "replace_with": None,  # Deprecated but still works in 14
                "warning": "customer field deprecated, use type field instead"
            }
        },

        # Odoo 14 -> 15
        "14.0_to_15.0": {
            # No major changes in res.partner
        },

        # Odoo 15 -> 16
        "15.0_to_16.0": {
            "customer": {
                "rename_to": None,
                "replace_with": None,  # Completely removed
                "removed": True
            },
            "supplier": {
                "rename_to": None,
                "replace_with": None,
                "removed": True
            }
        },

        # Odoo 16 -> 17
        "16.0_to_17.0": {
            "phone": {
                "rename_to": None,
                "warning": "phone field structure changed"
            }
        },

        # Odoo 17 -> 18
        "17.0_to_18.0": {
            "phone": {
                "rename_to": "phone_primary"
            },
            "mobile": {
                "rename_to": "phone_secondary"
            }
        },

        # Odoo 18 -> 19
        "18.0_to_19.0": {
            # Enhanced contact management
            "street": {
                "transform": "enhanced_address"
            }
        },

        # Direct migrations for common paths
        "13.0_to_16.0": {
            "customer": {
                "rename_to": None,
                "replace_with": None,
                "removed": True
            },
            "supplier": {
                "rename_to": None,
                "replace_with": None,
                "removed": True
            }
        },

        "13.0_to_18.0": {
            "customer": {
                "rename_to": None,
                "removed": True
            },
            "phone": {
                "rename_to": "phone_primary"
            },
            "mobile": {
                "rename_to": "phone_secondary"
            }
        },

        "13.0_to_19.0": {
            "customer": {
                "rename_to": None,
                "removed": True
            },
            "supplier": {
                "rename_to": None,
                "removed": True
            },
            "phone": {
                "rename_to": "phone_primary"
            },
            "mobile": {
                "rename_to": "phone_secondary"
            }
        },

        "16.0_to_18.0": {
            "phone": {
                "rename_to": "phone_primary"
            },
            "mobile": {
                "rename_to": "phone_secondary"
            }
        },

        "16.0_to_19.0": {
            "phone": {
                "rename_to": "phone_primary"
            },
            "mobile": {
                "rename_to": "phone_secondary"
            }
        }
    },

    "product.product": {
        # Odoo 13 -> 14
        "13.0_to_14.0": {
            "sale_delay": {
                "rename_to": "sale_delay",
                "warning": "Field behavior changed"
            }
        },

        # Odoo 14 -> 15
        "14.0_to_15.0": {},

        # Odoo 15 -> 16
        "15.0_to_16.0": {
            "sale_delay": {
                "rename_to": "delivery_delay"
            }
        },

        # Odoo 16 -> 17
        "16.0_to_17.0": {
            "type": {
                "value_mapping": {
                    "product": "storable",
                    "consu": "consumable"
                }
            }
        },

        # Odoo 17 -> 18
        "17.0_to_18.0": {
            "list_price": {
                "warning": "Multi-currency support enhanced"
            }
        },

        # Odoo 18 -> 19
        "18.0_to_19.0": {
            "barcode": {
                "warning": "Barcode validation enhanced"
            }
        },

        # Direct migrations
        "13.0_to_16.0": {
            "sale_delay": {
                "rename_to": "delivery_delay"
            }
        },

        "13.0_to_19.0": {
            "sale_delay": {
                "rename_to": "delivery_delay"
            },
            "type": {
                "value_mapping": {
                    "product": "storable",
                    "consu": "consumable"
                }
            }
        },

        "16.0_to_19.0": {
            "type": {
                "value_mapping": {
                    "product": "storable",
                    "consu": "consumable"
                }
            }
        }
    },

    "sale.order": {
        # Odoo 13 -> 14
        "13.0_to_14.0": {},

        # Odoo 14 -> 15
        "14.0_to_15.0": {},

        # Odoo 15 -> 16
        "15.0_to_16.0": {
            "validity_date": {
                "rename_to": "expiration_date"
            }
        },

        # Odoo 16 -> 17
        "16.0_to_17.0": {
            "payment_term_id": {
                "warning": "Payment terms structure enhanced"
            }
        },

        # Odoo 17 -> 18
        "17.0_to_18.0": {
            "state": {
                "value_mapping": {
                    "manual": "sale",  # Removed state
                    "progress": "sale"
                }
            }
        },

        # Odoo 18 -> 19
        "18.0_to_19.0": {
            "incoterm": {
                "rename_to": "incoterm_id",
                "transform": "to_many2one"
            }
        },

        # Direct migrations
        "13.0_to_16.0": {
            "validity_date": {
                "rename_to": "expiration_date"
            }
        },

        "13.0_to_19.0": {
            "validity_date": {
                "rename_to": "expiration_date"
            },
            "state": {
                "value_mapping": {
                    "manual": "sale",
                    "progress": "sale"
                }
            },
            "incoterm": {
                "rename_to": "incoterm_id"
            }
        },

        "16.0_to_19.0": {
            "state": {
                "value_mapping": {
                    "manual": "sale",
                    "progress": "sale"
                }
            },
            "incoterm": {
                "rename_to": "incoterm_id"
            }
        }
    },

    "account.move": {
        # Invoice changes across versions
        "13.0_to_14.0": {},

        "14.0_to_15.0": {
            "journal_id": {
                "warning": "Journal selection changed"
            }
        },

        "15.0_to_16.0": {
            "invoice_payment_state": {
                "rename_to": "payment_state"
            }
        },

        "16.0_to_17.0": {},

        "17.0_to_18.0": {
            "invoice_origin": {
                "rename_to": "ref"
            }
        },

        "18.0_to_19.0": {
            "amount_total": {
                "warning": "Tax calculation method changed"
            }
        },

        # Direct migrations
        "13.0_to_19.0": {
            "invoice_payment_state": {
                "rename_to": "payment_state"
            },
            "invoice_origin": {
                "rename_to": "ref"
            }
        }
    }
}

# Version sequence for auto-migration
ODOO_VERSION_SEQUENCE = [
    "13.0", "14.0", "15.0", "16.0", "17.0", "18.0", "19.0"
]

def get_migration_path(from_version: str, to_version: str) -> list:
    """
    Get the migration path between two versions

    Args:
        from_version: Source version (e.g., "13.0")
        to_version: Target version (e.g., "19.0")

    Returns:
        List of version steps

    Example:
        get_migration_path("13.0", "19.0")
        # Returns: ["13.0", "14.0", "15.0", "16.0", "17.0", "18.0", "19.0"]
    """
    try:
        from_idx = ODOO_VERSION_SEQUENCE.index(from_version)
        to_idx = ODOO_VERSION_SEQUENCE.index(to_version)

        if from_idx > to_idx:
            raise ValueError("Downgrade not supported")

        return ODOO_VERSION_SEQUENCE[from_idx:to_idx + 1]
    except ValueError as e:
        logger.error(f"Invalid version in migration path: {e}")
        return []
