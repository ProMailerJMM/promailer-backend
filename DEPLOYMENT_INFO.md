# 🚀 ProMailer Production Deployment Reference

This document stores the verified URLs, account logins, DNS configurations, and deployment setups for the production release of ProMailer.

---

## 🌐 1. Front-End Website (promailer.ca)

* **Production URL:** [https://promailer.ca](https://promailer.ca)
* **Hosting Provider:** Netlify
* **Netlify Site ID:** `grand-dango-0393a8`
* **Account Login Email:** `promailer@justmemedia.ca` (Logged in via Google)
* **Deployment Method:** Netlify Drop (Manual drag-and-drop of the `ProMailer-Landing/` folder containing `index.html` and `download.html`).

---

## ⚙️ 2. Back-End & Payment Server (Render)

* **Backend Service URL:** [https://promailer-backend-rdnl.onrender.com](https://promailer-backend-rdnl.onrender.com)
* **Hosting Provider:** Render (Web Service)
* **Service Name:** `promailer-backend`
* **Runtime:** Python 3 (Free Tier instance)
* **GitHub Repository:** [https://github.com/ProMailerJMM/promailer-backend.git](https://github.com/ProMailerJMM/promailer-backend.git)
* **Deployment Method:** Auto-deploy on Git push to the `main` branch.
* **Environment Variables (on Render Dashboard):**
  * `STRIPE_SECRET_KEY` (Stripe Live Secret Key)
  * `STRIPE_PUBLISHABLE_KEY` (Stripe Live Publishable Key)
  * `PORT` (Configured by Render)

---

## 🏷️ 3. Domain Name & DNS settings (Namecheap)

* **Domain Registrar:** Namecheap
* **Domain:** `promailer.ca`
* **Nameservers:** Namecheap BasicDNS (External DNS setup on Netlify)
* **DNS Records Configured:**
  * **A Record (@):** Points to `75.2.60.5` (Netlify primary load balancer)
  * **A Record (@):** Points to `99.83.190.102` (Netlify secondary load balancer)
  * **CNAME Record (www):** Points to `grand-dango-0393a8.netlify.app`
  * **MX Records:** (Optional: Manage MX records on Namecheap if configuring business emails on this domain).

---

## 💳 4. Stripe Payment Gateway

* **Stripe Mode:** Live Mode (Production)
* **Integration:** Frontend `index.html` loads Stripe Elements, queries client secrets from the Render backend, and redirects users to `/download.html` on success.
* **Live Webhooks / Redirection Query:** `payment_intent_id` and `platform` passed to `/download` on the backend to authenticate secure zip package delivery.

---

## 🔄 5. Rolling out Updates (Step-by-Step)

When making modifications or issuing upgrades:

### Step 1: Update & Sync Python Source
1. Edit the core code in `Promailer/`.
2. Sync changes to the platform folders (`ProMailer-Mac`, `ProMailer-Windows`, `ProMailer-Linux`).

### Step 2: Build the macOS App
```bash
cd /Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/02_ACTIVE_PROJECTS/ProMailer-Mac
chmod +x build/build_mac.sh
./build/build_mac.sh
```

### Step 3: Package the ZIP Archives
* Compresses the newly compiled binary for macOS and standard packages for Windows/Linux:
```bash
# macOS
zip -r -q ProMailer-Mac.zip dist/ProMailer.app

# Windows
zip -r -q ProMailer-Windows.zip ProMailer-Windows/ -x "*/.DS_Store" "*/.git*" "*/venv*"

# Linux
zip -r -q ProMailer-Linux.zip ProMailer-Linux/ -x "*/.DS_Store" "*/.git*" "*/venv*"
```

### Step 4: Deploy the ZIPs to the Payment Server
Copy the updated ZIP packages to the `ProMailer-PaymentServer/files/` directory, commit, and push to GitHub to trigger the Render auto-deploy:
```bash
cd /Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/02_ACTIVE_PROJECTS/ProMailer-PaymentServer
git add files/
git commit -m "Deploy updated ProMailer packages"
git push origin main
```
*(Check the Render dashboard to confirm the build goes live successfully).*
