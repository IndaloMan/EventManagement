"""Sends emails via Gmail SMTP — reservation confirmations and password resets."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr


def _from_header(config, settings=None):
    email = config.get('SMTP_EMAIL', '')
    from_name = ''
    if settings and settings.smtp_from_name:
        from_name = settings.smtp_from_name
    return formataddr((from_name, email)) if from_name else email


def _promo_name(settings=None):
    if settings and settings.promo_display_name:
        return settings.promo_display_name
    return 'VIP Promotions'


def send_confirmation_email(config, reservation, event, qr_base64=None, settings=None):
    if not config.get('SMTP_EMAIL') or not config.get('SMTP_PASSWORD'):
        return False

    app_url = config.get('APP_URL', '')
    business = event.business
    end_display = event.end_time_text or (event.end_time.strftime('%H:%M') if event.end_time else '')
    time_str = event.start_time.strftime('%A %d %B %Y, %H:%M')
    if end_display:
        time_str += f' — {end_display}'

    total = event.price * reservation.num_tickets if event.price else 0
    manage_url = f"{app_url}/reservation/{reservation.reference_code}"
    promo_name = _promo_name(settings)

    qr_html = ''
    if qr_base64:
        qr_html = f'''
        <div style="text-align:center;margin:24px 0 8px;">
            <p style="color:#555555;font-size:0.8rem;margin-bottom:10px;">Show this QR code at the bar:</p>
            <img src="data:image/png;base64,{qr_base64}" alt="QR Code"
                 style="width:160px;height:160px;border:1px solid #dddddd;border-radius:8px;display:block;margin:0 auto;">
        </div>'''

    location_row = f"<tr><td style='padding:7px 0;color:#777777;font-size:0.85rem;'>Where</td><td style='padding:7px 0;font-size:0.85rem;'>{event.location}</td></tr>" if event.location else ''
    total_fmt = '{:g}'.format(float(total)) if total else '0'
    total_row = f"<tr><td style='padding:7px 0;color:#777777;font-size:0.85rem;'>Total</td><td style='padding:7px 0;font-size:0.85rem;font-weight:600;color:#1a8f3f;'>&euro;{total_fmt}</td></tr>" if total > 0 else ''
    payment_note = f"<p style='font-size:0.8rem;color:#777777;margin-top:12px;'>Payment is made at the {business.name} bar.</p>" if event.price and event.price > 0 else ''

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;max-width:480px;margin:0 auto;background:#ffffff;border:1px solid #e0e0e0;border-radius:12px;overflow:hidden;">
        <div style="padding:20px 24px;border-bottom:1px solid #e0e0e0;">
            <span style="font-size:1.1rem;font-weight:700;color:#0a84ff;">{promo_name}</span>
        </div>
        <div style="padding:24px;">
            <h2 style="margin:0 0 4px;font-size:1.05rem;color:#1a1a1a;">Reservation Confirmed</h2>
            <p style="color:#777777;font-size:0.85rem;margin:0 0 16px;">Your reference code:</p>
            <div style="text-align:center;background:#f5f5f5;border-radius:8px;padding:14px;margin-bottom:20px;">
                <span style="font-size:2rem;font-weight:700;color:#0a84ff;letter-spacing:3px;">{reservation.reference_code}</span>
            </div>
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:7px 0;color:#777777;font-size:0.85rem;">Event</td><td style="padding:7px 0;font-size:0.85rem;color:#1a1a1a;">{event.title}</td></tr>
                <tr><td style="padding:7px 0;color:#777777;font-size:0.85rem;">Venue</td><td style="padding:7px 0;font-size:0.85rem;color:#1a1a1a;">{business.name}</td></tr>
                <tr><td style="padding:7px 0;color:#777777;font-size:0.85rem;">When</td><td style="padding:7px 0;font-size:0.85rem;color:#1a1a1a;">{time_str}</td></tr>
                {location_row}
                <tr><td style="padding:7px 0;color:#777777;font-size:0.85rem;">Tickets</td><td style="padding:7px 0;font-size:0.85rem;color:#1a1a1a;">{reservation.num_tickets}</td></tr>
                {total_row}
            </table>
            {qr_html}
            {payment_note}
            <p style="font-size:0.8rem;color:#777777;margin-top:10px;">Please show this QR code or reference code when you arrive.</p>
            <div style="text-align:center;margin-top:20px;">
                <a href="{manage_url}" style="display:inline-block;background:#f5f5f5;color:#0a84ff;padding:10px 24px;border-radius:8px;text-decoration:none;font-size:0.85rem;border:1px solid #e0e0e0;">Modify or Cancel Reservation</a>
            </div>
        </div>
        <div style="padding:12px 24px;border-top:1px solid #e0e0e0;text-align:center;">
            <span style="font-size:0.75rem;color:#aaaaaa;">{promo_name}</span>
        </div>
    </div>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Reservation Confirmed — {event.title} [{reservation.reference_code}]'
    msg['From'] = _from_header(config, settings)
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


def send_cancellation_email(config, reservation, event, settings=None):
    if not config.get('SMTP_EMAIL') or not config.get('SMTP_PASSWORD'):
        return False

    business = event.business
    time_str = event.start_time.strftime('%A %d %B %Y, %H:%M')
    promo_name = _promo_name(settings)

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:480px;margin:0 auto;background:#1c1c1e;color:#ffffff;border-radius:16px;overflow:hidden;">
        <div style="background:#ff453a;padding:20px 24px;">
            <h1 style="margin:0;font-size:1.2rem;color:#fff;">{promo_name}</h1>
        </div>
        <div style="padding:24px;">
            <h2 style="margin:0 0 4px;font-size:1.1rem;">Reservation Cancelled</h2>
            <p style="color:#ababab;font-size:0.85rem;margin:0 0 20px;">Your reservation has been cancelled:</p>
            <div style="text-align:center;background:#0d0d0d;border-radius:12px;padding:16px;margin-bottom:20px;">
                <span style="font-size:1.5rem;font-weight:700;color:#ff453a;letter-spacing:2px;">{reservation.reference_code}</span>
            </div>
            <table style="width:100%;font-size:0.9rem;color:#ababab;">
                <tr><td style="padding:6px 0;color:#636366;">Event</td><td style="padding:6px 0;">{event.title}</td></tr>
                <tr><td style="padding:6px 0;color:#636366;">Venue</td><td style="padding:6px 0;">{business.name}</td></tr>
                <tr><td style="padding:6px 0;color:#636366;">When</td><td style="padding:6px 0;">{time_str}</td></tr>
                <tr><td style="padding:6px 0;color:#636366;">Tickets</td><td style="padding:6px 0;">{reservation.num_tickets}</td></tr>
            </table>
            <p style="font-size:0.85rem;color:#ababab;margin-top:16px;">This reservation is no longer valid. No payment is required.</p>
        </div>
    </div>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Reservation Cancelled — {event.title} [{reservation.reference_code}]'
    msg['From'] = _from_header(config, settings)
    msg['To'] = reservation.email
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP_SSL(config['SMTP_SERVER'], config['SMTP_PORT']) as server:
            server.login(config['SMTP_EMAIL'], config['SMTP_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f'Cancellation email failed: {e}')
        return False


def send_password_reset_email(config, email, reset_url, settings=None):
    if not config.get('SMTP_EMAIL') or not config.get('SMTP_PASSWORD'):
        return False

    promo_name = _promo_name(settings)

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:480px;margin:0 auto;background:#1c1c1e;color:#ffffff;border-radius:16px;overflow:hidden;">
        <div style="background:#0a84ff;padding:20px 24px;">
            <h1 style="margin:0;font-size:1.2rem;color:#fff;">{promo_name}</h1>
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
    msg['Subject'] = f'{promo_name} — Password Reset'
    msg['From'] = _from_header(config, settings)
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
