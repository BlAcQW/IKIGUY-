#!/usr/bin/env python3
"""
ERP to Odoo Migration Script.

Migrates data from custom ERP (MongoDB) to Odoo 17 via XML-RPC API.

Entities migrated:
- Customers → res.partner
- Employees → hr.employee
- Projects → project.project
- Opportunities → crm.lead
- Expenses → hr.expense
"""

import asyncio
import logging
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path

from odoo_client import OdooClient, get_odoo_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/erp?authSource=admin"

# Migration mapping storage
MIGRATION_LOG_PATH = Path(__file__).parent / "migration_log.json"


class MigrationLog:
    """Tracks migration mappings between ERP and Odoo IDs."""

    def __init__(self):
        self.mappings: Dict[str, Dict[str, int]] = {
            "customers": {},
            "employees": {},
            "projects": {},
            "opportunities": {},
            "expenses": {},
            "departments": {},
            "expense_products": {},
        }
        self.errors: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        """Load existing mappings from file."""
        if MIGRATION_LOG_PATH.exists():
            try:
                with open(MIGRATION_LOG_PATH, 'r') as f:
                    data = json.load(f)
                    self.mappings = data.get('mappings', self.mappings)
                    self.errors = data.get('errors', [])
                logger.info(f"Loaded migration log from {MIGRATION_LOG_PATH}")
            except Exception as e:
                logger.warning(f"Failed to load migration log: {e}")

    def save(self):
        """Save mappings to file."""
        with open(MIGRATION_LOG_PATH, 'w') as f:
            json.dump({
                'mappings': self.mappings,
                'errors': self.errors,
                'updated_at': datetime.now().isoformat()
            }, f, indent=2)
        logger.info(f"Saved migration log to {MIGRATION_LOG_PATH}")

    def add_mapping(self, entity_type: str, erp_id: str, odoo_id: int):
        """Add a mapping between ERP and Odoo IDs."""
        self.mappings[entity_type][erp_id] = odoo_id

    def get_odoo_id(self, entity_type: str, erp_id: str) -> Optional[int]:
        """Get Odoo ID for an ERP ID."""
        return self.mappings[entity_type].get(erp_id)

    def add_error(self, entity_type: str, erp_id: str, error: str):
        """Log a migration error."""
        self.errors.append({
            'entity_type': entity_type,
            'erp_id': erp_id,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })


