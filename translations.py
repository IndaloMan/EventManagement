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
        # ── Shared baseline ───────────────────────────────────────────────────
        # Buttons
        'btn_save':       'Save',
        'btn_cancel':     'Cancel',
        'btn_delete':     'Delete',
        'btn_edit':       'Edit',
        'btn_add':        'Add',
        'btn_back':       'Back',
        'btn_confirm':    'Confirm',
        'btn_create':     'Create',
        'btn_update':     'Update',
        'btn_close':      'Close',
        'btn_search':     'Search',

        # Common labels
        'label_name':        'Name',
        'label_email':       'Email',
        'label_phone':       'Phone',
        'label_date':        'Date',
        'label_status':      'Status',
        'label_actions':     'Actions',
        'label_notes':       'Notes',
        'label_price':       'Price',
        'label_total':       'Total',
        'label_description': 'Description',
        'label_role':        'Role',
        'label_type':        'Type',

        # Status values
        'status_active':    'Active',
        'status_inactive':  'Inactive',
        'status_pending':   'Pending',
        'status_paid':      'Paid',
        'status_cancelled': 'Cancelled',
        'status_complete':  'Complete',

        # Common UI
        'no_results':     'No results found.',
        'are_you_sure':   'Are you sure?',
        'changes_saved':  'Changes saved.',
        'error_generic':  'An error occurred.',
        'field_required': 'Required',
        'field_optional': 'Optional',
        'loading':        'Loading…',

        # Navigation
        'nav_dashboard': 'Dashboard',
        'nav_settings':  'Settings',
        'nav_users':     'Users',
        'nav_logout':    'Log out',

        # ── App-specific ──────────────────────────────────────────────────────
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
        'btn_pay_online': 'Reserve & Pay Online',
        'btn_cancel': 'Cancel',
        'stripe_redirect_note': "You'll be taken to our secure payment page after confirming.",
        'payment_method': 'Payment Method',
        'pay_online_now': 'Pay online now (card)',
        'pay_at_bar': 'Pay at the {business} bar',
        'split_tickets_toggle': 'Send individual tickets to each person?',
        'ticket_n_email': 'Ticket {n} email',
        'group_booking_note': 'Each person will receive their own confirmation email.',
        'group_booking_label': 'Group Booking',
        'no_email_provided': 'No email',

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

        # Stripe pages
        'payment_confirmed': 'Payment Confirmed!',
        'paid_online': 'paid online',
        'payment_cancelled': 'Payment Cancelled',
        'reservation_held': 'Your reservation is still held.',
        'pending_payment': 'pending payment',
        'try_payment_again': 'Try Payment Again',
        'view_reservation_pay_bar': 'View Reservation (Pay at Bar)',
        'view_reservation': 'View Reservation',
    },
    'es': {
        # ── Shared baseline ───────────────────────────────────────────────────
        # Buttons
        'btn_save':       'Guardar',
        'btn_cancel':     'Cancelar',
        'btn_delete':     'Eliminar',
        'btn_edit':       'Editar',
        'btn_add':        'Añadir',
        'btn_back':       'Volver',
        'btn_confirm':    'Confirmar',
        'btn_create':     'Crear',
        'btn_update':     'Actualizar',
        'btn_close':      'Cerrar',
        'btn_search':     'Buscar',

        # Common labels
        'label_name':        'Nombre',
        'label_email':       'Email',
        'label_phone':       'Teléfono',
        'label_date':        'Fecha',
        'label_status':      'Estado',
        'label_actions':     'Acciones',
        'label_notes':       'Notas',
        'label_price':       'Precio',
        'label_total':       'Total',
        'label_description': 'Descripción',
        'label_role':        'Rol',
        'label_type':        'Tipo',

        # Status values
        'status_active':    'Activo',
        'status_inactive':  'Inactivo',
        'status_pending':   'Pendiente',
        'status_paid':      'Pagado',
        'status_cancelled': 'Cancelado',
        'status_complete':  'Completado',

        # Common UI
        'no_results':     'No se encontraron resultados.',
        'are_you_sure':   '¿Estás seguro?',
        'changes_saved':  'Cambios guardados.',
        'error_generic':  'Se produjo un error.',
        'field_required': 'Obligatorio',
        'field_optional': 'Opcional',
        'loading':        'Cargando…',

        # Navigation
        'nav_dashboard': 'Panel',
        'nav_settings':  'Configuración',
        'nav_users':     'Usuarios',
        'nav_logout':    'Cerrar sesión',

        # ── App-specific ──────────────────────────────────────────────────────
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
        'btn_pay_online': 'Reservar y Pagar Online',
        'btn_cancel': 'Cancelar',
        'stripe_redirect_note': 'Serás redirigido a nuestra página de pago seguro tras confirmar.',
        'payment_method': 'Método de Pago',
        'pay_online_now': 'Pagar online ahora (tarjeta)',
        'pay_at_bar': 'Pagar en la barra de {business}',
        'split_tickets_toggle': '¿Enviar entradas individuales a cada persona?',
        'ticket_n_email': 'Email entrada {n}',
        'group_booking_note': 'Cada persona recibirá su propio email de confirmación.',
        'group_booking_label': 'Reserva de Grupo',
        'no_email_provided': 'Sin email',

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

        # Stripe pages
        'payment_confirmed': '¡Pago Confirmado!',
        'paid_online': 'pagado online',
        'payment_cancelled': 'Pago Cancelado',
        'reservation_held': 'Tu reserva sigue reservada.',
        'pending_payment': 'pago pendiente',
        'try_payment_again': 'Intentar Pago de Nuevo',
        'view_reservation_pay_bar': 'Ver Reserva (Pagar en la Barra)',
        'view_reservation': 'Ver Reserva',
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
        'subject_paid': '{tickets} purchase confirmation — {event} [{ref}]',
        'heading_paid': '{tickets} purchase confirmation',
        'show_qr_paid': 'Show this QR code at event door:',
        'payment_note_paid': 'Payment made online via Stripe.',
        'modify_link': 'Modify or Cancel Reservation',
        'cancelled_note': 'This reservation is no longer valid. No payment is required.',
        'reset_intro': 'You requested a password reset. Click the button below to set a new password. This link expires in 1 hour.',
        'reset_button': 'Reset Password',
        'reset_ignore': 'If you did not request this, ignore this email. Your password will not change.',
        'group_extra_heading': 'Additional tickets in your group (no email provided):',
        'group_extra_note': 'Please forward or print these reference codes for the other members of your group.',
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
        'subject_paid': 'Confirmación de compra de {tickets} — {event} [{ref}]',
        'heading_paid': 'Confirmación de compra de {tickets}',
        'show_qr_paid': 'Muestra este código QR en la puerta del evento:',
        'payment_note_paid': 'Pago realizado online a través de Stripe.',
        'modify_link': 'Modificar o Cancelar Reserva',
        'cancelled_note': 'Esta reserva ya no es válida. No se requiere ningún pago.',
        'reset_intro': 'Has solicitado restablecer tu contraseña. Haz clic en el botón de abajo para establecer una nueva. Este enlace caduca en 1 hora.',
        'reset_button': 'Restablecer Contraseña',
        'reset_ignore': 'Si no has solicitado esto, ignora este correo. Tu contraseña no cambiará.',
        'group_extra_heading': 'Entradas adicionales de tu grupo (sin email):',
        'group_extra_note': 'Por favor reenvía o imprime estos códigos de referencia para los demás miembros de tu grupo.',
    }
}
