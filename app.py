"""
BrandCraft — Generative AI-Powered Branding Automation System
Python Flask Backend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SETUP:
    pip install flask flask-cors openai pillow fpdf2 python-dotenv

RUN:
    python app.py
    → Starts at http://localhost:5000
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from functools import wraps
import json, os, io, base64, random, string
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ── Optional: OpenAI for real AI generation ──────────────────
try:
    import openai
    OPENAI_ENABLED = True
except ImportError:
    OPENAI_ENABLED = False
    print("⚠  openai not installed. Using mock AI responses.")

# ── Optional: PDF generation ─────────────────────────────────
try:
    from fpdf import FPDF
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════
SECRET_KEY = os.getenv("SECRET_KEY", "brandcraft-secret-2024")
OPENAI_KEY  = os.getenv("OPENAI_API_KEY", "")

if OPENAI_ENABLED and OPENAI_KEY:
    openai.api_key = OPENAI_KEY

# In-memory store (use PostgreSQL/Redis in production)
USERS_DB = {
    "demo@brandcraft.ai": {"password": "password123", "name": "Demo User", "plan": "free"},
}
SESSIONS  = {}   # token → email
BRANDS_DB = {}   # email → [brand_objects]

# ══════════════════════════════════════════════════════════════
# AUTH HELPERS
# ══════════════════════════════════════════════════════════════
def gen_token(n=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token not in SESSIONS:
            return jsonify({"error": "Unauthorized"}), 401
        request.user_email = SESSIONS[token]
        return f(*args, **kwargs)
    return decorated

# ══════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════
@app.route("/api/auth/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Body: { "email": str, "password": str }
    """
    data  = request.json or {}
    email = data.get("email", "").strip().lower()
    pwd   = data.get("password", "")

    if email not in USERS_DB or USERS_DB[email]["password"] != pwd:
        return jsonify({"error": "Invalid credentials"}), 401

    token = gen_token()
    SESSIONS[token] = email
    user  = USERS_DB[email]

    return jsonify({
        "token": token,
        "user": {"email": email, "name": user["name"], "plan": user["plan"]},
        "expires_in": 86400
    })


@app.route("/api/auth/register", methods=["POST"])
def register():
    """
    POST /api/auth/register
    Body: { "email": str, "password": str, "name": str }
    """
    data  = request.json or {}
    email = data.get("email", "").strip().lower()
    pwd   = data.get("password", "")
    name  = data.get("name", "")

    if not email or "@" not in email:
        return jsonify({"error": "Invalid email"}), 400
    if len(pwd) < 6:
        return jsonify({"error": "Password must be ≥ 6 chars"}), 400
    if email in USERS_DB:
        return jsonify({"error": "Email already registered"}), 409

    USERS_DB[email] = {"password": pwd, "name": name, "plan": "free"}
    token = gen_token()
    SESSIONS[token] = email

    return jsonify({"token": token, "user": {"email": email, "name": name, "plan": "free"}}), 201


@app.route("/api/auth/logout", methods=["POST"])
@require_auth
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    SESSIONS.pop(token, None)
    return jsonify({"message": "Logged out"})

# ══════════════════════════════════════════════════════════════
# AI GENERATION HELPERS
# ══════════════════════════════════════════════════════════════
def ai_generate(prompt: str, max_tokens: int = 500) -> str:
    """Call OpenAI GPT-4 or fall back to mock."""
    if OPENAI_ENABLED and OPENAI_KEY:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are BrandCraft, an expert AI branding consultant. Respond with JSON only."},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.8
        )
        return response.choices[0].message.content
    else:
        return _mock_ai(prompt)


