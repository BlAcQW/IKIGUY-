# Module 7: Development Environment Setup

**Topics Covered:** prerequisites, installation, configuration

**Part of:** KasaAI Developer Intern Onboarding Course

---

## 7. Development Environment Setup

### 🖥️ Server Access

| Server | IP | Purpose |
|--------|-----|---------|
| **Production** | 148.251.0.46 | Live production environment |
| **Dev** | 85.214.12.174 | Development and testing |

```bash
# SSH to dev server
ssh dev@85.214.12.174

# Or production (with proper permissions)
ssh dev@148.251.0.46
```

---

### 🛠️ Required Tools

<table>
<tr>
<td width="50%">

**Development**
- IDE: VS Code or PyCharm
- Python: 3.11+ (use pyenv)
- Node.js: 18+ (use nvm)

</td>
<td width="50%">

**Database & Testing**
- MongoDB Compass
- Postman/Insomnia
- Docker Desktop

</td>
</tr>
</table>

---

### ⚙️ Local Development Setup

<details>
<summary><strong>Backend Setup</strong></summary>

```bash
# Navigate to project
cd /opt/kasaai/apps/core_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Run development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

</details>

<details>
<summary><strong>Frontend Setup</strong></summary>

```bash
# Navigate to frontend
cd /opt/kasaai/apps/b2c-portal

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
# Edit .env.local with API URLs

# Run development server
npm run dev
```

</details>

<details>
<summary><strong>Database Access</strong></summary>

**MongoDB**:
```bash
# Connect to MongoDB
mongo mongodb://admin:password@127.0.0.1:27017/

# Or use MongoDB Compass GUI
# Connection string: mongodb://admin:password@127.0.0.1:27017/
```

**PostgreSQL** (Supabase):
```bash
# Connection details in /opt/kasaai/.env
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=your-key
```

</details>

---

### 🎛️ Service Management

```bash
# Check all KasaAI services
sudo systemctl list-units "kasaai-*.service" --all

# Check specific service
sudo systemctl status kasaai-core-backend

# Restart service
sudo systemctl restart kasaai-studyflow-backend

# View logs
sudo journalctl -u kasaai-churchflow-backend -f
```

---