class ERPToOdooMigration:
    """
    Handles migration of ERP data to Odoo.

    Migrates in dependency order:
    1. Customers (res.partner)
    2. Departments (hr.department)
    3. Expense Products (product.product)
    4. Employees (hr.employee)
    5. Projects (project.project)
    6. Opportunities (crm.lead)
    7. Expenses (hr.expense)
    """

    def __init__(self):
        self.odoo: Optional[OdooClient] = None
        self.mongo_client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.log = MigrationLog()

    async def connect(self) -> bool:
        """Connect to both databases."""
        # Connect to Odoo
        self.odoo = get_odoo_client()
        if not self.odoo.connect():
            logger.error("Failed to connect to Odoo")
            return False

        # Connect to MongoDB
        self.mongo_client = AsyncIOMotorClient(MONGODB_URL)
        self.db = self.mongo_client.get_database('erp')
        logger.info("Connected to MongoDB (ERP)")
        return True

    async def close(self):
        """Close database connections."""
        if self.mongo_client:
            self.mongo_client.close()
        self.log.save()

    def _format_date(self, d: Any) -> Optional[str]:
        """Format date for Odoo (YYYY-MM-DD)."""
        if d is None:
            return None
        if isinstance(d, datetime):
            return d.strftime('%Y-%m-%d')
        if isinstance(d, date):
            return d.strftime('%Y-%m-%d')
        if isinstance(d, str):
            return d[:10] if len(d) >= 10 else d
        return None

    async def migrate_customers(self) -> int:
        """
        Migrate customers to res.partner.

        Returns:
            Number of customers migrated.
        """
        logger.info("=== Migrating Customers ===")
        cursor = self.db.customers.find({"is_active": True})
        customers = await cursor.to_list(length=1000)

        migrated = 0
        for cust in customers:
            erp_id = cust.get('id', str(cust['_id']))

            # Skip if already migrated
            if self.log.get_odoo_id('customers', erp_id):
                logger.info(f"  Skipping customer {erp_id} (already migrated)")
                continue

            try:
                # Determine name
                if cust.get('company_name'):
                    name = cust['company_name']
                    is_company = True
                else:
                    name = f"{cust.get('first_name', '')} {cust.get('last_name', '')}".strip()
                    is_company = False

                # Build Odoo values
                values = {
                    'name': name or 'Unknown Customer',
                    'email': cust.get('email'),
                    'phone': cust.get('phone'),
                    'street': cust.get('street_address'),
                    'city': cust.get('city'),
                    'zip': cust.get('postal_code'),
                    'is_company': is_company,
                    'customer_rank': 1,  # Mark as customer
                }

                # Remove None values
                values = {k: v for k, v in values.items() if v is not None}

                odoo_id = self.odoo.create('res.partner', values)
                self.log.add_mapping('customers', erp_id, odoo_id)
                migrated += 1
                logger.info(f"  Created customer: {name} (ERP:{erp_id} → Odoo:{odoo_id})")

            except Exception as e:
                logger.error(f"  Failed to migrate customer {erp_id}: {e}")
                self.log.add_error('customers', erp_id, str(e))

        logger.info(f"Customers migrated: {migrated}/{len(customers)}")
        return migrated

    async def setup_departments(self) -> Dict[str, int]:
        """
        Create departments in Odoo based on ERP employee departments.

        Returns:
            Mapping of department name to Odoo ID.
        """
        logger.info("=== Setting up Departments ===")

        # Get unique departments from employees
        cursor = self.db.employees.find({"is_active": True})
        employees = await cursor.to_list(length=1000)
        departments = set(emp.get('department', 'General') for emp in employees)

        dept_map = {}
        for dept_name in departments:
            if not dept_name:
                dept_name = 'General'

            # Check if exists
            existing = self.odoo.search('hr.department', [('name', '=', dept_name)], limit=1)
            if existing:
                dept_map[dept_name] = existing[0]
                logger.info(f"  Department exists: {dept_name} (ID: {existing[0]})")
            else:
                odoo_id = self.odoo.create('hr.department', {'name': dept_name})
                dept_map[dept_name] = odoo_id
                logger.info(f"  Created department: {dept_name} (ID: {odoo_id})")
                self.log.add_mapping('departments', dept_name, odoo_id)

        return dept_map

    async def setup_expense_products(self) -> Dict[str, int]:
        """
        Create expense category products in Odoo.

        Returns:
            Mapping of category name to product ID.
        """
        logger.info("=== Setting up Expense Categories ===")

        # Get unique categories from expenses
        cursor = self.db.expenses.find({"is_active": True})
        expenses = await cursor.to_list(length=1000)
        categories = set(exp.get('category', 'General') for exp in expenses)

        cat_map = {}
        for cat_name in categories:
            if not cat_name:
                cat_name = 'General Expense'

            # Check if exists
            existing = self.odoo.search('product.product', [
                ('name', '=', cat_name),
                ('can_be_expensed', '=', True)
            ], limit=1)

            if existing:
                cat_map[cat_name] = existing[0]
                logger.info(f"  Expense product exists: {cat_name} (ID: {existing[0]})")
            else:
                try:
                    odoo_id = self.odoo.create('product.product', {
                        'name': cat_name,
                        'can_be_expensed': True,
                        'type': 'service',
                        'list_price': 0.0,
                    })
                    cat_map[cat_name] = odoo_id
                    logger.info(f"  Created expense product: {cat_name} (ID: {odoo_id})")
                    self.log.add_mapping('expense_products', cat_name, odoo_id)
                except Exception as e:
                    logger.warning(f"  Failed to create expense product {cat_name}: {e}")
                    # Use default if creation fails
                    default = self.odoo.search('product.product', [
                        ('can_be_expensed', '=', True)
                    ], limit=1)
                    if default:
                        cat_map[cat_name] = default[0]

        return cat_map

    async def migrate_employees(self, dept_map: Dict[str, int]) -> int:
        """
        Migrate employees to hr.employee.

        Args:
            dept_map: Department name to Odoo ID mapping.

        Returns:
            Number of employees migrated.
        """
        logger.info("=== Migrating Employees ===")
        cursor = self.db.employees.find({"is_active": True})
        employees = await cursor.to_list(length=1000)

        migrated = 0
        for emp in employees:
            erp_id = emp.get('id', str(emp['_id']))

            # Skip if already migrated
            if self.log.get_odoo_id('employees', erp_id):
                logger.info(f"  Skipping employee {erp_id} (already migrated)")
                continue

            try:
                name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
                dept_name = emp.get('department', 'General')

                values = {
                    'name': name or 'Unknown Employee',
                    'work_email': emp.get('email'),
                    'work_phone': emp.get('phone'),
                    'job_title': emp.get('position'),
                    'department_id': dept_map.get(dept_name),
                }

                # Remove None values
                values = {k: v for k, v in values.items() if v is not None}

                odoo_id = self.odoo.create('hr.employee', values)
                self.log.add_mapping('employees', erp_id, odoo_id)
                migrated += 1
                logger.info(f"  Created employee: {name} (ERP:{erp_id} → Odoo:{odoo_id})")

            except Exception as e:
                logger.error(f"  Failed to migrate employee {erp_id}: {e}")
                self.log.add_error('employees', erp_id, str(e))

        logger.info(f"Employees migrated: {migrated}/{len(employees)}")
        return migrated

    async def migrate_projects(self) -> int:
        """
        Migrate projects to project.project.

        Returns:
            Number of projects migrated.
        """
        logger.info("=== Migrating Projects ===")
        cursor = self.db.projects.find({"is_active": True})
        projects = await cursor.to_list(length=1000)

        migrated = 0
        for proj in projects:
            erp_id = proj.get('id', str(proj['_id']))

            # Skip if already migrated
            if self.log.get_odoo_id('projects', erp_id):
                logger.info(f"  Skipping project {erp_id} (already migrated)")
                continue

            try:
                # Build description with project code
                description = proj.get('description', '') or ''
                if proj.get('project_code'):
                    description = f"[{proj['project_code']}] {description}"

                values = {
                    'name': proj.get('project_name') or 'Unnamed Project',
                    'description': description or None,
                    'date_start': self._format_date(proj.get('start_date')),
                    'date': self._format_date(proj.get('end_date')),
                }

                # Link to customer if exists
                customer_erp_id = proj.get('customer_id')
                if customer_erp_id:
                    partner_id = self.log.get_odoo_id('customers', customer_erp_id)
                    if partner_id:
                        values['partner_id'] = partner_id

                # Remove None values
                values = {k: v for k, v in values.items() if v is not None}

                odoo_id = self.odoo.create('project.project', values)
                self.log.add_mapping('projects', erp_id, odoo_id)
                migrated += 1
                logger.info(f"  Created project: {proj.get('project_name')} (ERP:{erp_id} → Odoo:{odoo_id})")

            except Exception as e:
                logger.error(f"  Failed to migrate project {erp_id}: {e}")
                self.log.add_error('projects', erp_id, str(e))

        logger.info(f"Projects migrated: {migrated}/{len(projects)}")
        return migrated

    async def migrate_opportunities(self) -> int:
        """
        Migrate opportunities to crm.lead.

        Returns:
            Number of opportunities migrated.
        """
        logger.info("=== Migrating Opportunities ===")
        cursor = self.db.opportunities.find({"is_active": True})
        opportunities = await cursor.to_list(length=1000)

        # Get CRM stages for mapping
        stages = self.odoo.search_read('crm.stage', [], fields=['id', 'name'])
        stage_map = {s['name'].lower(): s['id'] for s in stages}

        # Map ERP stages to Odoo stages
        erp_to_odoo_stage = {
            'prospecting': stage_map.get('new', stage_map.get('leads', 1)),
            'qualification': stage_map.get('qualified', stage_map.get('new', 1)),
            'proposal': stage_map.get('proposition', stage_map.get('qualified', 1)),
            'negotiation': stage_map.get('negotiation', stage_map.get('proposition', 1)),
            'closed_won': stage_map.get('won', stage_map.get('negotiation', 1)),
            'closed_lost': stage_map.get('lost', 1),
        }

        migrated = 0
        for opp in opportunities:
            erp_id = opp.get('id', str(opp['_id']))

            # Skip if already migrated
            if self.log.get_odoo_id('opportunities', erp_id):
                logger.info(f"  Skipping opportunity {erp_id} (already migrated)")
                continue

            try:
                # Determine stage
                erp_stage = opp.get('stage', 'prospecting').lower()
                stage_id = erp_to_odoo_stage.get(erp_stage, 1)

                values = {
                    'name': opp.get('name') or 'Unnamed Opportunity',
                    'type': 'opportunity',  # Not a lead
                    'expected_revenue': float(opp.get('amount', 0)),
                    'probability': float(opp.get('probability', 10)),
                    'description': opp.get('description'),
                    'stage_id': stage_id,
                }

                # Format deadline
                deadline = self._format_date(opp.get('expected_close_date'))
                if deadline:
                    values['date_deadline'] = deadline

                # Link to customer if exists
                customer_erp_id = opp.get('customer_id')
                if customer_erp_id:
                    partner_id = self.log.get_odoo_id('customers', customer_erp_id)
                    if partner_id:
                        values['partner_id'] = partner_id

                # Remove None values
                values = {k: v for k, v in values.items() if v is not None}

                odoo_id = self.odoo.create('crm.lead', values)
                self.log.add_mapping('opportunities', erp_id, odoo_id)
                migrated += 1
                logger.info(f"  Created opportunity: {opp.get('name')} (ERP:{erp_id} → Odoo:{odoo_id})")

            except Exception as e:
                logger.error(f"  Failed to migrate opportunity {erp_id}: {e}")
                self.log.add_error('opportunities', erp_id, str(e))

        logger.info(f"Opportunities migrated: {migrated}/{len(opportunities)}")
        return migrated

    async def migrate_expenses(self, product_map: Dict[str, int]) -> int:
        """
        Migrate expenses to hr.expense.

        Args:
            product_map: Category name to product ID mapping.

        Returns:
            Number of expenses migrated.
        """
        logger.info("=== Migrating Expenses ===")
        cursor = self.db.expenses.find({"is_active": True})
        expenses = await cursor.to_list(length=1000)

        # Map ERP status to Odoo state
        status_map = {
            'pending': 'draft',
            'approved': 'approved',
            'rejected': 'refused',
            'reimbursed': 'done',
            'paid': 'done',
        }

        migrated = 0
        for exp in expenses:
            erp_id = exp.get('id', str(exp['_id']))

            # Skip if already migrated
            if self.log.get_odoo_id('expenses', erp_id):
                logger.info(f"  Skipping expense {erp_id} (already migrated)")
                continue

            try:
                # Get product for category
                category = exp.get('category', 'General Expense')
                product_id = product_map.get(category)

                if not product_id:
                    # Use first available expense product
                    default = self.odoo.search('product.product', [
                        ('can_be_expensed', '=', True)
                    ], limit=1)
                    product_id = default[0] if default else None

                # Get employee
                emp_erp_id = exp.get('employee_id')
                employee_id = None
                if emp_erp_id:
                    employee_id = self.log.get_odoo_id('employees', emp_erp_id)

                # If no employee linked, try to find one
                if not employee_id:
                    default_emp = self.odoo.search('hr.employee', [], limit=1)
                    employee_id = default_emp[0] if default_emp else None

                if not employee_id:
                    logger.warning(f"  Skipping expense {erp_id}: No employee found")
                    continue

                # Build name/description
                name = exp.get('description') or f"{category} - {exp.get('merchant', 'Unknown')}"

                values = {
                    'name': name[:64],  # Odoo has length limit
                    'employee_id': employee_id,
                    'date': self._format_date(exp.get('expense_date')) or datetime.now().strftime('%Y-%m-%d'),
                    'total_amount_currency': float(exp.get('amount', 0)),
                }

                # Add product if available
                if product_id:
                    values['product_id'] = product_id

                # Remove None values
                values = {k: v for k, v in values.items() if v is not None}

                odoo_id = self.odoo.create('hr.expense', values)
                self.log.add_mapping('expenses', erp_id, odoo_id)
                migrated += 1
                logger.info(f"  Created expense: {name[:30]}... (ERP:{erp_id} → Odoo:{odoo_id})")

            except Exception as e:
                logger.error(f"  Failed to migrate expense {erp_id}: {e}")
                self.log.add_error('expenses', erp_id, str(e))

        logger.info(f"Expenses migrated: {migrated}/{len(expenses)}")
        return migrated

    async def run_migration(self) -> Dict[str, int]:
        """
        Run the complete migration.

        Returns:
            Dictionary with migration counts.
        """
        if not await self.connect():
            return {'error': 'Connection failed'}

        try:
            results = {}

            # 1. Migrate customers first (no dependencies)
            results['customers'] = await self.migrate_customers()

            # 2. Setup departments
            dept_map = await self.setup_departments()
            results['departments'] = len(dept_map)

            # 3. Setup expense products
            product_map = await self.setup_expense_products()
            results['expense_products'] = len(product_map)

            # 4. Migrate employees (depends on departments)
            results['employees'] = await self.migrate_employees(dept_map)

            # 5. Migrate projects (depends on customers, employees)
            results['projects'] = await self.migrate_projects()

            # 6. Migrate opportunities (depends on customers)
            results['opportunities'] = await self.migrate_opportunities()

            # 7. Migrate expenses (depends on employees, products)
            results['expenses'] = await self.migrate_expenses(product_map)

            # Save the log
            self.log.save()

            # Summary
            logger.info("\n=== Migration Summary ===")
            for entity, count in results.items():
                logger.info(f"  {entity}: {count}")

            if self.log.errors:
                logger.warning(f"\n  Errors: {len(self.log.errors)}")

            return results

        finally:
            await self.close()

    async def validate_migration(self) -> Dict[str, Dict[str, int]]:
        """
        Validate migration by comparing counts.

        Returns:
            Dictionary with source and target counts.
        """
        if not await self.connect():
            return {'error': 'Connection failed'}

        try:
            validation = {}

            # Count ERP records
            erp_counts = {
                'customers': await self.db.customers.count_documents({"is_active": True}),
                'employees': await self.db.employees.count_documents({"is_active": True}),
                'projects': await self.db.projects.count_documents({"is_active": True}),
                'opportunities': await self.db.opportunities.count_documents({"is_active": True}),
                'expenses': await self.db.expenses.count_documents({"is_active": True}),
            }

            # Count Odoo records
            odoo_counts = {
                'customers': self.odoo.search_count('res.partner', [('customer_rank', '>', 0)]),
                'employees': self.odoo.search_count('hr.employee', []),
                'projects': self.odoo.search_count('project.project', []),
                'opportunities': self.odoo.search_count('crm.lead', [('type', '=', 'opportunity')]),
                'expenses': self.odoo.search_count('hr.expense', []),
            }

            # Count mapped records
            mapped_counts = {
                entity: len(mappings)
                for entity, mappings in self.log.mappings.items()
                if entity in erp_counts
            }

            for entity in erp_counts:
                validation[entity] = {
                    'erp': erp_counts.get(entity, 0),
                    'odoo': odoo_counts.get(entity, 0),
                    'mapped': mapped_counts.get(entity, 0),
                }

            logger.info("\n=== Validation Results ===")
            for entity, counts in validation.items():
                status = "✓" if counts['mapped'] >= counts['erp'] else "⚠"
                logger.info(f"  {status} {entity}: ERP={counts['erp']}, Odoo={counts['odoo']}, Mapped={counts['mapped']}")

            return validation

        finally:
            await self.close()


async def main():
    """Run migration."""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate ERP data to Odoo')
    parser.add_argument('--validate', action='store_true', help='Validate migration only')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated')
    args = parser.parse_args()

    migration = ERPToOdooMigration()

    if args.validate:
        await migration.validate_migration()
    else:
        await migration.run_migration()
        # Also validate after migration
        await migration.validate_migration()


if __name__ == '__main__':
    asyncio.run(main())