def _mock_ai(prompt: str) -> str:
    """Mock responses for dev/demo without OpenAI key."""
    if "tagline" in prompt.lower():
        return json.dumps({"taglines": [
            "Build brands that last.",
            "Where vision meets identity.",
            "Crafted to be remembered.",
            "Your brand, amplified.",
            "Intelligence. Design. Impact."
        ]})
    if "hashtag" in prompt.lower() or "social" in prompt.lower():
        return json.dumps({"instagram": ["#branding","#logodesign","#startup","#entrepreneur","#marketing"],
                           "twitter":   ["#branding","#startup","#AI","#marketing"],
                           "linkedin":  ["#BrandStrategy","#BusinessGrowth","#Marketing"]})
    if "content" in prompt.lower():
        return json.dumps({"ideas": [
            {"platform":"Instagram","type":"Reel","idea":"Behind-the-scenes brand story"},
            {"platform":"Twitter","type":"Thread","idea":"5 branding mistakes to avoid"},
            {"platform":"LinkedIn","type":"Article","idea":"Visual identity boosts conversion by 33%"}
        ]})
    if "score" in prompt.lower():
        return json.dumps({"overall":87,"memorability":88,"market_fit":82,"uniqueness":91,"trust":79,"visual":94,
                           "summary":"Excellent brand potential with strong visual identity."})
    return json.dumps({"result": "AI-generated content placeholder"})

# ══════════════════════════════════════════════════════════════
# BRAND GENERATION ROUTES
# ══════════════════════════════════════════════════════════════
@app.route("/api/brand/generate", methods=["POST"])
@require_auth
def generate_brand():
    """
    POST /api/brand/generate
    Body: {
        "brand_name": str,
        "industry": str,
        "audience": [str],
        "tone": str,
        "description": str,
        "color_style": str,
        "boldness": int (0-100),
        "positioning": int (0-100)
    }
    Returns: { taglines, logo_config, palette, typography, score, description }
    """
    data = request.json or {}

    # 1. Generate taglines
    tagline_prompt = f"""
    Generate 5 powerful brand taglines for:
    - Brand: {data.get('brand_name', 'Brand')}
    - Industry: {data.get('industry', 'Technology')}
    - Audience: {', '.join(data.get('audience', []))}
    - Tone: {data.get('tone', 'Professional')}
    - Description: {data.get('description', '')}
    Return JSON: {{"taglines": ["...", "...", "...", "...", "..."]}}
    """
    tagline_result = json.loads(ai_generate(tagline_prompt))

    # 2. Generate AI score
    score_prompt = f"""
    Score this brand concept (0-100 each metric):
    Brand: {data.get('brand_name')} | Industry: {data.get('industry')} | Tone: {data.get('tone')}
    Return JSON: {{"overall":N,"memorability":N,"market_fit":N,"uniqueness":N,"trust":N,"visual":N,"summary":"..."}}
    """
    score_result = json.loads(ai_generate(score_prompt))

    # 3. Select logo config
    logo_config = _build_logo_config(data)

    # 4. Suggest palette
    palette = _suggest_palette(data.get('color_style', ''), data.get('industry', ''))

    # 5. Save to DB
    brand_obj = {
        "id": gen_token(8),
        "created_at": datetime.utcnow().isoformat(),
        "name": data.get('brand_name', ''),
        "industry": data.get('industry', ''),
        "taglines": tagline_result.get("taglines", []),
        "score": score_result,
        "logo_config": logo_config,
        "palette": palette,
        "input": data
    }
    email = request.user_email
    BRANDS_DB.setdefault(email, []).append(brand_obj)

    return jsonify({
        "brand_id": brand_obj["id"],
        "taglines": brand_obj["taglines"],
        "score": brand_obj["score"],
        "logo_config": logo_config,
        "palette": palette,
        "description": _generate_description(data)
    })


@app.route("/api/brand/social-content", methods=["POST"])
@require_auth
def social_content():
    """
    POST /api/brand/social-content
    Body: { "brand_id": str, "brand_name": str, "industry": str }
    """
    data = request.json or {}
    prompt = f"""
    Generate social media hashtags and content ideas for:
    Brand: {data.get('brand_name')} | Industry: {data.get('industry')}
    Return JSON: {{
        "instagram": ["#tag1","#tag2",...(10 tags)],
        "twitter": ["#tag1",...(8 tags)],
        "linkedin": ["#tag1",...(6 tags)],
        "content_ideas": [
            {{"platform":"Instagram","type":"Reel","idea":"...","caption":"..."}}, ...
        ]
    }}
    """
    result = json.loads(ai_generate(prompt, max_tokens=800))
    return jsonify(result)


