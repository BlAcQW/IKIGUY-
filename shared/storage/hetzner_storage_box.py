"""
Hetzner Storage Box Service.

Provides unified access to Hetzner Storage Box (WebDAV/SFTP/Samba) for file storage
across all KasaAI applications.

Credentials:
- Username: u497034-sub1
- Host: u497034-sub1.your-storagebox.de
- Samba: \\\\u497034-sub1.your-storagebox.de\\u497034-sub1
- Password: Stored in environment variable HETZNER_STORAGE_PASSWORD

Supported Protocols:
- WebDAV (HTTPS) - Primary, recommended for programmatic access
- SFTP (SSH) - Alternative, good for large files
- Samba/CIFS - For Windows integration

Features:
- Multi-protocol support (WebDAV, SFTP, Samba)
- Automatic directory creation
- File upload/download with progress tracking
- Metadata management
- Path validation and sanitization
- Error handling with retries
"""

import os
import logging
from typing import Optional, Dict, Any, List, BinaryIO, Callable
from pathlib import Path
from datetime import datetime
from enum import Enum
import asyncio
from urllib.parse import quote

# WebDAV client
try:
    from webdav3.client import Client as WebDAVClient
    WEBDAV_AVAILABLE = True
except ImportError:
    WEBDAV_AVAILABLE = False
    logging.warning("webdav3 not installed. Install with: pip install webdavclient3")

# SFTP client
try:
    import paramiko
    from stat import S_ISDIR
    SFTP_AVAILABLE = True
except ImportError:
    SFTP_AVAILABLE = False
    logging.warning("paramiko not installed. Install with: pip install paramiko")

# SMB client (optional, for Windows integration)
try:
    from smb.SMBConnection import SMBConnection
    SMB_AVAILABLE = True
except ImportError:
    SMB_AVAILABLE = False
    logging.warning("pysmb not installed. Install with: pip install pysmb")


logger = logging.getLogger(__name__)


class StorageProtocol(Enum):
    """Storage access protocols."""
    WEBDAV = "webdav"
    SFTP = "sftp"
    SAMBA = "samba"


class HetznerStorageBoxError(Exception):
    """Base exception for Hetzner Storage Box errors."""
    pass


