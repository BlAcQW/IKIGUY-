"""
Authentication service using Supabase Auth.

Handles phone OTP authentication and JWT token generation.
"""

from typing import Optional, Dict
from supabase import create_client, Client
from datetime import datetime, timedelta
import jwt
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service for handling OTP-based phone auth via Supabase.

    Attributes:
        supabase: Supabase client instance
    """

    def __init__(self):
        """Initialize service (client created lazily)."""
        self._supabase: Optional[Client] = None

    @property
    def supabase(self) -> Client:
        """
        Get Supabase client, creating it if necessary.

        Returns:
            Client: Supabase client instance
        """
        if self._supabase is None:
            self._supabase = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
        return self._supabase

    async def send_otp(self, phone: str) -> Dict[str, any]:
        """
        Send OTP code to phone number.

        Args:
            phone: Phone number in E.164 format (e.g., +233201234567)

        Returns:
            dict: Response with success status

        Raises:
            Exception: If OTP sending fails
        """
        try:
            logger.info(f"Sending OTP to {phone}")

            response = self.supabase.auth.sign_in_with_otp({
                "phone": phone,
                "options": {
                    "should_create_user": True
                }
            })

            logger.info(f"OTP sent successfully to {phone}")

            return {
                "success": True,
                "message": "OTP sent successfully",
                "phone": phone
            }

        except Exception as e:
            logger.error(f"Failed to send OTP to {phone}: {str(e)}")
            raise Exception(f"Failed to send OTP: {str(e)}")

    async def verify_otp(self, phone: str, token: str) -> Dict[str, any]:
        """
        Verify OTP code and return JWT token.

        Args:
            phone: Phone number in E.164 format
            token: OTP code received by user

        Returns:
            dict: User data and access token

        Raises:
            Exception: If OTP verification fails
        """
        try:
            logger.info(f"Verifying OTP for {phone}")

            response = self.supabase.auth.verify_otp({
                "phone": phone,
                "token": token,
                "type": "sms"
            })

            if not response.user:
                raise Exception("OTP verification failed")

            # Generate our own JWT for API access
            access_token = self._create_access_token(
                data={"sub": response.user.id, "phone": phone}
            )

            logger.info(f"OTP verified successfully for {phone}")

            return {
                "success": True,
                "user_id": response.user.id,
                "phone": phone,
                "access_token": access_token,
                "token_type": "bearer"
            }

        except Exception as e:
            logger.error(f"Failed to verify OTP for {phone}: {str(e)}")
            raise Exception(f"Failed to verify OTP: {str(e)}")

    def _create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.

        Args:
            data: Token payload data
            expires_delta: Custom expiration time

        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )

        return encoded_jwt

    def decode_token(self, token: str) -> Dict[str, any]:
        """
        Decode and verify JWT token.

        Supports both Supabase-issued tokens and app-issued tokens.

        Args:
            token: JWT token string

        Returns:
            dict: Token payload

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        # Try Supabase JWT secret first (for tokens from Supabase auth)
        try:
            payload = jwt.decode(
                token,
                settings.supabase_secret_key,
                algorithms=[settings.algorithm],
                options={"verify_aud": False}  # Supabase tokens have different audience
            )
            logger.debug("Token validated with Supabase JWT secret")
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.PyJWTError as e:
            # If Supabase validation fails, try app secret key (for OTP tokens)
            logger.debug(f"Supabase validation failed, trying app secret: {str(e)}")
            try:
                payload = jwt.decode(
                    token,
                    settings.secret_key,
                    algorithms=[settings.algorithm]
                )
                logger.debug("Token validated with app secret key")
                return payload
            except jwt.ExpiredSignatureError:
                raise jwt.InvalidTokenError("Token has expired")
            except jwt.PyJWTError as app_error:
                raise jwt.InvalidTokenError(f"Invalid token: {str(app_error)}")


# Global auth service instance
auth_service = AuthService()
