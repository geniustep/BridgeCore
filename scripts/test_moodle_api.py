#!/usr/bin/env python3
"""
Script to test Moodle API endpoints with a real Moodle server

Usage:
    python scripts/test_moodle_api.py --moodle-url https://lms.example.com --token YOUR_TOKEN
    python scripts/test_moodle_api.py --moodle-url https://lms.example.com --token YOUR_TOKEN --tenant-id TENANT_UUID
"""

import asyncio
import httpx
import json
import sys
import argparse
from typing import Optional, Dict, Any
from datetime import datetime


class MoodleAPITester:
    """Test Moodle API endpoints"""
    
    def __init__(self, base_url: str, moodle_url: str, moodle_token: str, tenant_id: Optional[str] = None, tenant_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.moodle_url = moodle_url.rstrip('/')
        self.moodle_token = moodle_token
        self.tenant_id = tenant_id
        self.tenant_token = tenant_token
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    def log_result(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if data and not success:
            print(f"   Data: {json.dumps(data, indent=2, default=str)}")
            
    async def test_health(self):
        """Test API health endpoint"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log_result("Health Check", True, "API is healthy", response.json())
                return True
            else:
                self.log_result("Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Health Check", False, str(e))
            return False
            
    async def login_tenant_user(self, email: str, password: str) -> Optional[str]:
        """Login as tenant user and get token"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/tenant/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                self.log_result("Tenant Login", True, "Login successful")
                return token
            else:
                self.log_result("Tenant Login", False, f"Status: {response.status_code}", response.json())
                return None
        except Exception as e:
            self.log_result("Tenant Login", False, str(e))
            return None
            
    async def setup_moodle_connection(self, admin_token: str) -> bool:
        """Setup Moodle connection for tenant via admin API"""
        if not self.tenant_id:
            self.log_result("Setup Moodle Connection", False, "Tenant ID is required")
            return False
            
        try:
            # First, check if Moodle system exists
            response = await self.client.get(
                f"{self.base_url}/admin/systems",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code != 200:
                self.log_result("Setup Moodle Connection", False, "Failed to get systems list")
                return False
                
            systems = response.json()
            moodle_system = next((s for s in systems if s.get("system_type") == "moodle"), None)
            
            if not moodle_system:
                self.log_result("Setup Moodle Connection", False, "Moodle system not found in catalog")
                return False
                
            system_id = moodle_system["id"]
            
            # Create tenant system connection
            connection_config = {
                "url": self.moodle_url,
                "token": self.moodle_token,
                "service": "moodle_mobile_app"
            }
            
            response = await self.client.post(
                f"{self.base_url}/admin/systems/tenant-connections",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "tenant_id": self.tenant_id,
                    "system_id": str(system_id),
                    "connection_config": connection_config,
                    "is_active": True,
                    "is_primary": False
                }
            )
            
            if response.status_code in [200, 201]:
                self.log_result("Setup Moodle Connection", True, "Connection created successfully", response.json())
                return True
            else:
                self.log_result("Setup Moodle Connection", False, f"Status: {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_result("Setup Moodle Connection", False, str(e))
            return False
            
    async def test_moodle_site_info(self, token: str):
        """Test Moodle site info endpoint"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/moodle/site-info",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                self.log_result("Moodle Site Info", True, "Retrieved site info", data)
                return True
            else:
                self.log_result("Moodle Site Info", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Moodle Site Info", False, str(e))
            return False
            
    async def test_moodle_health(self, token: str):
        """Test Moodle health endpoint"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/moodle/health",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                self.log_result("Moodle Health", True, f"Status: {data.get('status')}", data)
                return True
            else:
                self.log_result("Moodle Health", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Moodle Health", False, str(e))
            return False
            
    async def test_get_courses(self, token: str):
        """Test get courses endpoint"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/moodle/courses",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                courses = data if isinstance(data, list) else data.get("courses", [])
                self.log_result("Get Courses", True, f"Retrieved {len(courses)} courses", {"count": len(courses)})
                return True
            else:
                self.log_result("Get Courses", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Get Courses", False, str(e))
            return False
            
    async def test_get_course_by_id(self, token: str, course_id: int):
        """Test get course by ID endpoint"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/moodle/courses/{course_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                self.log_result("Get Course by ID", True, f"Retrieved course {course_id}", data)
                return True
            else:
                self.log_result("Get Course by ID", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Get Course by ID", False, str(e))
            return False
            
    async def test_get_users(self, token: str):
        """Test get users endpoint"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/moodle/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                users = data if isinstance(data, list) else data.get("users", [])
                self.log_result("Get Users", True, f"Retrieved {len(users)} users", {"count": len(users)})
                return True
            else:
                self.log_result("Get Users", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Get Users", False, str(e))
            return False
            
    async def test_moodle_call_function(self, token: str, function_name: str, params: Dict = None):
        """Test generic Moodle function call"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/moodle/call",
                headers={"Authorization": f"Bearer {token}"},
                params={"function_name": function_name},
                json=params or {}
            )
            if response.status_code == 200:
                data = response.json()
                self.log_result(f"Call Function: {function_name}", True, "Function called successfully", data)
                return True
            else:
                self.log_result(f"Call Function: {function_name}", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result(f"Call Function: {function_name}", False, str(e))
            return False
            
    async def run_all_tests(self, tenant_email: str = None, tenant_password: str = None, admin_token: str = None):
        """Run all tests"""
        print("=" * 60)
        print("Moodle API Integration Test")
        print("=" * 60)
        print(f"BridgeCore URL: {self.base_url}")
        print(f"Moodle URL: {self.moodle_url}")
        print("=" * 60)
        print()
        
        # Test 1: Health check
        await self.test_health()
        print()
        
        # Test 2: Setup Moodle connection (if admin token provided)
        if admin_token and self.tenant_id:
            await self.setup_moodle_connection(admin_token)
            print()
            
        # Test 3: Get tenant token
        token = self.tenant_token
        if not token and tenant_email and tenant_password:
            token = await self.login_tenant_user(tenant_email, tenant_password)
            print()
            
        if not token:
            print("❌ Cannot proceed without tenant token")
            print("   Please provide --tenant-token or --tenant-email and --tenant-password")
            return
            
        # Test 4: Moodle site info
        await self.test_moodle_site_info(token)
        print()
        
        # Test 5: Moodle health
        await self.test_moodle_health(token)
        print()
        
        # Test 6: Get courses
        await self.test_get_courses(token)
        print()
        
        # Test 7: Get users
        await self.test_get_users(token)
        print()
        
        # Test 8: Test generic function call
        await self.test_moodle_call_function(token, "core_webservice_get_site_info")
        print()
        
        # Summary
        print("=" * 60)
        print("Test Summary")
        print("=" * 60)
        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        print()
        
        if passed < total:
            print("Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed == total


async def main():
    parser = argparse.ArgumentParser(description="Test Moodle API endpoints")
    parser.add_argument("--base-url", default="http://localhost:8001", help="BridgeCore API base URL")
    parser.add_argument("--moodle-url", required=True, help="Moodle instance URL")
    parser.add_argument("--token", required=True, help="Moodle web services token")
    parser.add_argument("--tenant-id", help="Tenant ID for connection setup")
    parser.add_argument("--tenant-token", help="Tenant authentication token")
    parser.add_argument("--tenant-email", help="Tenant user email for login")
    parser.add_argument("--tenant-password", help="Tenant user password for login")
    parser.add_argument("--admin-token", help="Admin token for setting up connections")
    
    args = parser.parse_args()
    
    async with MoodleAPITester(
        base_url=args.base_url,
        moodle_url=args.moodle_url,
        moodle_token=args.token,
        tenant_id=args.tenant_id,
        tenant_token=args.tenant_token
    ) as tester:
        success = await tester.run_all_tests(
            tenant_email=args.tenant_email,
            tenant_password=args.tenant_password,
            admin_token=args.admin_token
        )
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

