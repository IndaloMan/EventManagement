"""Sends emails via Gmail SMTP — reservation confirmations and password resets."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_confirmation_email(config, reservation, event):
    if not config.get('SMTP_EMAIL') or not config.get('SMTP_PASSWORD'):
        return False

    business = event.business
    end_display = event.end_time_text or (event.end_time.strftime('%H:%M') if event.end_time else '')
    time_str = event.start_time.strftime('%A %d %B %Y, %H:%M')
    if end_display:
        time_str += f' — {end_display}'

    total = event.price * reservation.num_tickets if event.price else 0

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:480px;margin:0 auto;background:#1c1c1e;color:#ffffff;border-radius:16px;overflow:hidden;">
        <div style="background:#0a84ff;padding:20px 24px;">
            <h1 style="margin:0;font-size:1.2rem;color:#fff;">VIP Promotions</h1>
        </div>
        <div style="padding:24px;">
            <h2 style="margin:0 0 4px;font-size:1.1rem;">Reservation Confirmed</h2>
            <p style="color:#ababab;font-size:0.85rem;margin:0 0 20px;">Your reference code:</p>
            <div style="text-align:center;background:#0d0d0d;border-radius:12px;padding:16px;margin-bottom:20px;">
                <span style="font-size:2rem;font-weight:700;color:#0a84ff;letter-spacing:2px;">{reservation.reference_code}</span>
            </div>
            <table style="width:100%;font-size:0.9rem;color:#ababab;">
                <tr><td style="padding:6px 0;color:#636366;">Event</td><td style="padding:6px 0;">{event.title}</td></tr>
                <tr><td style="padding:6px 0;color:#636366;">Venue</td><td style="padding:6px 0;">{business.name}</td></tr>
                <tr><td style="padding:6px 0;color:#636366;">When</td><td style="padding:6px 0;">{time_str}</td></tr>
                {"<tr><td style='padding:6px 0;color:#636366;'>Where</td><td style='padding:6px 0;'>" + event.location + "</td></tr>" if event.location else ""}
                <tr><td style="padding:6px 0;color:#636366;">Tickets</td><td style="padding:6px 0;">{reservation.num_tickets}</td></tr>
                {"<tr><td style='padding:6px 0;color:#636366;'>Total</td><td style='padding:6px 0;font-weight:600;color:#30d158;'>&euro;" + f"{total:.2f}" + "</td></tr>" if total > 0 else ""}
            </table>
            {"<p style='font-size:0.85rem;color:#ababab;margin-top:16px;'>Payment is made at the " + business.name + " bar.</p>" if event.price and event.price > 0 else ""}
            <p style="font-size:0.85rem;color:#ababab;margin-top:12px;">Please show this reference code when you arrive.</p>
        </div>
    </div>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Reservation Confirmed — {event.title} [{reservation.reference_code}]'
    msg['From'] = config['SMTP_EMAIL']
    msg['To'] = reservation.email
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP_SSL(config['SMTP_SERVER'], config['SMTP_PORT']) as server:
            server.login(config['SMTP_EMAIL'], config['SMTP_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f'Email send failed: {e}')
        return False


def send_password_reset_email(config, email, reset_url):
    if not config.get('SMTP_EMAIL') or not config.get('SMTP_PASSWORD'):
        return False

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:480px;margin:0 auto;background:#1c1c1e;color:#ffffff;border-radius:16px;overflow:hidden;">
        <div style="background:#0a84ff;padding:20px 24px;">
            <h1 style="margin:0;font-size:1.2rem;color:#fff;">VIP Promotions</h1>
        </div>
        <div style="padding:24px;">
            <h2 style="margin:0 0 12px;font-size:1.1rem;">Password Reset</h2>
            <p style="color:#ababab;font-size:0.85rem;margin:0 0 20px;">
                You requested a password reset. Click the button below to set a new password.
                This link expires in 1 hour.
            </p>
            <div style="text-align:center;margin:24px 0;">
                <a href="{reset_url}" style="display:inline-block;background:#0a84ff;color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:600;font-size:0.95rem;">Reset Password</a>
            </div>
            <p style="color:#636366;font-size:0.75rem;margin-top:20px;">
                If you did not request this, ignore this email. Your password will not change.
            </p>
        </div>
    </div>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'VIP Promotions — Password Reset'
    msg['From'] = config['SMTP_EMAIL']
    msg['To'] = email
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP_SSL(config['SMTP_SERVER'], config['SMTP_PORT']) as server:
            server.login(config['SMTP_EMAIL'], config['SMTP_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f'Password reset email failed: {e}')
        return False
