"""
Odoo XML-RPC Client Utility.

Provides a wrapper for interacting with Odoo via XML-RPC API.
"""

import xmlrpc.client
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OdooConfig:
    """Odoo connection configuration."""
    url: str
    database: str
    username: str
    password: str


class OdooClient:
    """
    Odoo XML-RPC client for CRUD operations.

    Provides methods to create, read, update, and delete records
    in Odoo via the External API.
    """

    def __init__(self, config: OdooConfig):
        """
        Initialize Odoo client.

        Args:
            config: OdooConfig with connection details.
        """
        self.config = config
        self.uid: Optional[int] = None
        self._common: Optional[xmlrpc.client.ServerProxy] = None
        self._models: Optional[xmlrpc.client.ServerProxy] = None

    def connect(self) -> bool:
        """
        Connect and authenticate with Odoo.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            self._common = xmlrpc.client.ServerProxy(
                f'{self.config.url}/xmlrpc/2/common'
            )
            version = self._common.version()
            logger.info(f"Connected to Odoo {version.get('server_version')}")

            self.uid = self._common.authenticate(
                self.config.database,
                self.config.username,
                self.config.password,
                {}
            )

            if not self.uid:
                logger.error("Authentication failed")
                return False

            self._models = xmlrpc.client.ServerProxy(
                f'{self.config.url}/xmlrpc/2/object'
            )
            logger.info(f"Authenticated as user {self.uid}")
            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def _execute(
        self,
        model: str,
        method: str,
        args: List[Any],
        kwargs: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a method on an Odoo model.

        Args:
            model: Odoo model name (e.g., 'res.partner').
            method: Method to call (e.g., 'create', 'search').
            args: Positional arguments.
            kwargs: Keyword arguments.

        Returns:
            Result from Odoo.

        Raises:
            RuntimeError: If not connected.
        """
        if not self._models or not self.uid:
            raise RuntimeError("Not connected to Odoo. Call connect() first.")

        kwargs = kwargs or {}
        return self._models.execute_kw(
            self.config.database,
            self.uid,
            self.config.password,
            model,
            method,
            args,
            kwargs
        )

    def create(self, model: str, values: Dict[str, Any]) -> int:
        """
        Create a new record.

        Args:
            model: Odoo model name.
            values: Field values for the new record.

        Returns:
            ID of the created record.
        """
        record_id = self._execute(model, 'create', [values])
        logger.info(f"Created {model} record with ID {record_id}")
        return record_id

    def create_many(self, model: str, records: List[Dict[str, Any]]) -> List[int]:
        """
        Create multiple records.

        Args:
            model: Odoo model name.
            records: List of field value dictionaries.

        Returns:
            List of created record IDs.
        """
        ids = []
        for values in records:
            record_id = self.create(model, values)
            ids.append(record_id)
        return ids

    def search(
        self,
        model: str,
        domain: List[Any],
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[int]:
        """
        Search for records matching a domain.

        Args:
            model: Odoo model name.
            domain: Search domain (e.g., [('name', '=', 'Test')]).
            limit: Maximum records to return.
            offset: Number of records to skip.

        Returns:
            List of matching record IDs.
        """
        kwargs = {'offset': offset}
        if limit:
            kwargs['limit'] = limit
        return self._execute(model, 'search', [domain], kwargs)

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Read records by ID.

        Args:
            model: Odoo model name.
            ids: List of record IDs to read.
            fields: Specific fields to read (None for all).

        Returns:
            List of record dictionaries.
        """
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        return self._execute(model, 'read', [ids], kwargs)

    def search_read(
        self,
        model: str,
        domain: List[Any],
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search and read records in one call.

        Args:
            model: Odoo model name.
            domain: Search domain.
            fields: Specific fields to read.
            limit: Maximum records to return.
            offset: Number of records to skip.
            order: Sort order (e.g., 'name asc').

        Returns:
            List of matching record dictionaries.
        """
        kwargs = {'offset': offset}
        if fields:
            kwargs['fields'] = fields
        if limit:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order
        return self._execute(model, 'search_read', [domain], kwargs)

    def write(self, model: str, ids: List[int], values: Dict[str, Any]) -> bool:
        """
        Update existing records.

        Args:
            model: Odoo model name.
            ids: List of record IDs to update.
            values: Field values to update.

        Returns:
            True if successful.
        """
        result = self._execute(model, 'write', [ids, values])
        logger.info(f"Updated {model} records {ids}")
        return result

    def delete(self, model: str, ids: List[int]) -> bool:
        """
        Delete records.

        Args:
            model: Odoo model name.
            ids: List of record IDs to delete.

        Returns:
            True if successful.
        """
        result = self._execute(model, 'unlink', [ids])
        logger.info(f"Deleted {model} records {ids}")
        return result

    def get_fields(
        self,
        model: str,
        attributes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get field definitions for a model.

        Args:
            model: Odoo model name.
            attributes: Field attributes to return
                       (e.g., ['string', 'type', 'required']).

        Returns:
            Dictionary of field definitions.
        """
        kwargs = {}
        if attributes:
            kwargs['attributes'] = attributes
        return self._execute(model, 'fields_get', [], kwargs)

    def search_count(self, model: str, domain: List[Any]) -> int:
        """
        Count records matching a domain.

        Args:
            model: Odoo model name.
            domain: Search domain.

        Returns:
            Number of matching records.
        """
        return self._execute(model, 'search_count', [domain])

    def get_or_create(
        self,
        model: str,
        domain: List[Any],
        values: Dict[str, Any]
    ) -> Tuple[int, bool]:
        """
        Get existing record or create new one.

        Args:
            model: Odoo model name.
            domain: Search domain to find existing record.
            values: Values for creating new record if not found.

        Returns:
            Tuple of (record_id, created) where created is True if new.
        """
        existing = self.search(model, domain, limit=1)
        if existing:
            return existing[0], False
        return self.create(model, values), True

    def get_id_by_name(
        self,
        model: str,
        name: str,
        field: str = 'name'
    ) -> Optional[int]:
        """
        Get record ID by name field.

        Args:
            model: Odoo model name.
            name: Value to search for.
            field: Field to search (default 'name').

        Returns:
            Record ID or None if not found.
        """
        ids = self.search(model, [(field, '=', name)], limit=1)
        return ids[0] if ids else None


def get_odoo_client() -> OdooClient:
    """
    Get configured Odoo client instance.

    Returns:
        Configured OdooClient ready to connect.
    """
    config = OdooConfig(
        url='http://localhost:8069',
        database='odoo-ailabs',
        username='alfred.anyan@gmail.com',
        password='Dolt702%'
    )
    return OdooClient(config)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    client = get_odoo_client()
    if client.connect():
        print("Connection successful!")

        # List models and counts
        models = ['res.partner', 'hr.employee', 'project.project', 'crm.lead', 'hr.expense']
        for model in models:
            count = client.search_count(model, [])
            print(f"  {model}: {count} records")
    else:
        print("Connection failed!")
