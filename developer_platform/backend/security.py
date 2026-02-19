"""
Security module for Developer Platform.

Handles mTLS client configuration, JWT token management, and security middleware
for secure communication with the Core Backend.
"""

import ssl
import certifi
import httpx
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
import os
import logging

logger = logging.getLogger(__name__)


class MTLSClient:
    """mTLS client for secure communication with Core Backend."""
    
    def __init__(self, core_url: str, cert_path: str, key_path: str, ca_path: str):
        """
        Initialize mTLS client.
        
        Args:
            core_url: Core Backend URL
            cert_path: Path to client certificate
            key_path: Path to client private key
            ca_path: Path to CA certificate
        """
        self.core_url = core_url.rstrip('/')
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            
    async def _create_client(self):
        """Create httpx client with mTLS configuration."""
        # Load certificates
        cert = (self.cert_path, self.key_path)
        
        # Create SSL context
        ssl_context = ssl.create_default_context(cafile=self.ca_path)
        ssl_context.load_cert_chain(self.cert_path, self.key_path)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        
        # Create client with custom SSL context
        self._client = httpx.AsyncClient(
            verify=ssl_context,
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
    async def request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """
        Make authenticated request to Core Backend.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            headers: Additional headers
            
        Returns:
            httpx.Response: Response from Core Backend
        """
        if not self._client:
            await self._create_client()
            
        url = f"{self.core_url}{endpoint}"
        request_headers = {
            "Content-Type": "application/json",
            "User-Agent": "KasaAI-DeveloperPlatform/1.0",
            **(headers or {})
        }
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=data,
                headers=request_headers
            )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise


class JWTManager:
    """JWT token management for service-to-service authentication."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT manager.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm to use
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        
    def create_service_token(
        self, 
        tenant_id: UUID, 
        scopes: list[str], 
        expires_in: int = 3600
    ) -> str:
        """
        Create a service JWT token for Core Backend communication.
        
        Args:
            tenant_id: Tenant ID for the request
            scopes: List of allowed scopes
            expires_in: Token expiration time in seconds
            
        Returns:
            str: JWT token
        """
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "developer_platform",
            "iss": "developer_platform",
            "aud": "core_backend",
            "tenant_id": str(tenant_id),
            "scopes": scopes,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
            "type": "service"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Dict containing token payload
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")


class SecurityMiddleware:
    """Security middleware for API endpoints."""
    
    def __init__(self, jwt_manager: JWTManager):
        """
        Initialize security middleware.
        
        Args:
            jwt_manager: JWT manager instance
        """
        self.jwt_manager = jwt_manager
        
    async def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Verify API key and return key details.
        
        Args:
            api_key: API key to verify
            
        Returns:
            Dict containing API key details
        """
        # Import here to avoid circular imports
        from .storage import APIKeyStore
        
        # Get API key from database
        store = APIKeyStore()
        key = store.get_by_secret(api_key)
        
        if not key:
            raise ValueError("Invalid API key")
            
        if not key.enabled:
            raise ValueError("API key is disabled")
            
        return {
            "key_id": str(key.id),
            "tenant_id": str(key.tenant_id),
            "scopes": key.scopes or []
        }
        
    def inject_tenant_context(self, tenant_id: str) -> Dict[str, str]:
        """
        Create headers for tenant context injection.
        
        Args:
            tenant_id: Tenant ID to inject
            
        Returns:
            Dict containing tenant context headers
        """
        return {
            "x-tenant-id": tenant_id,
            "x-request-id": f"req-{datetime.now().timestamp()}"
        }


class CertificateManager:
    """Certificate management for mTLS."""
    
    @staticmethod
    def generate_self_signed_cert(
        common_name: str,
        cert_path: str,
        key_path: str,
        days_valid: int = 365
    ):
        """
        Generate self-signed certificate for development.
        
        Args:
            common_name: Common name for the certificate
            cert_path: Path to save certificate
            key_path: Path to save private key
            days_valid: Certificate validity in days
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "KasaAI Developer Platform"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Development"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=days_valid)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress("127.0.0.1")
            ]),
            critical=False,
        ).sign(private_key, None)
        
        # Save certificate
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
            
        # Save private key
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        logger.info(f"Generated self-signed certificate: {cert_path}")
        logger.info(f"Generated private key: {key_path}")


# Global instances
jwt_manager = JWTManager(os.getenv("JWT_SECRET_KEY", "dev-secret-key"))
security_middleware = SecurityMiddleware(jwt_manager) 