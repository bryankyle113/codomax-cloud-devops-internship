import os
import time
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)

# Normalize postgres:// URLs from cloud providers to postgresql:// for SQLAlchemy
db_url = os.getenv("DATABASE_URL", "sqlite:///cloudpulse.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class MonitoredService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="PENDING")
    status_code = db.Column(db.Integer, nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    last_checked = db.Column(db.String(50), default="Never")


class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(20), default="OPEN")  # OPEN or RESOLVED
    details = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)


with app.app_context():
    db.create_all()
    if MonitoredService.query.count() == 0:
        defaults = [
            MonitoredService(name="GitHub API", url="https://api.github.com"),
            MonitoredService(name="Cloudflare DNS", url="https://1.1.1.1"),
        ]
        db.session.add_all(defaults)
        db.session.commit()


def run_health_checks():
    services = MonitoredService.query.all()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    for svc in services:
        prev_status = svc.status
        start = time.perf_counter()
        err_msg = ""
        try:
            resp = requests.get(svc.url, timeout=5)
            elapsed = int((time.perf_counter() - start) * 1000)
            svc.status_code = resp.status_code
            svc.latency_ms = elapsed
            svc.status = "UP" if resp.status_code < 400 else "DOWN"
        except requests.RequestException as exc:
            svc.status_code = 0
            svc.latency_ms = None
            svc.status = "DOWN"
            err_msg = exc.__class__.__name__

        svc.last_checked = now_str

        if svc.status == "DOWN" and prev_status != "DOWN":
            reason = f"HTTP {svc.status_code}" if svc.status_code else f"Connection Error ({err_msg})"
            db.session.add(
                Incident(
                    service_name=svc.name,
                    url=svc.url,
                    state="OPEN",
                    details=f"Outage detected: {reason}",
                    timestamp=now_str,
                )
            )
        elif svc.status == "UP" and prev_status == "DOWN":
            open_inc = Incident.query.filter_by(service_name=svc.name, state="OPEN").first()
            if open_inc:
                open_inc.state = "RESOLVED"
                open_inc.details += f" | Recovered at {now_str}"

    db.session.commit()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "cloudpulse", "database": db_url.split(":")[0]}), 200


@app.route("/api/status", methods=["GET"])
def get_status():
    services = MonitoredService.query.order_by(MonitoredService.id.asc()).all()
    incidents = Incident.query.order_by(Incident.id.desc()).limit(10).all()
    return jsonify({
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "status": s.status,
                "status_code": s.status_code,
                "latency_ms": s.latency_ms,
                "last_checked": s.last_checked,
            }
            for s in services
        ],
        "incidents": [
            {
                "id": i.id,
                "service_name": i.service_name,
                "url": i.url,
                "state": i.state,
                "details": i.details,
                "timestamp": i.timestamp,
            }
            for i in incidents
        ],
    })


@app.route("/api/services", methods=["POST"])
def add_service():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    if not name or not url:
        return jsonify({"error": "Name and URL are required"}), 400
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    svc = MonitoredService(name=name, url=url)
    db.session.add(svc)
    db.session.commit()
    run_health_checks()
    return jsonify({"message": "Service added"}), 201


@app.route("/api/services/<int:svc_id>", methods=["DELETE"])
def delete_service(svc_id):
    svc = db.session.get(MonitoredService, svc_id)
    if not svc:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(svc)
    db.session.commit()
    return jsonify({"message": "Service deleted"}), 200


@app.route("/api/check", methods=["POST"])
def trigger_checks():
    run_health_checks()
    return jsonify({"message": "Health checks completed"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
