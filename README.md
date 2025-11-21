## ProcurePay – Procure-to-Pay Demo

Full-stack reference implementation of the technical assessment. Includes:

- **Backend** – Django REST Framework + JWT auth, document processing hooks, AI-ready PO and receipt validation, Swagger docs.
- **Frontend** – React + Vite + shadcn/ui client already in `frontend/` (see `src/pages/*`).
- **Infrastructure** – Dockerfiles for backend & frontend plus `docker-compose.yml` wiring a Postgres database. Ready for deployment on any VPS/EC2/Render/Fly.

### Quick Start (local dev)

```bash
git clone <repo>
cd CHALLENGES/IST2
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
cp backend/example.env backend/.env
python backend/manage.py migrate
python backend/manage.py seed_demo_users  # create the demo accounts used in the UI
python backend/manage.py runserver 0.0.0.0:8000
```

Frontend (in another terminal):

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000/api npm run dev
```

Login with the seeded accounts (password defaults to `Password123!`):

- `staff@company.com`
- `approver1@company.com`
- `approver2@company.com`
- `finance@company.com`

### Docker workflow

```bash
cp backend/example.env backend/.env   # adjust secrets, DB URL, OpenAI key if available
docker compose up --build
```

Services:

- `frontend` → http://localhost:8080
- `backend` → http://localhost:8000 (Swagger at `/api/docs/`)
- `db` → Postgres (internal)

### Deployment checklist

1. Provision Postgres + storage (S3 or local volume) on your target platform.
2. Set `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `DATABASE_URL`, and JWT lifetimes via env vars.
3. Build and push the Docker images or run `docker compose up -d` on the server.
4. Run `python manage.py collectstatic --noinput` if serving admin assets behind a CDN.
5. (Optional) Set `OPENAI_API_KEY` to enable richer document extraction.

### API overview

- `POST /api/auth/login/` – obtain JWT + user payload
- `GET /api/auth/user/` – current user profile
- `GET/POST /api/requests/` – list/create (staff limited to their own)
- `GET/PUT /api/requests/{id}/` – detail/update (staff can edit while pending)
- `PATCH /api/requests/{id}/approve/` – approve as L1/L2
- `PATCH /api/requests/{id}/reject/` – reject
- `POST /api/requests/{id}/submit-receipt/` – upload receipt for validation

All endpoints are documented at `/api/docs/` (Swagger UI powered by drf-spectacular).

### Document automation

- **Proforma ingestion**: extracts metadata via pdfplumber/pytesseract, optional GPT enrichment.
- **PO generation**: auto-creates plain-text PO stored on the request record when final approval finishes.
- **Receipt validation**: compares vendor/amount to PO metadata and surfaces discrepancies back to the frontend.

### Testing

```bash
cd backend
python manage.py test
```

### Public deployment

Deploy the `backend` container behind HTTPS (e.g., Nginx, Caddy, Fly Machines) and serve the `frontend` build via any static host (Netlify, S3+CloudFront, Render Static Site). Point `VITE_API_URL` to the live backend URL before building the frontend image or static assets. Update the README with the public URL once deployed.

## Live Demo
Access the live application here: [http://209.105.242.202:8085/](http://209.105.242.202:8085/)

## Login Credentials
Use the seeded accounts below (default password: `Password123!`):

- **Staff:** `staff@company.com`  
- **Approver Level 1:** `approver1@company.com`  
- **Approver Level 2:** `approver2@company.com`  
- **Finance:** `finance@company.com`