@app.route("/api/brand/growth-strategy", methods=["POST"])
@require_auth
def growth_strategy():
    """
    POST /api/brand/growth-strategy
    Body: { "brand_name": str, "industry": str, "audience": [str] }
    """
    data = request.json or {}
    prompt = f"""
    Create a 90-day growth strategy for:
    Brand: {data.get('brand_name')} | Industry: {data.get('industry')} | Audience: {data.get('audience')}
    Return JSON: {{
        "phases": [
            {{"phase":"Foundation (Days 1-30)","actions":["..."],"kpis":["..."]}},
            {{"phase":"Traction (Days 31-60)","actions":["..."],"kpis":["..."]}},
            {{"phase":"Scale (Days 61-90)","actions":["..."],"kpis":["..."]}}
        ],
        "channels": [{{"name":"...","priority":"high/medium/low","budget_percent":N}}],
        "quick_wins": ["...","...","..."]
    }}
    """
    result = json.loads(ai_generate(prompt, max_tokens=1000))
    return jsonify(result)


@app.route("/api/brand/chatbot", methods=["POST"])
@require_auth
def chatbot():
    """
    POST /api/brand/chatbot
    Body: { "message": str, "context": { brand details } }
    """
    data    = request.json or {}
    message = data.get("message", "")
    context = data.get("context", {})

    if OPENAI_ENABLED and OPENAI_KEY:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"""You are BrandCraft AI, an expert branding assistant.
                Current brand context: {json.dumps(context)}
                Be concise, helpful, and actionable. Use emojis sparingly."""},
                {"role": "user", "content": message}
            ],
            max_tokens=300
        )
        reply = response.choices[0].message.content
    else:
        # Mock responses
        replies = {
            "logo": "Your logo scores well! Consider testing on dark and light backgrounds.",
            "color": "Color psychology for your palette: trust (blue), energy (yellow), growth (green).",
            "market": "Your market positioning is strong. Focus on differentiation through storytelling.",
            "content": "Top content formats for your audience: short video (40%), carousels (30%), stories (30%).",
        }
        key = next((k for k in replies if k in message.lower()), None)
        reply = replies.get(key, "Great question! I can help with logo design, brand strategy, content planning, and market analysis. What would you like to explore? 🚀")

    return jsonify({"reply": reply, "timestamp": datetime.utcnow().isoformat()})

# ══════════════════════════════════════════════════════════════
# BUSINESS DETAILS ROUTES
# ══════════════════════════════════════════════════════════════
@app.route("/api/business/save", methods=["POST"])
@require_auth
def save_business():
    """
    POST /api/business/save
    Body: {
        "owner_name": str, "phone": str, "email": str,
        "website": str, "city": str, "state": str,
        "country": str, "pincode": str,
        "socials": { "instagram": str, "linkedin": str, "twitter": str }
    }
    """
    data  = request.json or {}
    email = request.user_email

    # Attach to latest brand
    if email in BRANDS_DB and BRANDS_DB[email]:
        BRANDS_DB[email][-1]["business"] = data
        return jsonify({"message": "Business details saved", "status": "success"})

    return jsonify({"error": "No brand found. Generate brand first."}), 404

