# Odoo ERP - AI Labs Africa

Odoo 17 installation hosted at https://odoo.ailabsafrica.com

## Architecture

- **Odoo Application**: Docker container (odoo:17.0) on port 8069 (internal)
- **PostgreSQL Database**: Docker container (postgres:15) - dedicated for Odoo
- **Nginx Reverse Proxy**: SSL termination, proxying to localhost:8069
- **Longpolling**: Separate endpoint on port 8072 for real-time updates

## Directory Structure

```
/opt/kasaai/apps/odoo/
├── docker-compose.yml    # Container orchestration
├── .env                  # Environment variables (PostgreSQL password)
├── config/
│   └── odoo.conf         # Odoo configuration
├── addons/               # Custom addons directory
└── nginx/
    └── odoo.ailabsafrica.com.conf    # Nginx configuration
```

## Docker Volumes

- `odoo-db-data`: PostgreSQL data persistence
- `odoo-web-data`: Odoo filestore and sessions

## Management Commands

```bash
# Start Odoo
cd /opt/kasaai/apps/odoo && sudo docker-compose up -d

# Stop Odoo
cd /opt/kasaai/apps/odoo && sudo docker-compose down

# View logs
docker logs odoo -f
docker logs odoo-db -f

# Restart Odoo
docker restart odoo

# Access Odoo shell
docker exec -it odoo odoo shell -d <database_name>

# Backup database
docker exec odoo-db pg_dump -U odoo <database_name> > backup.sql

# Restore database
docker exec -i odoo-db psql -U odoo <database_name> < backup.sql
```

## Configuration

Key settings in `config/odoo.conf`:
- `proxy_mode = True` - Required for nginx reverse proxy
- `workers = 4` - Worker processes for multi-processing
- `db_host = odoo-db` - Internal Docker network hostname

## SSL Certificate

- Provider: Let's Encrypt (auto-renewal via certbot)
- Expiry: February 24, 2026
- Location: `/etc/letsencrypt/live/odoo.ailabsafrica.com/`

## First-Time Setup

1. Navigate to https://odoo.ailabsafrica.com
2. Set your master password (database manager password)
3. Create your first database with:
   - Database name
   - Email (admin username)
   - Password
   - Country
   - Demo data (optional)

## Security Notes

- Database manager is accessible at `/web/database`
- Set a strong master password during first setup
- Consider restricting database manager access in production (uncomment in nginx config)
- PostgreSQL is only accessible within Docker network (not exposed to host)

## Custom Addons

Place custom addons in `/opt/kasaai/apps/odoo/addons/` and restart:
```bash
docker restart odoo
```

Then update apps list in Odoo: Apps > Update Apps List

## Troubleshooting

1. **Permission denied on config**:
   ```bash
   sudo chmod 644 /opt/kasaai/apps/odoo/config/odoo.conf
   ```

2. **Container won't start**:
   ```bash
   docker logs odoo
   docker logs odoo-db
   ```

3. **Database connection issues**:
   - Check if odoo-db is healthy: `docker ps`
   - Verify password matches in `.env` and `odoo.conf`
