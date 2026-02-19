# Module 10: Resources and Support

**Topics Covered:** resources, communication, help

**Part of:** KasaAI Developer Intern Onboarding Course

---

## 10. Resources & Support

### 📚 Essential Documentation Locations

| Component | Path | Key Files |
|-----------|------|-----------|
| **Architecture** | `/opt/kasaai/apps/architecture/` | ARCHITECTURE.md, INTEGRATION_GUIDE.md |
| **Shared Services** | `/opt/kasaai/apps/shared/` | QUICK_REFERENCE.md, services/README.md |
| **Core Backend** | `/opt/kasaai/apps/core_backend/` | README.md, backend/main.py |
| **B2C Portal** | `/opt/kasaai/apps/b2c-portal/` | README.md, src/App.tsx |
| **Developer Platform** | `/opt/kasaai/apps/developer_platform/` | API_DOCUMENTATION.md, PLANNING.md |
| **StudyFlow** | `/opt/kasaai/apps/studyflow/` | PLANNING.md, PRD.md, MVP_SUMMARY.md |
| **ChurchFlow** | `/opt/kasaai/apps/churchflow/` | PLANNING.md, PRD.md, MVP_SUMMARY.md |
| **EventFlow** | `/opt/kasaai/apps/eventflow/` | PLANNING.md, VOICE_AI_IMPLEMENTATION_PLAN.md |
| **InkWave** | `/opt/kasaai/apps/inkwave/` | PLANNING.md |
| **ERP** | `/opt/kasaai/apps/erp/` | README.md, TASKS.md, PLANNING.md |
| **TTS Deployment** | `/opt/kasaai/apps/tts-deployment/` | README.md, RUNPOD_SETUP.md |
| **Community** | `/opt/kasaai/apps/community/` | COMMUNITY_DATA_PLATFORM.md, DEPLOYMENT.md |

---

### 🔧 Common Commands Cheat Sheet

<details>
<summary><strong>Service Management</strong></summary>

```bash
# List all KasaAI services
sudo systemctl list-units "kasaai-*.service"

# Check service status
sudo systemctl status kasaai-core-backend

# Restart service
sudo systemctl restart kasaai-studyflow-backend

# View live logs
sudo journalctl -u kasaai-churchflow-backend -f

# Check last 100 log lines
sudo journalctl -u kasaai-core-backend -n 100
```

</details>

<details>
<summary><strong>Database Operations</strong></summary>

```bash
# Connect to MongoDB
mongo mongodb://admin:password@127.0.0.1:27017/

# Show databases
show dbs

# Use database
use kasaai_core

# Show collections
show collections

# Query documents
db.users.find({}).limit(5)

# Count documents
db.assistants.count()
```

</details>

<details>
<summary><strong>Docker (TTS Services)</strong></summary>

```bash
# List running containers
docker ps

# Check container logs
docker logs -f coqui-tts

# Restart container
docker restart melotts

# Check Docker disk usage
docker system df

# Cleanup unused images
docker image prune -a
```

</details>

<details>
<summary><strong>Git Operations</strong></summary>

```bash
# Check status
git status

# Create feature branch
git checkout -b feature/my-feature

# Stage changes
git add .

# Commit with message
git commit -m "Add feature X with Y functionality"

# Push to remote
git push origin feature/my-feature

# Pull latest changes
git pull origin main
```

</details>

---

### 🐛 Troubleshooting

<details>
<summary><strong>1. Service won't start</strong></summary>

```bash
# Check logs for errors
sudo journalctl -u kasaai-[service-name] -n 100

# Check if port is in use
sudo netstat -tulpn | grep [port]

# Check permissions
ls -la /opt/kasaai/apps/[app-name]/
```

</details>

<details>
<summary><strong>2. Database connection errors</strong></summary>

```bash
# Check MongoDB status
sudo systemctl status mongodb

# Test connection
mongo --eval "db.adminCommand('ping')"

# Check credentials in .env
cat /opt/kasaai/.env | grep MONGODB
```

</details>

<details>
<summary><strong>3. Import errors</strong></summary>

```bash
# Ensure virtual environment is activated
source /opt/kasaai/apps/venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
echo $PYTHONPATH
```

</details>

<details>
<summary><strong>4. Frontend won't build</strong></summary>

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm cache clean --force

# Check Node version
node --version  # Should be 18+
```

</details>

---

### 👥 Who to Ask

| Topic | Contact |
|-------|---------|
| **Architecture & System Design** | Senior developers, Lead architects |
| **Backend Development (Python/FastAPI)** | Backend team leads |
| **Frontend Development (React/TypeScript)** | Frontend team leads |
| **AI Integration (TTS/ASR/LLM)** | AI/ML team |
| **Database (MongoDB/PostgreSQL)** | Database administrators |
| **DevOps (Docker/Nginx/Deployment)** | DevOps team |
| **Specific Apps** | App-specific team leads |
| **General Questions** | Your assigned mentor |

---

### 📖 Learning Resources

**Internal**:
- Architecture documentation (`/opt/kasaai/apps/architecture/`)
- Shared services examples (`/opt/kasaai/apps/shared/services/`)
- Existing app code (read before you write!)
- PLANNING.md files for each app

**External**:
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [React Docs](https://react.dev)
- [MongoDB Docs](https://docs.mongodb.com)
- [Supabase Docs](https://supabase.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)

---