# ══════════════════════════════════════════════════════════════
# BRAND EXPORT — PDF BRAND KIT
# ══════════════════════════════════════════════════════════════
@app.route("/api/brand/export-pdf", methods=["POST"])
@require_auth
def export_pdf():
    """Generate a downloadable PDF brand kit."""
    if not PDF_ENABLED:
        return jsonify({"error": "fpdf2 not installed. Run: pip install fpdf2"}), 500

    data   = request.json or {}
    email  = request.user_email
    brands = BRANDS_DB.get(email, [])
    brand  = brands[-1] if brands else {}

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_fill_color(10, 10, 15)
    pdf.rect(0, 0, 210, 60, 'F')
    pdf.set_text_color(232, 197, 71)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_xy(15, 20)
    pdf.cell(0, 10, brand.get("name", "Brand Name").upper())
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(200, 200, 200)
    pdf.set_xy(15, 38)
    pdf.cell(0, 8, f"Brand Kit — Generated by BrandCraft AI • {datetime.now().strftime('%B %d, %Y')}")

    # Section: Taglines
    pdf.set_text_color(10, 10, 15)
    pdf.set_xy(15, 70)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "AI-Generated Taglines")
    pdf.set_font("Helvetica", "", 11)
    y = 82
    for i, t in enumerate(brand.get("taglines", [])[:5]):
        pdf.set_xy(15, y)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 7, f"{i+1}. {t}")
        y += 9

    # Section: Brand Score
    score = brand.get("score", {})
    pdf.set_xy(15, y + 8)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(10, 10, 15)
    pdf.cell(0, 8, "AI Brand Score")
    y += 20
    for metric, label in [("memorability","Memorability"),("market_fit","Market Fit"),
                           ("uniqueness","Uniqueness"),("trust","Trust Signal"),("visual","Visual Appeal")]:
        val = score.get(metric, 80)
        pdf.set_xy(15, y)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(60, 7, label)
        # Progress bar
        pdf.set_fill_color(230, 230, 230)
        pdf.rect(65, y + 1, 80, 4, 'F')
        pdf.set_fill_color(26, 155, 138)
        pdf.rect(65, y + 1, val * 0.8, 4, 'F')
        pdf.set_text_color(26, 155, 138)
        pdf.set_xy(150, y)
        pdf.cell(0, 7, f"{val}%")
        y += 11

    # Section: Business Details
    biz = brand.get("business", {})
    if biz:
        y += 8
        pdf.set_xy(15, y)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(10, 10, 15)
        pdf.cell(0, 8, "Business Details")
        y += 12
        for k, v in [("Owner", biz.get("owner_name","")), ("Phone", biz.get("phone","")),
                     ("Email", biz.get("email","")), ("Location", f"{biz.get('city','')} {biz.get('country','')}")]:
            if v:
                pdf.set_xy(15, y)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(35, 7, k + ":")
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 7, str(v))
                y += 9

    # Footer
    pdf.set_fill_color(10, 10, 15)
    pdf.rect(0, 282, 210, 15, 'F')
    pdf.set_xy(15, 284)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 7, "Generated by BrandCraft — AI-Powered Branding Automation System")

    pdf_bytes = bytes(pdf.output())
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"brandcraft-kit-{brand.get('name','brand')}.pdf"
    )

# ══════════════════════════════════════════════════════════════
# SUBSCRIPTION ROUTES
# ══════════════════════════════════════════════════════════════
@app.route("/api/subscription/plans", methods=["GET"])
def get_plans():
    """GET /api/subscription/plans"""
    return jsonify({
        "plans": [
            {"id":"starter","name":"Starter","price_monthly":0,"price_annual":0,"currency":"INR",
             "features":["3 logo generations/month","5 AI taglines","Basic brand score","1 social media kit"]},
            {"id":"pro","name":"Pro","price_monthly":999,"price_annual":699,"currency":"INR",
             "features":["Unlimited logos","50 taglines/month","Full brand score","Complete social media kit",
                         "Advanced AI insights","Chatbot assistant"],"popular":True},
            {"id":"enterprise","name":"Enterprise","price_monthly":4999,"price_annual":3499,"currency":"INR",
             "features":["Everything in Pro","White-label","API access","10 team seats",
                         "Dedicated brand strategist","Custom AI fine-tuning","24/7 support"]}
        ]
    })


@app.route("/api/subscription/upgrade", methods=["POST"])
@require_auth
def upgrade_plan():
    """
    POST /api/subscription/upgrade
    Body: { "plan_id": str, "billing": "monthly"|"annual" }
    """
    data  = request.json or {}
    plan  = data.get("plan_id", "starter")
    email = request.user_email
    if email in USERS_DB:
        USERS_DB[email]["plan"] = plan
    # In production: integrate Razorpay / Stripe here
    return jsonify({
        "message": f"Upgraded to {plan} plan",
        "plan": plan,
        "billing": data.get("billing", "monthly"),
        "next_billing": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    })

