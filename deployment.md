# 🚢 Deployment Guide — GitIntel

This guide covers multiple ways to deploy **GitIntel** for production.

---

## 🏗️ Option 1: Docker (Recommended)
Docker is the most robust way to deploy GitIntel on any VPS (DigitalOcean, AWS, GCP).

1.  **Build the image**:
    ```bash
    docker build -t gitintel .
    ```

2.  **Run the container**:
    ```bash
    docker run -d \
      -p 80:8000 \
      -e GITHUB_TOKEN=your_token \
      -e OPENAI_API_KEY=your_key \
      --name gitintel gitintel
    ```

---

## ⚡ Option 2: Render / Railway / Fly.io
These are "Git-to-Deploy" platforms that are excellent for FastAPI.

### For Render.com:
1.  Connect your GitHub repository.
2.  Choose **Web Service**.
3.  **Build Command**: `pip install -r requirements.txt`
4.  **Start Command**: `python src/server/main.py`
5.  Add **Environment Variables**:
    - `GITHUB_TOKEN`: `your_pat_token`
    - `OPENAI_API_KEY`: `your_key`
    - `PYO3_USE_ABI3_FORWARD_COMPATIBILITY`: `1`

---

## ☁️ Option 3: Vercel (Fastest for SPA + API)
Vercel handles FastAPI naturally using their Python Runtime.

1.  Add a `vercel.json` file to the root (see below).
2.  Create a project on [Vercel](https://vercel.com) and link your GitHub.
3.  Add environment variables in the Vercel dashboard.

---

## 🔒 Security checklist
Before deploying, ensure:
1.  **Environment Variables**: Never hardcode secrets in `.env` inside the repository. Use the deployment platform's secret manager.
2.  **CORS Settings**: In `src/server/main.py`, update `allow_origins=["*"]` to your specific production domain (e.g., `["https://gitintel.com"]`).
3.  **Port**: Production servers usually look for port `80` or `443`. Docker handles the `80:8000` mapping.

---

## 📦 Monitoring
If using Docker, consider using a reverse proxy like **Nginx** or **Traefik** to handle SSL (HTTPS) automatically with Let's Encrypt.
