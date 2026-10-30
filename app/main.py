"""TeknTandao Media Cloud independent SaaS API. Development-only baseline."""
import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlparse
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field

DB = os.getenv("MEDIA_DB", "media_cloud.sqlite")
app = FastAPI(title="TeknTandao Media Cloud", version="0.6.0-dev")

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.executescript("""
      CREATE TABLE IF NOT EXISTS tenants(id TEXT PRIMARY KEY, name TEXT NOT NULL, secret_hash TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS campaigns(id TEXT PRIMARY KEY, tenant TEXT NOT NULL, name TEXT NOT NULL, brief TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS creators(id TEXT PRIMARY KEY, tenant TEXT NOT NULL, handle TEXT NOT NULL, profile_url TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS posts(id TEXT PRIMARY KEY, tenant TEXT NOT NULL, campaign_id TEXT NOT NULL, caption TEXT NOT NULL, status TEXT NOT NULL, platform TEXT NOT NULL);
    """)
    return c

def uid():
    return secrets.token_hex(16)

def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()

def tenant(x_api_key: str = Header(default="")):
    if not x_api_key:
        raise HTTPException(401, "Server-side API key required")
    with db() as c:
        row = c.execute("SELECT id FROM tenants WHERE secret_hash=?", (sha(x_api_key),)).fetchone()
    if row is None:
        raise HTTPException(401, "Invalid API key")
    return row["id"]

class TenantIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)

class CampaignIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    brief: str = Field(min_length=1)

class CreatorIn(BaseModel):
    handle: str = Field(min_length=1)
    profile_url: str

class PostIn(BaseModel):
    campaign_id: str
    caption: str
    platform: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "media-cloud", "publishing": "disabled"}

@app.post("/v1/tenants", status_code=201)
def create_tenant(payload: TenantIn, x_bootstrap_secret: str = Header(default="")):
    expected = os.getenv("MEDIA_BOOTSTRAP_SECRET", "")
    if not expected or not secrets.compare_digest(x_bootstrap_secret, expected):
        raise HTTPException(403, "Bootstrap secret required")
    key = "tmc_" + secrets.token_urlsafe(32)
    tenant_id = uid()
    with db() as c:
        c.execute("INSERT INTO tenants VALUES (?,?,?)", (tenant_id, payload.name, sha(key)))
    return {"tenant_id": tenant_id, "api_key": key, "warning": "Store key server-side; shown once"}

@app.post("/v1/campaigns", status_code=201)
def create_campaign(payload: CampaignIn, t=Depends(tenant)):
    item_id = uid()
    with db() as c:
        c.execute("INSERT INTO campaigns VALUES (?,?,?,?)", (item_id, t, payload.name, payload.brief))
    return {"id": item_id, "status": "draft"}

@app.get("/v1/campaigns")
def list_campaigns(t=Depends(tenant)):
    with db() as c:
        return [dict(x) for x in c.execute("SELECT * FROM campaigns WHERE tenant=?", (t,))]

@app.post("/v1/creators", status_code=201)
def register_creator(payload: CreatorIn, t=Depends(tenant)):
    parsed = urlparse(payload.profile_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(422, "HTTPS profile URL required")
    item_id = uid()
    with db() as c:
        c.execute("INSERT INTO creators VALUES (?,?,?,?)", (item_id, t, payload.handle, payload.profile_url))
    return {"id": item_id, "connected": False, "status": "awaiting_authorized_data"}

@app.post("/v1/posts", status_code=201)
def create_post(payload: PostIn, t=Depends(tenant)):
    with db() as c:
        campaign = c.execute("SELECT id FROM campaigns WHERE id=? AND tenant=?", (payload.campaign_id, t)).fetchone()
        if campaign is None:
            raise HTTPException(404, "Campaign not found")
        item_id = uid()
        c.execute("INSERT INTO posts VALUES (?,?,?,?,?,?)", (item_id,t,payload.campaign_id,payload.caption,"draft",payload.platform))
    return {"id": item_id, "status": "draft", "publishing_enabled": False}

@app.get("/v1/posts")
def list_posts(t=Depends(tenant)):
    with db() as c:
        return [dict(x) for x in c.execute("SELECT * FROM posts WHERE tenant=?", (t,))]