class HetznerStorageBox:
    """
    Hetzner Storage Box client supporting WebDAV, SFTP, and Samba protocols.

    Primary protocol: WebDAV (HTTPS) for reliability and ease of use.
    Fallback: SFTP for large files or when WebDAV is unavailable.

    Example:
        ```python
        storage = HetznerStorageBox()
        await storage.connect()

        # Upload file
        await storage.upload_file(
            local_path="/path/to/file.pdf",
            remote_path="documents/file.pdf"
        )

        # Download file
        await storage.download_file(
            remote_path="documents/file.pdf",
            local_path="/path/to/downloaded.pdf"
        )

        # List files
        files = await storage.list_files("documents/")
        ```
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        protocol: StorageProtocol = StorageProtocol.WEBDAV,
        base_path: str = ""
    ):
        """
        Initialize Hetzner Storage Box client.

        Args:
            username: Storage box username (default: from env HETZNER_STORAGE_USERNAME)
            password: Storage box password (default: from env HETZNER_STORAGE_PASSWORD)
            host: Storage box host (default: from env HETZNER_STORAGE_HOST)
            protocol: Protocol to use (webdav, sftp, or samba)
            base_path: Base path for all operations (e.g., "kasaai/")
        """
        self.username = username or os.getenv("HETZNER_STORAGE_USERNAME", "u497034-sub1")
        self.password = password or os.getenv("HETZNER_STORAGE_PASSWORD")
        self.host = host or os.getenv("HETZNER_STORAGE_HOST", "u497034-sub1.your-storagebox.de")
        self.protocol = protocol
        self.base_path = base_path.strip("/")

        # Client instances
        self.webdav_client: Optional[WebDAVClient] = None
        self.sftp_client: Optional[paramiko.SFTPClient] = None
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.smb_conn: Optional[SMBConnection] = None

        self.connected = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        if not self.password:
            raise HetznerStorageBoxError("Storage password not provided. Set HETZNER_STORAGE_PASSWORD environment variable.")

    async def connect(self) -> bool:
        """
        Connect to Hetzner Storage Box using the specified protocol.

        Returns:
            True if connection successful

        Raises:
            HetznerStorageBoxError: If connection fails
        """
        try:
            if self.protocol == StorageProtocol.WEBDAV:
                return await self._connect_webdav()
            elif self.protocol == StorageProtocol.SFTP:
                return await self._connect_sftp()
            elif self.protocol == StorageProtocol.SAMBA:
                return await self._connect_samba()
            else:
                raise HetznerStorageBoxError(f"Unsupported protocol: {self.protocol}")

        except Exception as e:
            self.logger.error(f"Failed to connect to Hetzner Storage Box: {e}")
            raise HetznerStorageBoxError(f"Connection failed: {e}")

    async def _connect_webdav(self) -> bool:
        """Connect using WebDAV protocol."""
        if not WEBDAV_AVAILABLE:
            raise HetznerStorageBoxError("WebDAV client not available. Install with: pip install webdavclient3")

        try:
            options = {
                'webdav_hostname': f"https://{self.host}",
                'webdav_login': self.username,
                'webdav_password': self.password,
                'webdav_timeout': 30,
                'verbose': False
            }

            self.webdav_client = WebDAVClient(options)

            # Test connection
            await asyncio.to_thread(self.webdav_client.list, "/")

            self.connected = True
            self.logger.info(f"Connected to Hetzner Storage Box via WebDAV: {self.host}")
            return True

        except Exception as e:
            raise HetznerStorageBoxError(f"WebDAV connection failed: {e}")

    async def _connect_sftp(self) -> bool:
        """Connect using SFTP protocol."""
        if not SFTP_AVAILABLE:
            raise HetznerStorageBoxError("SFTP client not available. Install with: pip install paramiko")

        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            await asyncio.to_thread(
                self.ssh_client.connect,
                hostname=self.host,
                port=23,  # Hetzner Storage Box SFTP port
                username=self.username,
                password=self.password,
                timeout=30
            )

            self.sftp_client = self.ssh_client.open_sftp()

            self.connected = True
            self.logger.info(f"Connected to Hetzner Storage Box via SFTP: {self.host}")
            return True

        except Exception as e:
            raise HetznerStorageBoxError(f"SFTP connection failed: {e}")

    async def _connect_samba(self) -> bool:
        """Connect using Samba/CIFS protocol."""
        if not SMB_AVAILABLE:
            raise HetznerStorageBoxError("SMB client not available. Install with: pip install pysmb")

        try:
            # Note: SMB connection setup is complex and may require additional configuration
            self.logger.warning("Samba/CIFS protocol is experimental. WebDAV or SFTP recommended.")

            # Placeholder for SMB connection
            # Actual implementation would depend on specific requirements
            raise HetznerStorageBoxError("Samba/CIFS protocol not fully implemented yet")

        except Exception as e:
            raise HetznerStorageBoxError(f"Samba connection failed: {e}")

    async def disconnect(self):
        """Disconnect from storage."""
        try:
            if self.sftp_client:
                self.sftp_client.close()
            if self.ssh_client:
                self.ssh_client.close()
            if self.smb_conn:
                self.smb_conn.close()

            self.connected = False
            self.logger.info("Disconnected from Hetzner Storage Box")

        except Exception as e:
            self.logger.warning(f"Error during disconnect: {e}")

    def _get_remote_path(self, path: str) -> str:
        """
        Get full remote path with base_path prefix.

        For SFTP: Returns relative path (from home directory)
        For WebDAV: Returns absolute path (with leading /)

        Args:
            path: Relative path

        Returns:
            Full remote path
        """
        path = path.strip("/")
        if self.base_path:
            full_path = f"{self.base_path}/{path}"
        else:
            full_path = path

        # SFTP uses relative paths from home directory
        # WebDAV uses absolute paths with leading /
        if self.protocol == StorageProtocol.SFTP:
            return full_path
        else:
            return f"/{full_path}"

    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        overwrite: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Upload file to storage.

        Args:
            local_path: Local file path
            remote_path: Remote file path (relative to base_path)
            overwrite: Whether to overwrite existing file
            progress_callback: Optional callback(bytes_transferred, total_bytes)

        Returns:
            True if upload successful

        Raises:
            HetznerStorageBoxError: If upload fails
        """
        if not self.connected:
            raise HetznerStorageBoxError("Not connected to storage")

        try:
            remote_path = self._get_remote_path(remote_path)

            # Create parent directory if needed
            parent_dir = str(Path(remote_path).parent)
            creation_success = await self.create_directory(parent_dir)
            if not creation_success:
                self.logger.error(f"Directory creation failed for: {parent_dir}")
                raise HetznerStorageBoxError(f"Failed to create directory: {parent_dir}")

            # Check if file exists
            if not overwrite and await self.file_exists(remote_path):
                raise HetznerStorageBoxError(f"File already exists: {remote_path}")

            if self.protocol == StorageProtocol.WEBDAV:
                await asyncio.to_thread(
                    self.webdav_client.upload_sync,
                    remote_path=remote_path,
                    local_path=local_path
                )

            elif self.protocol == StorageProtocol.SFTP:
                await asyncio.to_thread(
                    self.sftp_client.put,
                    localpath=local_path,
                    remotepath=remote_path,
                    callback=progress_callback
                )

            self.logger.info(f"Uploaded file: {local_path} -> {remote_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to upload file: {e}")
            raise HetznerStorageBoxError(f"Upload failed: {e}")

    async def download_file(
        self,
        remote_path: str,
        local_path: str,
        overwrite: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Download file from storage.

        Args:
            remote_path: Remote file path (relative to base_path)
            local_path: Local file path
            overwrite: Whether to overwrite existing local file
            progress_callback: Optional callback(bytes_transferred, total_bytes)

        Returns:
            True if download successful

        Raises:
            HetznerStorageBoxError: If download fails
        """
        if not self.connected:
            raise HetznerStorageBoxError("Not connected to storage")

        try:
            remote_path = self._get_remote_path(remote_path)

            # Check if local file exists
            if not overwrite and os.path.exists(local_path):
                raise HetznerStorageBoxError(f"Local file already exists: {local_path}")

            # Create local parent directory
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            if self.protocol == StorageProtocol.WEBDAV:
                await asyncio.to_thread(
                    self.webdav_client.download_sync,
                    remote_path=remote_path,
                    local_path=local_path
                )

            elif self.protocol == StorageProtocol.SFTP:
                await asyncio.to_thread(
                    self.sftp_client.get,
                    remotepath=remote_path,
                    localpath=local_path,
                    callback=progress_callback
                )

            self.logger.info(f"Downloaded file: {remote_path} -> {local_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to download file: {e}")
            raise HetznerStorageBoxError(f"Download failed: {e}")

    async def download_file_content(self, remote_path: str) -> Optional[bytes]:
        """
        Download file content as bytes (for serving via API).
        
        Args:
            remote_path: Remote file path (relative to base_path)
            
        Returns:
            File content as bytes, or None if not found
            
        Raises:
            HetznerStorageBoxError: If download fails
        """
        if not self.connected:
            raise HetznerStorageBoxError("Not connected to storage")
        
        try:
            remote_path = self._get_remote_path(remote_path)
            
            # Use temp file to download, then read content
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                if self.protocol == StorageProtocol.WEBDAV:
                    await asyncio.to_thread(
                        self.webdav_client.download_sync,
                        remote_path=remote_path,
                        local_path=tmp_path
                    )
                elif self.protocol == StorageProtocol.SFTP:
                    await asyncio.to_thread(
                        self.sftp_client.get,
                        remotepath=remote_path,
                        localpath=tmp_path
                    )
                
                # Read content
                with open(tmp_path, "rb") as f:
                    content = f.read()
                
                return content
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            self.logger.error(f"Failed to download file content: {e}")
            return None

    async def delete_file(self, remote_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            remote_path: Remote file path (relative to base_path)

        Returns:
            True if deletion successful
        """
        if not self.connected:
            raise HetznerStorageBoxError("Not connected to storage")

        try:
            remote_path = self._get_remote_path(remote_path)

            if self.protocol == StorageProtocol.WEBDAV:
                await asyncio.to_thread(
                    self.webdav_client.clean,
                    remote_path
                )

            elif self.protocol == StorageProtocol.SFTP:
                await asyncio.to_thread(
                    self.sftp_client.remove,
                    remote_path
                )

            self.logger.info(f"Deleted file: {remote_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete file: {e}")
            raise HetznerStorageBoxError(f"Delete failed: {e}")

    async def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            remote_path: Remote file path (relative to base_path)

        Returns:
            True if file exists
        """
        if not self.connected:
            raise HetznerStorageBoxError("Not connected to storage")

        try:
            remote_path = self._get_remote_path(remote_path)

            if self.protocol == StorageProtocol.WEBDAV:
                return await asyncio.to_thread(
                    self.webdav_client.check,
                    remote_path
                )

            elif self.protocol == StorageProtocol.SFTP:
                try:
                    await asyncio.to_thread(
                        self.sftp_client.stat,
                        remote_path
                    )
                    return True
                except FileNotFoundError:
                    return False

            return False

        except Exception as e:
            self.logger.debug(f"File check failed: {e}")
            return False

    async def list_files(
        self,
        remote_path: str = "",
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List files in directory.

        Args:
            remote_path: Remote directory path (relative to base_path)
            recursive: Whether to list recursively

        Returns:
            List of file metadata dictionaries
        """
        if not self.connected:
            raise HetznerStorageBoxError("Not connected to storage")

        try:
            remote_path = self._get_remote_path(remote_path)

            files = []

            if self.protocol == StorageProtocol.WEBDAV:
                items = await asyncio.to_thread(
                    self.webdav_client.list,
                    remote_path
                )

                for item in items:
                    if item == '.' or item == '..':
                        continue

                    item_path = f"{remote_path}/{item}".replace("//", "/")
                    info = await asyncio.to_thread(
                        self.webdav_client.info,
                        item_path
                    )

                    files.append({
                        "name": item,
                        "path": item_path,
                        "is_directory": info.get('isdir', False),
                        "size": info.get('size', 0),
                        "modified": info.get('modified', None)
                    })

                    # Recursive listing
                    if recursive and info.get('isdir', False):
                        subfiles = await self.list_files(item_path, recursive=True)
                        files.extend(subfiles)

            elif self.protocol == StorageProtocol.SFTP:
                items = await asyncio.to_thread(
                    self.sftp_client.listdir_attr,
                    remote_path
                )

                for item in items:
                    item_path = f"{remote_path}/{item.filename}".replace("//", "/")
                    is_dir = S_ISDIR(item.st_mode)

                    files.append({
                        "name": item.filename,
                        "path": item_path,
                        "is_directory": is_dir,
                        "size": item.st_size,
                        "modified": datetime.fromtimestamp(item.st_mtime).isoformat()
                    })

                    # Recursive listing
                    if recursive and is_dir:
                        subfiles = await self.list_files(item_path, recursive=True)
                        files.extend(subfiles)

            return files

        except Exception as e:
            self.logger.error(f"Failed to list files: {e}")
            raise HetznerStorageBoxError(f"List failed: {e}")

    async def create_directory(self, remote_path: str) -> bool:
        """
        Create directory in storage.

        Args:
            remote_path: Remote directory path (can be relative or absolute)

        Returns:
            True if creation successful
        """
        if not self.connected:
            raise HetznerStorageBoxError("Not connected to storage")

        try:
            # Only apply base_path if this is a relative path (no leading /)
            if not remote_path.startswith("/"):
                remote_path = self._get_remote_path(remote_path)

            # Check if already exists
            if await self.file_exists(remote_path):
                return True

            if self.protocol == StorageProtocol.WEBDAV:
                # Create parent directories recursively for WebDAV
                parts = remote_path.strip("/").split("/")
                current_path = ""

                for part in parts:
                    current_path += f"/{part}"
                    try:
                        # Check if directory exists
                        exists = await self.file_exists(current_path)
                        if not exists:
                            # Directory doesn't exist, create it
                            await asyncio.to_thread(
                                self.webdav_client.mkdir,
                                current_path
                            )
                            self.logger.info(f"Created directory: {current_path}")

                            # Verify it was created
                            if not await self.file_exists(current_path):
                                raise HetznerStorageBoxError(
                                    f"Failed to create directory (verification failed): {current_path}"
                                )
                    except HetznerStorageBoxError:
                        # Re-raise our own errors
                        raise
                    except Exception as e:
                        # Check if directory exists now (might have been created by another process)
                        if not await self.file_exists(current_path):
                            # Directory still doesn't exist, this is a real error
                            raise HetznerStorageBoxError(
                                f"Failed to create directory {current_path}: {e}"
                            )

            elif self.protocol == StorageProtocol.SFTP:
                # Create parent directories recursively
                # SFTP uses relative paths from home directory
                parts = remote_path.strip("/").split("/")
                current_path = ""

                for part in parts:
                    if current_path:
                        current_path = f"{current_path}/{part}"
                    else:
                        current_path = part
                    try:
                        await asyncio.to_thread(
                            self.sftp_client.stat,
                            current_path
                        )
                    except FileNotFoundError:
                        await asyncio.to_thread(
                            self.sftp_client.mkdir,
                            current_path
                        )

            self.logger.info(f"Verified directory exists: {remote_path}")
            return True

        except HetznerStorageBoxError:
            # Re-raise our specific errors
            raise
        except Exception as e:
            self.logger.error(f"Failed to create directory: {e}")
            raise HetznerStorageBoxError(f"Directory creation failed for {remote_path}: {e}")

    async def get_file_info(self, remote_path: str) -> Dict[str, Any]:
        """
        Get file metadata.

        Args:
            remote_path: Remote file path (relative to base_path)

        Returns:
            File metadata dictionary
        """
        if not self.connected:
            raise HetznerStorageBoxError("Not connected to storage")

        try:
            remote_path = self._get_remote_path(remote_path)

            if self.protocol == StorageProtocol.WEBDAV:
                info = await asyncio.to_thread(
                    self.webdav_client.info,
                    remote_path
                )

                return {
                    "path": remote_path,
                    "is_directory": info.get('isdir', False),
                    "size": info.get('size', 0),
                    "modified": info.get('modified', None),
                    "created": info.get('created', None)
                }

            elif self.protocol == StorageProtocol.SFTP:
                stat = await asyncio.to_thread(
                    self.sftp_client.stat,
                    remote_path
                )

                return {
                    "path": remote_path,
                    "is_directory": S_ISDIR(stat.st_mode),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "accessed": datetime.fromtimestamp(stat.st_atime).isoformat()
                }

        except Exception as e:
            self.logger.error(f"Failed to get file info: {e}")
            raise HetznerStorageBoxError(f"Get info failed: {e}")

    def __enter__(self):
        """Context manager entry."""
        asyncio.run(self.connect())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        asyncio.run(self.disconnect())


# Global storage instance
_storage_instance: Optional[HetznerStorageBox] = None


async def get_storage(
    protocol: StorageProtocol = StorageProtocol.WEBDAV,
    base_path: str = "kasaai"
) -> HetznerStorageBox:
    """
    Get or create global Hetzner Storage Box instance.

    Args:
        protocol: Protocol to use (webdav, sftp, samba)
        base_path: Base path for operations

    Returns:
        HetznerStorageBox instance
    """
    global _storage_instance

    if _storage_instance is None or not _storage_instance.connected:
        _storage_instance = HetznerStorageBox(
            protocol=protocol,
            base_path=base_path
        )
        await _storage_instance.connect()

    return _storage_instance
