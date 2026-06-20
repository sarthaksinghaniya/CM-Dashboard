import smtplib
import logging
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

def sync_send_email(email_to: str, subject: str, html_content: str) -> None:
    """
    Synchronous email dispatch using smtplib.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            f"\n[MOCK EMAIL DISPATCH] To: {email_to}\n"
            f"Subject: {subject}\n"
            f"Body:\n{html_content}\n"
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAILS_FROM_EMAIL
    msg["To"] = email_to

    # Attach html body
    msg.attach(MIMEText(html_content, "html"))

    try:
        # Connect to Gmail SMTP
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, email_to, msg.as_string())
            logger.info(f"Successfully sent email to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {str(e)}", exc_info=True)
        raise e

async def async_send_otp_email(email_to: str, otp: str) -> None:
    """
    Async wrapping of the sync SMTP dispatch using asyncio.to_thread.
    """
    subject = "Delhi CMO Grievance Portal - OTP Verification Code"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
            <h2 style="color: #0b3c5d;">Delhi CMO Grievance Management System</h2>
            <p>Hello,</p>
            <p>You requested a verification code to log in to the Chief Minister's Office Grievance Portal.</p>
            <div style="background-color: #f5f7fa; border-radius: 4px; padding: 15px; text-align: center; margin: 20px 0;">
                <span style="font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #d9534f;">{otp}</span>
            </div>
            <p style="font-size: 13px; color: #777;">This OTP is cryptographically secure and is valid for <strong>4 minutes</strong>. If you did not make this request, please ignore this email.</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #999; text-align: center;">Government of National Capital Territory of Delhi &copy; 2026</p>
        </body>
    </html>
    """
    await asyncio.to_thread(sync_send_email, email_to, subject, html_content)

async def async_send_complaint_acknowledgement_email(
    email_to: str,
    citizen_name: str,
    ticket_id: str,
    status: str,
    estimated_sla: str
) -> None:
    """
    Async wrapping of the complaint acknowledgement email dispatch.
    """
    subject = f"Grievance Lodged Successfully - Ticket {ticket_id}"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
            <h2 style="color: #0b3c5d;">Delhi Chief Minister's Office</h2>
            <h3 style="color: #5cb85c;">Grievance Registration Acknowledgement</h3>
            <p>Dear {citizen_name},</p>
            <p>Thank you for reaching out to the Chief Minister's Office. Your grievance has been registered successfully.</p>
            <div style="background-color: #f5f7fa; border-radius: 4px; padding: 15px; margin: 20px 0; border-left: 5px solid #0b3c5d;">
                <strong>Ticket ID:</strong> {ticket_id}<br>
                <strong>Status:</strong> {status}<br>
                <strong>Estimated SLA:</strong> {estimated_sla}
            </div>
            <p>You can track the progress of your grievance using the Ticket ID provided above.</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #999; text-align: center;">Government of National Capital Territory of Delhi &copy; 2026</p>
        </body>
    </html>
    """
    await asyncio.to_thread(sync_send_email, email_to, subject, html_content)

async def async_send_notification_email(
    email_to: str,
    subject: str,
    message: str
) -> None:
    """
    Async wrapping of a generic alert notification email dispatch.
    """
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
            <h2 style="color: #0b3c5d;">Delhi CMO Grievance Portal</h2>
            <h3 style="color: #d9534f;">New Alert Notification</h3>
            <p>{message}</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #999; text-align: center;">Government of National Capital Territory of Delhi &copy; 2026</p>
        </body>
    </html>
    """
    await asyncio.to_thread(sync_send_email, email_to, subject, html_content)

async def async_send_feedback_acknowledgement_email(
    email_to: str,
    ticket_id: str,
    rating: int,
    remarks: str
) -> None:
    """
    Async wrapping of the citizen feedback acknowledgement email dispatch.
    """
    subject = f"Feedback Received - Grievance Ticket {ticket_id}"
    stars = "★" * rating + "☆" * (5 - rating)
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="background-color: #0b3c5d; color: #fff; padding: 20px; text-align: center;">
                    <h2 style="margin: 0; font-size: 20px; font-weight: bold; letter-spacing: 1px;">DELHI CHIEF MINISTER'S OFFICE</h2>
                    <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Grievance Redressal Portal</p>
                </div>
                <div style="padding: 25px; background-color: #ffffff;">
                    <h3 style="color: #0b3c5d; margin-top: 0; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">Citizen Feedback Acknowledgement</h3>
                    <p>Dear Citizen,</p>
                    <p>Thank you for submitting your feedback for your resolved grievance. Your response has been successfully registered in our systems.</p>
                    
                    <div style="background-color: #f8f9fa; border-left: 4px solid #f0ad4e; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 5px 0; font-weight: bold; width: 120px; color: #555;">Ticket ID:</td>
                                <td style="padding: 5px 0; color: #333;">{ticket_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 5px 0; font-weight: bold; color: #555;">Rating:</td>
                                <td style="padding: 5px 0; color: #333;">
                                    <span style="font-size: 16px; font-weight: bold; color: #f0ad4e;">{stars}</span> ({rating}/5)
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 5px 0; font-weight: bold; color: #555; vertical-align: top;">Remarks:</td>
                                <td style="padding: 5px 0; color: #555; font-style: italic;">{remarks or "No remarks provided."}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p>Your feedback is vital to our reinforcement learning model and helps us dynamically adjust officer workloads, identify training requirements, and enhance our overall grievance response systems.</p>
                </div>
                <div style="background-color: #f5f7fa; padding: 15px; text-align: center; border-top: 1px solid #eee; font-size: 12px; color: #777;">
                    <p style="margin: 0;">This is an automated notification. Please do not reply to this email.</p>
                    <p style="margin: 5px 0 0 0; font-weight: bold;">Chief Minister's Office, Government of National Capital Territory of Delhi &copy; 2026</p>
                </div>
            </div>
        </body>
    </html>
    """
    await asyncio.to_thread(sync_send_email, email_to, subject, html_content)
