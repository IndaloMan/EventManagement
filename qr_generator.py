"""Generates QR codes for event reservation URLs and ticket references."""

import os
import io
import base64
import qrcode


def generate_event_qr(event_id, app_url, output_dir):
    """Generate a QR code PNG for an event's reservation page.

    Returns the filename of the generated QR code.
    """
    url = f"{app_url}/reserve/{event_id}"
    filename = f"qr_event_{event_id}.png"
    filepath = os.path.join(output_dir, filename)

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)

    return filename


def generate_reference_qr_base64(reference_code):
    """Generate a QR code as a base64 PNG string for embedding in HTML."""
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(reference_code)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
