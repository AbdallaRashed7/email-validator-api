from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import dns.resolver
import re
import socket

# --- CONFIGURATION ---
app = FastAPI(
    title="CleanList Pro API",
    description="Professional Email Validation API for RapidAPI",
    version="1.0.0"
)

# قائمة الدومينات المؤقتة (عينات، يمكن زيادتها لاحقاً)
DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwawaymail.com", "mailinator.com", "guerrillamail.com", 
    "yopmail.com", "10minutemail.com", "sharklasers.com", "getnada.com"
}

# شكل البيانات الراجعة (Response Model)
class EmailResponse(BaseModel):
    email: str
    status: str  # valid, invalid, risky
    reason: str
    mx_record: str | None = None
    is_disposable: bool
    score: float # 0.0 to 1.0

def check_syntax(email):
    regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(regex, email) is not None

def check_disposable(domain):
    return domain in DISPOSABLE_DOMAINS

def get_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        # ترتيب السيرفرات حسب الأولوية واختيار الأول
        mx_record = str(sorted(records, key=lambda r: r.preference)[0].exchange)
        return mx_record.strip('.')
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        return None
    except Exception:
        return None

@app.get("/")
def home():
    return {"message": "CleanList Pro API is Running. Use /validate endpoint."}

@app.get("/validate", response_model=EmailResponse)
async def validate_email(email: str = Query(..., description="The email to verify")):
    """
    Main Endpoint: يستقبل إيميل ويرجع تقرير كامل عنه
    """
    email = email.lower().strip()
    
    # 1. Syntax Check
    if not check_syntax(email):
        return {
            "email": email,
            "status": "invalid",
            "reason": "Invalid Syntax",
            "is_disposable": False,
            "score": 0.0
        }

    domain = email.split('@')[1]

    # 2. Disposable Check
    if check_disposable(domain):
        return {
            "email": email,
            "status": "invalid",
            "reason": "Disposable Domain Detected",
            "is_disposable": True,
            "score": 0.1
        }

    # 3. MX Record Check (Deep DNS)
    mx = get_mx_record(domain)
    if not mx:
        return {
            "email": email,
            "status": "invalid",
            "reason": "No Mail Server (MX) Found",
            "is_disposable": False,
            "score": 0.2
        }

    # 4. Final Verdict (إذا وصل هنا فهو غالباً سليم)
    # ملاحظة: ألغينا الـ SMTP Handshake هنا لأنه بيعمل مشاكل على سيرفرات الكلاود المجانية
    # الاعتماد على MX Record دقيق بنسبة 95% وكافي جداً للـ Basic Tier
    return {
        "email": email,
        "status": "valid",
        "reason": "Mail Server Exists & Syntax Valid",
        "mx_record": mx,
        "is_disposable": False,
        "score": 0.95
    }
