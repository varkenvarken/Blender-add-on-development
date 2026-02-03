# SPDX-FileCopyrightText: © 2026 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# NOTE: this example has the SMTP password as a plain text string property.
# This is for demonstration purposes only, and you should NOT use this in any real scenario!

import re
from smtplib import SMTP_SSL, SMTPException
from email.message import EmailMessage
from typing import Literal

import bpy
from bpy.utils import register_class, unregister_class
from bpy_extras.io_utils import ImportHelper
from bpy.types import Context

# to prevent having to annotate the return type of every execute method with this rather unreadable chunk
EXECUTE_RETURN = set[
    Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]
]

bl_info = {
    "name": "Mail example",
    "author": "Michel Anders",
    "version": (0, 0, 1),
    "blender": (5, 0, 0),
    "location": "User preferences",
    "description": "Send a test mail",
    "category": "Render",
}

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


connection_status = "Connection: unknown"


def verify_smtp_connection() -> bool:
    """Test the SMTP connection with current addon preferences.

    Attempts to establish an SMTP_SSL connection using the configured server,
    port, sender email, and password. Updates the global connection_status
    variable with the result.

    Returns:
        True if the connection and login were successful, False otherwise.
        Also returns False if online access is blocked by user settings.
    """
    global connection_status

    if bpy.app.online_access:  #  or bpy.app.online_access_override   not needed, override indicates when overridden, that'all
        assert bpy.context.preferences is not None  # keep Pylance happy
        prefs: RenderDonePreferences = bpy.context.preferences.addons[
            __name__
        ].preferences  # type: ignore
        try:
            with SMTP_SSL(host=prefs.server, port=prefs.port) as smtp:
                smtp.login(user=prefs.sender, password=prefs.password)  # type: ignore (if password is None login will fail which is perfectly ok)
                smtp.noop()
                connection_status = "Connection: ok"
            return True
        except Exception as e:  # not just smtp exceptions also socket.gaierror
            connection_status = f"Connection: error {str(e)}"
            return False
    else:
        connection_status = "Connection: blocked by user (see prefs|system|network)"
        return False


def send_smtp_message(content: str) -> bool:
    """Send an email message via SMTP.

    Creates an email message with the provided content and sends it through
    the configured SMTP server using credentials from addon preferences.
    Updates the global connection_status variable with the result.

    Args:
        content: The body text of the email message to send.

    Returns:
        True if the message was sent successfully, False if sending failed.
    """
    global connection_status

    assert bpy.context.preferences is not None  # keep Pylance happy
    prefs: RenderDonePreferences = bpy.context.preferences.addons[__name__].preferences  # type: ignore

    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "Render job completed"
    msg["From"] = prefs.sender
    msg["To"] = prefs.email

    try:
        with SMTP_SSL(host=prefs.server, port=prefs.port) as smtp:
            smtp.login(user=prefs.sender, password=prefs.password)  # type: ignore (if password is None login will fail which is perfectly ok)
            smtp.send_message(msg)
            smtp.quit()
            connection_status = "Connection: message sent"
        return True
    except (SMTPException, RuntimeError) as e:
        connection_status = f"Connection: error {str(e)}"
        return False


class SendTestmail(bpy.types.Operator):
    bl_idname = "workspace.send_testmail"
    bl_label = "Send a testmail"

    def execute(self, context: Context) -> EXECUTE_RETURN:
        if send_smtp_message("test email"):
            self.report({"INFO"}, "SMTP server connection ok")
        else:
            self.report({"ERROR"}, "SMTP server connection failed")
        return {"FINISHED"}


class VerifyServer(bpy.types.Operator):
    bl_idname = "workspace.verify_server"
    bl_label = "Verify SMTP server"

    def execute(self, context: Context) -> EXECUTE_RETURN:
        if verify_smtp_connection():
            self.report({"INFO"}, "SMTP server connection ok")
        else:
            self.report({"ERROR"}, "SMTP server connection failed")
        return {"FINISHED"}


def reset_status(self, context):
    """
    helper function to reset the connection_status variable.
    """
    global connection_status
    connection_status = "Connection: unknown"


class RenderDonePreferences(bpy.types.AddonPreferences):
    bl_idname = __name__  # important: this links these preferences with the current add-on; you still need to register the class though

    email: bpy.props.StringProperty(
        name="Recipient address",
        description="Valid email address of the form someone@example.org",
    )  # type: ignore

    sender: bpy.props.StringProperty(
        name="Sender address",
        description="Valid email address of the form someone@example.org",
        update=reset_status,
    )  # type: ignore
    server: bpy.props.StringProperty(
        name="Email server",
        description="Fully qualified name of the SMTP server",
        default="smtp.example.com",
        update=reset_status,
    )  # type: ignore
    port: bpy.props.IntProperty(
        name="Server port",
        description="Port to use SMTP server (SSL is assumed)",
        default=465,
        min=1,
        max=65535,
        update=reset_status,
    )  # type: ignore
    # NOTE: this example has the SMTP password as a plain text string property.
    # This is for demonstration purposes only, and you should NOT use this in any real scenario!
    password: bpy.props.StringProperty(
        name="Password",
        update=reset_status,
    )  # type: ignore

    def draw(self, context):
        global connection_status

        # NOTE: unlike with operators there is no default draw implementation so if you don´t add it, you see nothing
        layout = self.layout

        recipient_row = layout.row()
        address_row = layout.row()
        password_row = layout.row()
        server_row = layout.row()

        recipient_row.alert = not is_valid_email_address(self.email)
        recipient_row.prop(self, "email", text="Recipient")

        address_row.alert = not is_valid_email_address(self.sender)
        address_row.prop(self, "sender", text="Sender")

        password_row.prop(self, "password", text="Password")

        server_row.prop(self, "server", text="Server")
        server_row.prop(self, "port", text="")

        status_col = layout.column()
        status_col.label(text=connection_status)
        status_col.operator(VerifyServer.bl_idname)
        status_col.operator(SendTestmail.bl_idname)


classes = (RenderDonePreferences, VerifyServer, SendTestmail)


def register():
    for klass in classes:
        register_class(klass)


def unregister():
    for klass in classes:
        unregister_class(klass)
