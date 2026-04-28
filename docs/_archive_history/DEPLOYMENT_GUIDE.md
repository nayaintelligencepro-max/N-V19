# 🚀 NAYA V19 — Guide Déploiement Production

## Table des Matières
1. **Déploiement Local** (Développement)
2. **Déploiement Docker** (Développement + Production)
3. **Déploiement Cloud Run** (Google Cloud - Serverless)
4. **Déploiement VPS/Bare Metal** (AWS EC2, DigitalOcean)

---

## 1️⃣ DÉPLOIEMENT LOCAL (Développement)

### Installation Rapide
```bash
# 1. Setup venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Copier env
cp .env.example .env

# 3. Démarrer services
docker-compose up -d

# 4. Init DB
python PERSISTENCE/database/init_db.py

# 5. Démarrer API
uvicorn NAYA_CORE.api.main:app --reload --port 8000
```

### Accès
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin_naya_2024)

---

## 2️⃣ DÉPLOIEMENT DOCKER

### Build
```bash
docker build -t naya:v19 .
docker tag naya:v19 gcr.io/YOUR_PROJECT/naya:v19
docker push gcr.io/YOUR_PROJECT/naya:v19
```

### Run
```bash
export ENVIRONMENT=production
docker-compose --env-file .env.prod up -d
```

---

## 3️⃣ DÉPLOIEMENT CLOUD RUN

```bash
# Deploy
gcloud run deploy naya-api \
  --image gcr.io/YOUR_PROJECT/naya:v19 \
  --platform managed \
  --region europe-west1 \
  --memory 2Gi \
  --cpu 2
```

---

## 4️⃣ DÉPLOIEMENT VPS (AWS EC2 / DigitalOcean)

```bash
# SSH
ssh ubuntu@instance-ip

# Install
sudo apt update && sudo apt install -y docker.io docker-compose

# Clone & Run
git clone <repo>
cd NAYA_V19
docker-compose up -d

# Proxy with Nginx
sudo apt install -y nginx certbot python3-certbot-nginx
# Configure Nginx → proxy to 0.0.0.0:8000
# Add SSL certificate
```

---

## 📋 Production Checklist

- [ ] All secrets in .env (never commit)
- [ ] Database backups automated
- [ ] Monitoring alerts configured
- [ ] Logs aggregation in place
- [ ] SSL/TLS certificates active
- [ ] Rate limiting enabled
- [ ] Database indexes created
- [ ] Health checks passing