# ══════════════════════════════════════════════════════════════
# USER / BRAND MANAGEMENT ROUTES
# ══════════════════════════════════════════════════════════════
@app.route("/api/user/profile", methods=["GET"])
@require_auth
def get_profile():
    email = request.user_email
    user  = USERS_DB.get(email, {})
    return jsonify({"email": email, "name": user.get("name"), "plan": user.get("plan", "free"),
                    "brands_count": len(BRANDS_DB.get(email, []))})


@app.route("/api/user/brands", methods=["GET"])
@require_auth
def get_brands():
    email  = request.user_email
    brands = BRANDS_DB.get(email, [])
    return jsonify({"brands": [{"id":b["id"],"name":b["name"],"created_at":b["created_at"],
                                "score":b.get("score",{}).get("overall",0)} for b in brands]})


@app.route("/api/user/brands/<brand_id>", methods=["GET"])
@require_auth
def get_brand(brand_id):
    email  = request.user_email
    brands = BRANDS_DB.get(email, [])
    brand  = next((b for b in brands if b["id"] == brand_id), None)
    if not brand:
        return jsonify({"error": "Brand not found"}), 404
    return jsonify(brand)

# ══════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════
def _build_logo_config(data: dict) -> dict:
    """Suggest logo design parameters based on brand input."""
    tone = data.get("tone", "Professional").lower()
    industry = data.get("industry", "").lower()
    icons = {"technology":"💻","healthcare":"🏥","food":"🍕","finance":"💰",
             "education":"🎓","travel":"✈️","fitness":"💪","creative":"🎨"}
    icon = icons.get(industry, "⚡")
    styles = {"professional":"modern","luxury":"minimal","bold":"bold","playful":"retro","minimal":"minimal"}
    style = next((v for k,v in styles.items() if k in tone), "modern")
    return {"icon": icon, "style": style, "font_weight": "800",
            "layout": "centered", "badge_style": "rounded"}


def _suggest_palette(color_style: str, industry: str) -> dict:
    """Suggest brand color palette."""
    palettes = {
        "dark": {"primary":"#0a0a0f","secondary":"#1a1a2e","accent":"#e8c547","light":"#f5f3ee","name":"Midnight Gold"},
        "teal": {"primary":"#0077b6","secondary":"#00b4d8","accent":"#1a9b8a","light":"#f0f7ff","name":"Ocean Teal"},
        "coral": {"primary":"#e84545","secondary":"#ff6b35","accent":"#ffc107","light":"#fff5f5","name":"Coral Sunset"},
        "green": {"primary":"#1b4332","secondary":"#40916c","accent":"#95d5b2","light":"#f8f9fa","name":"Forest Green"},
    }
    key = "teal" if "tech" in industry.lower() or "finance" in industry.lower() else \
          "green" if "health" in industry.lower() else \
          "coral" if "food" in industry.lower() else "dark"
    return palettes[key]


def _generate_description(data: dict) -> str:
    return (f"{data.get('brand_name','Your brand')} is a forward-thinking brand empowering "
            f"{', '.join(data.get('audience',['professionals']))} in the "
            f"{data.get('industry','technology')} space. Built on innovation, trust, and bold vision.")

# ══════════════════════════════════════════════════════════════
# HEALTH CHECK & MAIN
# ══════════════════════════════════════════════════════════════
@app.route("/api/health")
def health():
    return jsonify({"status":"ok","version":"1.0.0","ai_enabled":OPENAI_ENABLED and bool(OPENAI_KEY),
                    "pdf_enabled":PDF_ENABLED,"timestamp":datetime.utcnow().isoformat()})


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════╗
║   BrandCraft API Server v1.0             ║
║   http://localhost:5000                  ║
╠══════════════════════════════════════════╣
║  POST /api/auth/login                    ║
║  POST /api/auth/register                 ║
║  POST /api/brand/generate                ║
║  POST /api/brand/social-content          ║
║  POST /api/brand/growth-strategy         ║
║  POST /api/brand/chatbot                 ║
║  POST /api/brand/export-pdf              ║
║  POST /api/business/save                 ║
║  GET  /api/subscription/plans            ║
║  POST /api/subscription/upgrade          ║
║  GET  /api/user/profile                  ║
║  GET  /api/user/brands                   ║
╚══════════════════════════════════════════╝
    """)
    app.run(debug=True, port=5000, host="0.0.0.0")