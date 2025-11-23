#!/usr/bin/env python3
"""
Script to add rate limiting to all Odoo endpoints
This script adds rate limiting decorators to all endpoints in Odoo routes
"""
import re
from pathlib import Path

# Rate limit mapping for each route file
RATE_LIMIT_MAP = {
    "search.py": {
        "search": "odoo_search",
        "search_read": "odoo_search",
        "search_count": "odoo_search",
    },
    "crud.py": {
        "create": "odoo_create",
        "read": "odoo_read",
        "write": "odoo_write",
        "unlink": "odoo_delete",
    },
    "advanced.py": {
        "onchange": "odoo_advanced",
        "read_group": "odoo_advanced",
        "copy": "odoo_advanced",
        "exists": "odoo_utility",
    },
    "names.py": {
        "name_get": "odoo_name",
        "name_search": "odoo_name",
        "name_create": "odoo_create",
    },
    "views.py": {
        "fields_view_get": "odoo_view",
        "load_views": "odoo_view",
        "get_views": "odoo_view",
    },
    "web.py": {
        "web_read": "odoo_web",
        "web_save": "odoo_web",
        "web_search_read": "odoo_web",
    },
    "permissions.py": {
        "check_access_rights": "odoo_permission",
        "check_field_access": "odoo_permission",
    },
    "utility.py": {
        "fields_get": "odoo_utility",
        "default_get": "odoo_utility",
        "get_metadata": "odoo_utility",
    },
    "methods.py": {
        "call_method": "odoo_method",
        "call_kw": "odoo_method",
        "execute": "odoo_method",
    },
}

def add_rate_limiting_to_file(file_path: Path):
    """Add rate limiting to a route file"""
    if file_path.name not in RATE_LIMIT_MAP:
        return False
    
    content = file_path.read_text()
    original_content = content
    
    # Check if rate limiter is already imported
    if "from app.core.rate_limiter import" not in content:
        # Add import after other imports
        import_line = "from app.core.rate_limiter import limiter, get_rate_limit\n"
        # Find the last import line
        lines = content.split('\n')
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                last_import_idx = i
        
        lines.insert(last_import_idx + 1, import_line)
        content = '\n'.join(lines)
    
    # Add rate limiting to each endpoint
    for endpoint_name, rate_limit_type in RATE_LIMIT_MAP[file_path.name].items():
        # Pattern to find @router.post("/endpoint_name"...
        pattern = rf'(@router\.(post|get|put|delete)\("\/{endpoint_name}"[^)]*\)\s*\n(?:.*\n)*?async def {endpoint_name}[^(]*\()'
        
        # Check if rate limiting already exists
        if f'@limiter.limit(get_rate_limit("{rate_limit_type}"))' in content:
            continue
        
        # Find the function definition
        func_pattern = rf'(@router\.(post|get|put|delete)\("\/{endpoint_name}"[^)]*\))\s*\n(async def {endpoint_name}[^(]*\()'
        
        def add_decorator(match):
            decorator = match.group(1)
            func_def = match.group(3)
            # Check if Request is already in parameters
            if 'request: Request' not in func_def:
                # Add Request as first parameter
                func_def = func_def.replace('(', '(request: Request, ', 1)
            return f'{decorator}\n@limiter.limit(get_rate_limit("{rate_limit_type}"))\n{func_def}'
        
        content = re.sub(func_pattern, add_decorator, content)
    
    if content != original_content:
        file_path.write_text(content)
        return True
    return False

if __name__ == "__main__":
    routes_dir = Path(__file__).parent.parent / "app" / "api" / "routes" / "odoo"
    
    for file_name in RATE_LIMIT_MAP.keys():
        file_path = routes_dir / file_name
        if file_path.exists():
            if add_rate_limiting_to_file(file_path):
                print(f"✅ Added rate limiting to {file_name}")
            else:
                print(f"⚠️  No changes needed for {file_name}")
        else:
            print(f"❌ File not found: {file_name}")

