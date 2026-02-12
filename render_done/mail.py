# SPDX-FileCopyrightText: © 2026 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import re
from smtplib import SMTP_SSL, SMTPException
from email.message import EmailMessage

import bpy
from .utils import get_package_name

# compile this only once so that the actual check can be quick
# note this email pattern might be overly restrictive,
# see: https://www.regular-expressions.info/email.html
valid_email_pattern = re.compile(
    r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE
)


def is_valid_email_address(email: str) -> bool:
    """Check if the provided string is a valid email address.

    Args:
        email: The email address string to validate.

    Returns:
        True if the email matches the valid email pattern, False otherwise.
    """
    return valid_email_pattern.match(email) is not None


def verify_smtp_connection():
    """Test the SMTP connection with current addon preferences.

    Attempts to establish an SMTP_SSL connection using the configured server,
    port, sender email, and password. Updates the global connection_status
    variable with the result.

    Returns:
        True if the connection and login were successful, False otherwise.
        Also returns False if online access is blocked by user settings.
    """
    if bpy.app.online_access:
        prefs = bpy.context.preferences.addons[get_package_name()].preferences  # type: ignore
        password = bpy.context.window_manager.password  # type: ignore
        try:
            with SMTP_SSL(host=prefs.server, port=prefs.port) as smtp:
                smtp.login(user=prefs.sender, password=password)  # type: ignore (if password is None login will fail which is perfectly ok)
                smtp.noop()
            bpy.context.window_manager.connection_status = "Connection: ok" # type: ignore
            return True
        except Exception as e:  # not just smtp exceptions also socket.gaierror
            bpy.context.window_manager.connection_status = f"Connection: error {str(e)}" # type: ignore
            return False
    else:
        bpy.context.window_manager.connection_status =  "Connection: blocked by user (see prefs|system|network)"  # type: ignore


def send_smtp_message(content: str):
    """Send an email message via SMTP.

    Creates an email message with the provided content and sends it through
    the configured SMTP server using credentials from addon preferences.
    Updates the global connection_status variable with the result.

    Args:
        content: The body text of the email message to send.

    Returns:
        True if the message was sent successfully, False if sending failed.
    """
    prefs = bpy.context.preferences.addons[get_package_name()].preferences  # type: ignore

    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "Render job completed"
    msg["From"] = prefs.sender
    msg["To"] = prefs.email

    if bpy.app.online_access:
        password = bpy.context.window_manager.password  # type: ignore
        try:
            with SMTP_SSL(host=prefs.server, port=prefs.port) as smtp:
                smtp.login(user=prefs.sender, password=password)  # type: ignore (if password is None login will fail which is perfectly ok)
                smtp.send_message(msg)
                smtp.quit()
            bpy.context.window_manager.connection_status = "Connection: message sent" # type: ignore
            return True
        except Exception as e:  # not just smtp exceptions also socket.gaierror
            bpy.context.window_manager.connection_status = f"Connection: error {str(e)}" # type: ignore
            return False
    else:
        bpy.context.window_manager.connection_status =  "Connection: blocked by user (see prefs|system|network)"  # type: ignore
        return False