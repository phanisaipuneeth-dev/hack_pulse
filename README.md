BrandCraft — AI-Powered Branding Automation System
Complete Setup Guide



📁 Project Structure


brandcraft/
├── index.html      ← Full frontend (HTML + CSS + JS) — open in browser
├── app.py          ← Python Flask backend API
├── .env            ← Environment variables (create this)
└── README.md       ← This file




🚀 Quick Start

1. Run Frontend Only (No Backend Needed)
Just open `index.html` in your browser — everything works with mock data!

Demo login:
- Email: `demo@brandcraft.ai`
- Password: `password123`



2. Run with Python Backend

**Install dependencies:**
```bash
pip install flask flask-cors openai pillow fpdf2 python-dotenv
```

**Create `.env` file:**
```
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-your-openai-key-here   # optional, enables real AI
```

**Start the server:**
```bash
python app.py
```
Server starts at `http://localhost:5000`

**Connect frontend to backend:**
In `index.html`, find the `handleLogin()` function and replace with:
```js
const res = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type':'application/json'},
  body: JSON.stringify({email, password: pass})
});
const data = await res.json();
if (data.token) { localStorage.setItem('token', data.token); ... }
```

---
🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login with email/password |
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/logout` | Logout (invalidate token) |
| POST | `/api/brand/generate` | Generate AI brand identity |
| POST | `/api/brand/social-content` | Get hashtags & content ideas |
| POST | `/api/brand/growth-strategy` | 90-day growth roadmap |
| POST | `/api/brand/chatbot` | AI chat responses |
| POST | `/api/brand/export-pdf` | Download brand kit PDF |
| POST | `/api/business/save` | Save owner/contact details |
| GET | `/api/subscription/plans` | Get all pricing plans |
| POST | `/api/subscription/upgrade` | Upgrade user plan |
| GET | `/api/user/profile` | Get user profile |
| GET | `/api/user/brands` | List all user brands |
| GET | `/api/health` | Health check |

---

🌟 Feature Walkthrough

Step 1 — Dashboard
- Select industry (12 options)
- Choose target audience (8 options)
- Pick brand personality traits
- Set color style preference
- Enter brand name, tone, boldness sliders

Step 2 — Brand Identity
- AI-generated logo with 4 style variants (Modern, Minimal, Bold, Retro)
- 5 AI taglines with quality scores
- AI Brand Score (0-100) with 5 metrics breakdown
- 4 color palette options
- Typography pairing suggestions

Step 3 — Business Details
- Owner name, phone, email, website
- Location (city, state, country, PIN)
- Social media handles
- Live brand card preview (updates as you type)
- Download brand card button

 Step 4 — AI Insights
- Social hashtags for Instagram, Twitter, LinkedIn
- 6 content creation ideas with platform/type/copy
- 5-step business scaling strategy
- Market intelligence with progress bars
Chatbot
- Floating AI assistant (bottom-right)
- Quick chip prompts
- Contextual branding advice

---

🛠 Production Upgrades

| Feature | Tool |
|---------|------|
| Real Database | PostgreSQL + SQLAlchemy |
| Payments | Razorpay or Stripe |
| Real AI Generation | OpenAI GPT-4o / DALL·E 3 |
| Logo SVG Export | Python `svgwrite` |
| Email Notifications | SendGrid |
| Auth | JWT tokens |
| Deployment | Render / Railway / AWS |

---

 📦 Requirements

```
flask==3.0.0
flask-cors==4.0.0
openai==1.0.0
fpdf2==2.7.0
python-dotenv==1.0.0
Pillow==10.0.0
```
