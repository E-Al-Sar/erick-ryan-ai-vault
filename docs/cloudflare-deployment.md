# Free 100% Secure Hosting on Cloudflare Pages

> **Summary**: How to host the collaboration portal on Cloudflare Pages for **$0/month** with zero-trust access control so only Ryan and you can view it.

---

## Why Cloudflare Pages?
- **100% Free**: Unlimited bandwidth, free custom domains, free SSL certificates.
- **Access Control (Cloudflare Zero Trust)**: Protect your site behind a free Google / Email one-time-passcode (OTP) login for up to 50 users. Ryan enters his email, receives a 6-digit code, and gets instant access without creating complex passwords.
- **Zero Server Maintenance**: Pure static hosting with global CDN edge caching.

---

## 3-Minute Deployment Steps

### Method A: Connect Clean Git Repo (Automated CI/CD)
1. Go to the [Cloudflare Dashboard](https://dash.cloudflare.com) and click **Workers & Pages**.
2. Click **Create Application** -> **Pages** -> **Connect to Git**.
3. Select your clean mirror repository (`ai-collab-portal` or similar).
4. Set build settings:
   - **Framework preset**: `None`
   - **Build output directory**: `portal`
5. Click **Save and Deploy**. Your site will be live at `https://your-project.pages.dev` in ~15 seconds.

### Method B: Direct Drag-and-Drop (Instant 1-Click)
1. Go to **Workers & Pages** -> **Create Application** -> **Pages** -> **Upload assets**.
2. Name your project (e.g., `ai-collab-studio`).
3. Drag and drop the `portal/` folder directly from your Finder into the browser window.
4. Click **Deploy Site**.

---

## Adding Free Zero-Trust Access Protection
1. In Cloudflare Dashboard, go to **Zero Trust** -> **Access** -> **Applications**.
2. Click **Add an application** -> **Self-hosted**.
3. Set Application Name to `AI Collab Portal` and enter your Pages URL (`your-project.pages.dev`).
4. Under **Policies**:
   - Rule Action: `Allow`
   - Include: `Emails` -> Add Ryan's email and your email.
5. Save. Now, when anyone visits the link, Cloudflare will challenge them for an email verification code before displaying a single pixel.
