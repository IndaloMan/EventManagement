"""UI string translations for public-facing pages. Admin UI remains English."""

# Add new languages here — picked up automatically by the Test Reservation button
SUPPORTED_LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
]

# Spanish day/month names for date formatting
_DAYS_LONG_ES = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado',
    'Sunday': 'Domingo'
}
_DAYS_SHORT_ES = {
    'Mon': 'lun', 'Tue': 'mar', 'Wed': 'mié',
    'Thu': 'jue', 'Fri': 'vie', 'Sat': 'sáb', 'Sun': 'dom'
}
_MONTHS_LONG_ES = {
    'January': 'enero', 'February': 'febrero', 'March': 'marzo',
    'April': 'abril', 'May': 'mayo', 'June': 'junio',
    'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
    'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
}
_MONTHS_SHORT_ES = {
    'Jan': 'ene', 'Feb': 'feb', 'Mar': 'mar', 'Apr': 'abr',
    'May': 'may', 'Jun': 'jun', 'Jul': 'jul', 'Aug': 'ago',
    'Sep': 'sep', 'Oct': 'oct', 'Nov': 'nov', 'Dec': 'dic'
}


def format_date_long(dt, lang='en'):
    """Return long date string: 'Saturday 13 June 2026, 14:00' / 'Sábado 13 de junio de 2026, 14:00'"""
    if lang == 'es':
        day_name = _DAYS_LONG_ES.get(dt.strftime('%A'), dt.strftime('%A'))
        month_name = _MONTHS_LONG_ES.get(dt.strftime('%B'), dt.strftime('%B'))
        return f"{day_name} {dt.day} de {month_name} de {dt.year}, {dt.strftime('%H:%M')}"
    return dt.strftime('%A %d %B %Y, %H:%M')


def format_date_short(dt, lang='en'):
    """Return short date string: 'Sat 13 Jun 2026' / 'sáb 13 jun 2026'"""
    if lang == 'es':
        day_name = _DAYS_SHORT_ES.get(dt.strftime('%a'), dt.strftime('%a'))
        month_name = _MONTHS_SHORT_ES.get(dt.strftime('%b'), dt.strftime('%b'))
        return f"{day_name} {dt.day} {month_name} {dt.year}"
    return dt.strftime('%a %d %b %Y')


TRANSLATIONS = {
    'en': {
        # Page / section titles
        'reserve_tickets': 'Reserve Tickets',
        'upcoming_events': 'Upcoming Events',
        'venues': 'Venues',
        'your_reservation': 'Your Reservation',
        'reservation_confirmed_title': 'Reservation Confirmed',

        # Reserve form
        'your_details': 'Your Details',
        'label_name': 'Name',
        'placeholder_name': 'Full name',
        'label_email': 'Email',
        'placeholder_email': 'For confirmation',
        'label_phone': 'Phone',
        'placeholder_phone': 'Optional',
        'label_tickets': 'Tickets',
        'label_quantity': 'Quantity',
        'per_person': 'per person',
        'tickets_remaining': 'tickets remaining',
        'agree_terms_prefix': 'I agree to the',
        'terms_link': 'Terms & Conditions',
        'payment_note': 'Payment is made at the {business} bar. This form reserves your place.',
        'btn_confirm': 'Confirm Reservation',
        'btn_cancel': 'Cancel',

        # Confirmation page
        'confirmed_heading': 'Reservation Confirmed!',
        'your_reference': 'Your reference code:',
        'ticket_singular': 'ticket',
        'ticket_plural': 'tickets',
        'total_label': 'Total:',
        'confirmation_sent': 'Confirmation sent to {email}',
        'show_reference': 'Please show this reference code when you arrive.',
        'payment_bar': 'Payment is made at the {business} bar.',

        # Reservation manage page
        'label_reference': 'Reference',
        'label_status': 'Status',
        'label_event': 'Event',
        'label_title': 'Title',
        'label_venue': 'Venue',
        'label_date': 'Date',
        'label_location': 'Location',
        'label_name_display': 'Name',
        'label_total': 'Total',
        'change_tickets': 'Change Tickets',
        'btn_update': 'Update Reservation',
        'confirm_cancel_question': 'Do you really want to cancel this reservation?',
        'btn_cancel_reservation': 'Cancel Reservation',
        'status_cancelled_msg': 'This reservation has been cancelled.',
        'status_paid_msg': 'This reservation has been paid.',
        'show_qr': 'Please show your reference code or QR code at the door.',

        # Status badge labels
        'status_pending': 'pending',
        'status_paid': 'paid',
        'status_cancelled': 'cancelled',

        # Events listing
        'free_entry': 'Free entry',
        'sold_out': 'SOLD OUT',
        'btn_reserve': 'Reserve Tickets',
        'no_events_heading': 'No upcoming events',
        'no_events_sub': 'Check back soon!',
        'btn_all_venues': 'All Venues',

        # Index
        'no_venues': 'No venues available',

        # Embed / generic
        'event_not_available': 'Event not available.',
        'no_upcoming_events': 'No upcoming events.',
    },
    'es': {
        # Page / section titles
        'reserve_tickets': 'Reservar Entradas',
        'upcoming_events': 'Próximos Eventos',
        'venues': 'Locales',
        'your_reservation': 'Tu Reserva',
        'reservation_confirmed_title': 'Reserva Confirmada',

        # Reserve form
        'your_details': 'Tus Datos',
        'label_name': 'Nombre',
        'placeholder_name': 'Nombre completo',
        'label_email': 'Email',
        'placeholder_email': 'Para confirmación',
        'label_phone': 'Teléfono',
        'placeholder_phone': 'Opcional',
        'label_tickets': 'Entradas',
        'label_quantity': 'Cantidad',
        'per_person': 'por persona',
        'tickets_remaining': 'entradas disponibles',
        'agree_terms_prefix': 'Acepto los',
        'terms_link': 'Términos y Condiciones',
        'payment_note': 'El pago se realiza en la barra de {business}. Este formulario reserva tu lugar.',
        'btn_confirm': 'Confirmar Reserva',
        'btn_cancel': 'Cancelar',

        # Confirmation page
        'confirmed_heading': '¡Reserva Confirmada!',
        'your_reference': 'Tu código de referencia:',
        'ticket_singular': 'entrada',
        'ticket_plural': 'entradas',
        'total_label': 'Total:',
        'confirmation_sent': 'Confirmación enviada a {email}',
        'show_reference': 'Por favor, muestra este código de referencia al llegar.',
        'payment_bar': 'El pago se realiza en la barra de {business}.',

        # Reservation manage page
        'label_reference': 'Referencia',
        'label_status': 'Estado',
        'label_event': 'Evento',
        'label_title': 'Título',
        'label_venue': 'Local',
        'label_date': 'Fecha',
        'label_location': 'Ubicación',
        'label_name_display': 'Nombre',
        'label_total': 'Total',
        'change_tickets': 'Cambiar Entradas',
        'btn_update': 'Actualizar Reserva',
        'confirm_cancel_question': '¿Realmente deseas cancelar esta reserva?',
        'btn_cancel_reservation': 'Cancelar Reserva',
        'status_cancelled_msg': 'Esta reserva ha sido cancelada.',
        'status_paid_msg': 'Esta reserva ha sido pagada.',
        'show_qr': 'Por favor, muestra tu código de referencia o código QR al llegar.',

        # Status badge labels
        'status_pending': 'pendiente',
        'status_paid': 'pagado',
        'status_cancelled': 'cancelado',

        # Events listing
        'free_entry': 'Entrada gratuita',
        'sold_out': 'AGOTADO',
        'btn_reserve': 'Reservar Entradas',
        'no_events_heading': 'No hay próximos eventos',
        'no_events_sub': '¡Vuelve pronto!',
        'btn_all_venues': 'Todos los Locales',

        # Index
        'no_venues': 'No hay locales disponibles',

        # Embed / generic
        'event_not_available': 'Evento no disponible.',
        'no_upcoming_events': 'No hay próximos eventos.',
    }
}


