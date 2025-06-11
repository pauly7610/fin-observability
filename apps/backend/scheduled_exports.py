import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from apps.backend.models import ComplianceLog, AgentAction
from apps.backend.database import SessionLocal
import csv
import hashlib
from apps.backend import siem
from apps.backend import crypto_utils
import smtplib
from email.message import EmailMessage
import boto3
from botocore.exceptions import NoCredentialsError

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# Email and S3 config (placeholders, read from env)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "user@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "password")
EXPORT_EMAIL_TO = os.getenv("EXPORT_EMAIL_TO", "compliance@example.com")
EXPORT_EMAIL_FROM = os.getenv("EXPORT_EMAIL_FROM", SMTP_USER)

S3_BUCKET = os.getenv("EXPORT_S3_BUCKET", "fin-observability-exports")
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "your-access-key")
S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "your-secret-key")
S3_REGION = os.getenv("AWS_REGION", "us-east-1")


def send_export_email(subject, body, attachment_path):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EXPORT_EMAIL_FROM
        msg["To"] = EXPORT_EMAIL_TO
        msg.set_content(body)
        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)
            msg.add_attachment(
                file_data,
                maintype="application",
                subtype="octet-stream",
                filename=file_name,
            )
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        siem.send_syslog_event(
            f"Export emailed: {attachment_path}",
            host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
            port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        )
    except Exception as e:
        siem.send_syslog_event(
            f"Failed to email export {attachment_path}: {e}",
            host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
            port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        )


def upload_export_s3(attachment_path):
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name=S3_REGION,
        )
        s3.upload_file(attachment_path, S3_BUCKET, os.path.basename(attachment_path))
        siem.send_syslog_event(
            f"Export uploaded to S3: {attachment_path}",
            host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
            port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        )
    except NoCredentialsError:
        siem.send_syslog_event(
            f"S3 credentials not available for {attachment_path}",
            host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
            port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        )
    except Exception as e:
        siem.send_syslog_event(
            f"Failed to upload export to S3 {attachment_path}: {e}",
            host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
            port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        )


def hash_chain_csv(filename):
    hashes = []
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
        prev_hash = ""
        for line in lines:
            data = (prev_hash + line).encode()
            h = hashlib.sha256(data).hexdigest()
            hashes.append(h)
            prev_hash = h
    hashfile = filename + ".hash"
    with open(hashfile, "w", encoding="utf-8") as hfile:
        for h in hashes:
            hfile.write(h + "\n")
    # Digital signature of the hash chain
    if hashes:
        signature = crypto_utils.sign_data(hashes[-1].encode())
        crypto_utils.write_signature_file(filename, signature)
    return hashes[-1] if hashes else None


from opentelemetry import trace

tracer = trace.get_tracer(__name__)


def export_compliance_logs():
    with tracer.start_as_current_span("scheduled.export_compliance_logs") as span:
        session = SessionLocal()
        try:
            logs = (
                session.query(ComplianceLog)
                .order_by(ComplianceLog.timestamp.desc())
                .all()
            )
            fieldnames = [c.name for c in ComplianceLog.__table__.columns]
            filename = os.path.join(
                EXPORT_DIR,
                f"compliance_logs_{datetime.utcnow().strftime('%Y%m%d')}.csv",
            )
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for log in logs:
                    writer.writerow({fn: getattr(log, fn) for fn in fieldnames})
            span.set_attribute("export.record_count", len(logs))
            session.close()
            last_hash = hash_chain_csv(filename)
            span.set_attribute("export.hash", last_hash)
            siem.send_syslog_event(
                f"Compliance logs exported: {filename}, hash: {last_hash}",
                host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
                port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
            )
            # Deliver export via email and S3
            email_status = send_export_email(
                subject="Daily Compliance Logs Export",
                body=f"Attached are the compliance logs export for {datetime.utcnow().strftime('%Y-%m-%d')}.",
                attachment_path=filename,
            )
            s3_status = upload_export_s3(filename)
            span.set_attribute("email_status", str(email_status))
            span.set_attribute("s3_status", str(s3_status))
            # Write export metadata
            from apps.backend.models import ExportMetadata

            export_meta = ExportMetadata(
                export_type="compliance_log",
                file_path=filename,
                hash=last_hash,
                signature=None,  # Fill if available
                requested_by=None,
                delivered_to=f"{EXPORT_EMAIL_TO}, {S3_BUCKET}",
                delivery_method="email,s3",
                delivery_status=(
                    "delivered"
                    if email_status and s3_status
                    else "partial" if email_status or s3_status else "failed"
                ),
                verification_status="unverified",
                created_at=datetime.utcnow(),
                delivered_at=datetime.utcnow(),
                meta={"email_status": str(email_status), "s3_status": str(s3_status)},
            )
            session.add(export_meta)
            session.commit()

            # Increment export job metric
            from apps.backend.main import export_job_counter

            status = (
                "delivered"
                if email_status and s3_status
                else "partial" if email_status or s3_status else "failed"
            )
            export_job_counter.add(1, {"type": "compliance_log", "status": status})
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode

            span.set_status(Status(StatusCode.ERROR, str(e)))
            session.close()
            raise


