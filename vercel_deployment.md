# MMU Clearance System — Vercel + Supabase Deployment Guide

**Project:** MMU Student Clearance System  
**Author:** Victor Kimutai (CIT-222-044/2020)  
**Supervisor:** Dr. Nick Ishmael  
**Stack:** Django 4.2 · DRF · PostgreSQL · Vercel · Supabase · Cloudinary

---

## Architecture

```
Vercel       → hosts Django as Python Serverless Functions
Supabase     → free managed PostgreSQL (permanent free tier, no sleep)
Cloudinary   → free file storage for uploaded supporting documents
Gmail SMTP   → transactional email notifications
```

---

## Step 1 — Supabase (PostgreSQL)

1. Go to [supabase.com](https://supabase.com) → **New Project** → note your Project Password
2. **Settings → Database → Connection String** → copy the **URI** tab value
3. It looks like: `postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres`
4. This becomes your `DATABASE_URL`

---

## Step 2 — Cloudinary (File Storage)

1. Go to [cloudinary.com](https://cloudinary.com) → free account
2. **Dashboard** → copy **Cloud Name**, **API Key**, **API Secret**

---

## Step 3 — Gmail App Password (Email)

1. Go to your Google Account → **Security** → **2-Step Verification** → **App Passwords**
2. Generate a password for "Mail"
3. Copy the 16-character password — this is your `EMAIL_HOST_PASSWORD`

---

## Step 4 — GitHub

```bash
cd mmu_clearance
git init
git add .
git commit -m "Initial commit — MMU Clearance System"
git remote add origin https://github.com/YOUR_USERNAME/mmu-clearance.git
git push -u origin main
```

Make sure `.env` is in `.gitignore` — **never commit secrets**.

---

## Step 5 — Vercel Deployment

1. Go to [vercel.com](https://vercel.com) → **Add New Project** → Import from GitHub
2. Framework Preset: **Other**
3. Root Directory: `.` (project root)
4. Add Environment Variables in the Vercel dashboard:

| Variable | Value |
|---|---|
| `SECRET_KEY` | Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DEBUG` | `False` |
| `DATABASE_URL` | From Supabase Step 1 |
| `CLOUDINARY_CLOUD_NAME` | From Cloudinary Step 2 |
| `CLOUDINARY_API_KEY` | From Cloudinary Step 2 |
| `CLOUDINARY_API_SECRET` | From Cloudinary Step 2 |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST_USER` | Your Gmail address |
| `EMAIL_HOST_PASSWORD` | Gmail App Password from Step 3 |
| `VERCEL_URL` | `your-app-name.vercel.app` |

5. Click **Deploy** — Vercel runs `build_files.sh` automatically

---

## Step 6 — Seed the Database (One Time)

```bash
# Install Vercel CLI
npm i -g vercel

# Pull env vars locally
vercel env pull .env.production

# Run against Supabase
DATABASE_URL=$(cat .env.production | grep DATABASE_URL | cut -d= -f2-) python manage.py seed_mmu_data
```

Or connect to Supabase locally:
```bash
export DATABASE_URL="postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres"
python manage.py seed_mmu_data
```

---

## Step 7 — Create Django Superuser (for /admin)

```bash
# With Supabase DATABASE_URL set:
python manage.py createsuperuser
```

---

## Local Development Setup

```bash
# 1. Clone and install
git clone https://github.com/YOUR_USERNAME/mmu-clearance.git
cd mmu-clearance
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Copy env file
cp .env.example .env
# Edit .env with your values

# 3. Run migrations
python manage.py migrate

# 4. Seed data
python manage.py seed_mmu_data

# 5. Run server
python manage.py runserver
```

Visit http://localhost:8000

---

## Test Accounts

| Role | ID | Password | Department |
|---|---|---|---|
| Student | `CIT-222-044/2020` | `student123` | — |
| Library Staff | `LIB-001` | `staff123` | Library |
| Finance Staff | `FIN-001` | `staff123` | Finance |
| Hostels Staff | `HOS-001` | `staff123` | Hostels |
| Faculty Staff | `FAC-001` | `staff123` | Faculty |
| ICT Staff | `ICT-001` | `staff123` | ICT Services |
| Registry Staff | `REG-001` | `staff123` | Registry |
| Admin | `ADM-001` | `admin123` | Registry |

---

## Page URLs

| URL | Description |
|---|---|
| `/login/` | Student login |
| `/dashboard/` | Student real-time clearance dashboard |
| `/certificate/` | Downloadable clearance certificate |
| `/staff/login/` | Staff login |
| `/staff/dashboard/` | Staff clearance queue |
| `/staff/action/<id>/` | Staff approve/reject panel |
| `/admin/` | Django admin panel |

---

## REST API Endpoints

### Auth
```
POST   /api/auth/student/login/
POST   /api/auth/staff/login/
POST   /api/auth/logout/
```

### Student (Token required)
```
GET    /api/student/profile/
GET    /api/student/clearance/status/
POST   /api/student/clearance/submit/
GET    /api/student/clearance/certificate/
GET    /api/student/notifications/
```

### Staff (Token required)
```
GET    /api/staff/queue/
GET    /api/staff/queue/<request_id>/
POST   /api/staff/queue/<request_id>/action/
GET    /api/staff/history/
```

### Admin (Admin token required)
```
GET    /api/admin/requests/
GET    /api/admin/requests/<id>/
GET/POST /api/admin/staff/
PUT    /api/admin/staff/<id>/
GET    /api/admin/reports/summary/
```

---

## Common Issues

| Problem | Fix |
|---|---|
| `STATIC_ROOT` mismatch | Must be `staticfiles_build/static` — matches `distDir` in `vercel.json` |
| 500 on media uploads | Ensure Cloudinary env vars are set |
| SSL error on Supabase | `dj_database_url` is configured with SSL in settings.py |
| Email not sending | Verify Gmail App Password (not regular password), 2FA must be on |
| Migrations fail | Check `DATABASE_URL` env var is set correctly |
| `ALLOWED_HOSTS` error | Add your Vercel URL to `VERCEL_URL` env var |

---

## Future Deployments

```bash
git add .
git commit -m "Your changes"
git push
# Vercel auto-deploys in ~60 seconds
```