# Email translations (used by email_sender.py — no Jinja2 context)
EMAIL_TRANSLATIONS = {
    'en': {
        'subject_confirmed': 'Reservation Confirmed — {event} [{ref}]',
        'subject_cancelled': 'Reservation Cancelled — {event} [{ref}]',
        'subject_reset': '{promo} — Password Reset',
        'heading_confirmed': 'Reservation Confirmed',
        'heading_cancelled': 'Reservation Cancelled',
        'your_reference': 'Your reference code:',
        'label_event': 'Event',
        'label_venue': 'Venue',
        'label_when': 'When',
        'label_where': 'Where',
        'label_tickets': 'Tickets',
        'label_total': 'Total',
        'show_qr': 'Show this QR code at the bar:',
        'payment_note': 'Payment is made at the {business} bar.',
        'arrive_note': 'Please show this QR code or reference code when you arrive.',
        'modify_link': 'Modify or Cancel Reservation',
        'cancelled_note': 'This reservation is no longer valid. No payment is required.',
        'reset_intro': 'You requested a password reset. Click the button below to set a new password. This link expires in 1 hour.',
        'reset_button': 'Reset Password',
        'reset_ignore': 'If you did not request this, ignore this email. Your password will not change.',
    },
    'es': {
        'subject_confirmed': 'Reserva Confirmada — {event} [{ref}]',
        'subject_cancelled': 'Reserva Cancelada — {event} [{ref}]',
        'subject_reset': '{promo} — Restablecer Contraseña',
        'heading_confirmed': 'Reserva Confirmada',
        'heading_cancelled': 'Reserva Cancelada',
        'your_reference': 'Tu código de referencia:',
        'label_event': 'Evento',
        'label_venue': 'Local',
        'label_when': 'Cuándo',
        'label_where': 'Dónde',
        'label_tickets': 'Entradas',
        'label_total': 'Total',
        'show_qr': 'Muestra este código QR en la barra:',
        'payment_note': 'El pago se realiza en la barra de {business}.',
        'arrive_note': 'Por favor, muestra este código QR o código de referencia al llegar.',
        'modify_link': 'Modificar o Cancelar Reserva',
        'cancelled_note': 'Esta reserva ya no es válida. No se requiere ningún pago.',
        'reset_intro': 'Has solicitado restablecer tu contraseña. Haz clic en el botón de abajo para establecer una nueva. Este enlace caduca en 1 hora.',
        'reset_button': 'Restablecer Contraseña',
        'reset_ignore': 'Si no has solicitado esto, ignora este correo. Tu contraseña no cambiará.',
    }
}