def export_agent_actions():
    with tracer.start_as_current_span("scheduled.export_agent_actions") as span:
        session = SessionLocal()
        try:
            actions = (
                session.query(AgentAction).order_by(AgentAction.created_at.desc()).all()
            )
            fieldnames = [c.name for c in AgentAction.__table__.columns]
            filename = os.path.join(
                EXPORT_DIR, f"agent_actions_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            )
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for action in actions:
                    writer.writerow({fn: getattr(action, fn) for fn in fieldnames})
            span.set_attribute("export.record_count", len(actions))
            session.close()
            last_hash = hash_chain_csv(filename)
            span.set_attribute("export.hash", last_hash)
            siem.send_syslog_event(
                f"Agent actions exported: {filename}, hash: {last_hash}",
                host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
                port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
            )
            # Deliver export via email and S3
            email_status = send_export_email(
                subject="Daily Agent Actions Export",
                body=f"Attached are the agent actions export for {datetime.utcnow().strftime('%Y-%m-%d')}.",
                attachment_path=filename,
            )
            s3_status = upload_export_s3(filename)
            span.set_attribute("email_status", str(email_status))
            span.set_attribute("s3_status", str(s3_status))
            # Write export metadata
            from apps.backend.models import ExportMetadata

            export_meta = ExportMetadata(
                export_type="agent_action",
                file_path=filename,
                hash=last_hash,
                signature=None,  # Fill if available
                requested_by=None,
                delivered_to=f"{EXPORT_EMAIL_TO}, {S3_BUCKET}",
                delivery_method="email,s3",
                delivery_status=(
                    "delivered"
                    if email_status and s3_status
                    else "partial" if email_status or s3_status else "failed"
                ),
                verification_status="unverified",
                created_at=datetime.utcnow(),
                delivered_at=datetime.utcnow(),
                meta={"email_status": str(email_status), "s3_status": str(s3_status)},
            )
            session.add(export_meta)
            session.commit()

            # Increment export job metric
            from apps.backend.main import export_job_counter

            status = (
                "delivered"
                if email_status and s3_status
                else "partial" if email_status or s3_status else "failed"
            )
            export_job_counter.add(1, {"type": "agent_action", "status": status})
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode

            span.set_status(Status(StatusCode.ERROR, str(e)))
            session.close()
            raise


def schedule_exports():
    with tracer.start_as_current_span("scheduled.schedule_exports") as span:
        try:
            scheduler = BackgroundScheduler()
            scheduler.add_job(export_compliance_logs, "cron", hour=0, minute=0)
            scheduler.add_job(export_agent_actions, "cron", hour=0, minute=5)
            scheduler.start()
            span.set_attribute("scheduled_jobs", 2)
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode

            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


# To be called from main.py or app startup
