# SPDX-FileCopyrightText: © 2026 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime
import re
from smtplib import SMTP_SSL, SMTPException
from email.message import EmailMessage
from typing import Literal

import bpy
from bpy.app.handlers import persistent
from bpy.utils import register_class, unregister_class
from bpy_extras.io_utils import ImportHelper
from bl_ui.utils import PresetPanel
from bpy.types import Context, Panel, Menu
from bl_operators.presets import AddPresetBase

# to prevent having to annotate the return type of every execute method with this rather unreadable chunk
EXECUTE_RETURN = set[
    Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]
]


bl_info = {
    "name": "Mail when render is done",
    "author": "Michel Anders",
    "version": (0, 0, 1),
    "blender": (5, 0, 0),
    "location": "User preferences",
    "description": "Send a mail when rendering is done",
    "category": "Render",
}

# NOTE: it would make more sense from a code maintenance point of view
# to move the password and email code each to its own module, but
# to keep things simple from a didactical point of view I decided to
# keep this all in one file. Later in the series on Blender add-on development
# we might tackle how to work with multi file add-on (Python packages).
# For now we do add region/endregion pairs to allow us to at least
# visually separate things a bit (if you IDE support this)

# region password

# we do NOT store the password in a user preferences property because that would be persisted to disk
# instead we keep a global variable that we initialize from a file, so when you close Blender
# it doesn´t linger around. This means we delegate password security to access management on the file system.
password: str | None = None


def read_password():
    """Read password from file and update global password variable.

    Reads the first line of the password file specified in addon preferences,
    stores it in the global password variable, and sets a custom property in the window
    manager to indicate whether the password was successfully loaded.
    """
    global password
    assert bpy.context.preferences is not None  # keep Pylance happy
    password = read_first_line(
        bpy.context.preferences.addons[__name__].preferences.password_file  # type: ignore (password_file is an attribute)
    )
    bpy.context.window_manager.password_loaded = password is not None  # type: ignore (password_loaded is an attribute)


def read_first_line(filepath: str) -> str | None:
    """Read and return the first line from a file.

    Args:
        filepath: Path to the file to read.

    Returns:
        The first line of the file with leading/trailing whitespace stripped,
        or None if the file cannot be read (e.g., missing or not readable).
    """
    try:  # can fail for several reasons: file might not exist, or is not readable, etc.
        with open(filepath, "r", encoding="utf-8") as f:
            return f.readline().strip()
    except IOError:
        return None


class ReadPasswordFromFile(bpy.types.Operator, ImportHelper):  # type: ignore (check() method defined differently in each base class; not something we can fix)
    """
    Lets the user select a file using the standard Blender file dialog
    and sets the password to the first line of this file.
    """

    bl_idname = "import.password"
    bl_label = "Read password"

    def execute(self, context: Context) -> EXECUTE_RETURN:
        assert context.preferences is not None  # keep Pylance happy
        context.preferences.addons[__name__].preferences.password_file = self.filepath  # type: ignore (password_file is an attribute as is filepath)
        read_password()
        return {"FINISHED"}


# endregion


# region app handlers


# a whole collection of app handlers
# the first one might be a bit superfluous as it tries to read the password on every .blend file being opened.
# we keep it for now.
@persistent
def load_pre_handler(file: str):
    # gets called before loading a file
    if password is None:
        read_password()


# the next handlers are all relevanr to rendering
# the render int, complete, and cancel ones will be called
# at most once for any render job (where a job can be a still render or an animation)
# but the stats handler will be called for every frame rendered.
# because we want to preserve those statuses we keep a record of them in the
# status_lines variable, and send all of them as the context of a message
# at the end of a job.
# status_lines get reset at the start of a job.
status_lines = []


@persistent
def render_init_handler(scene: bpy.types.Scene):
    # gets called before a render job
    status_lines.clear()
    status_lines.append(
        f"Render init: Scene '{scene.name}' frames {scene.frame_start} - {scene.frame_end} (step {scene.frame_step}) started at {datetime.now()}"
    )


@persistent
def render_complete_handler(scene: bpy.types.Scene):
    global password
    # gets called after a render job completed successfully
    lines = "\n".join(status_lines)
    send_smtp_message(
        f"Hello,\n\nthe render job for Scene '{scene.name}' was completed and reported the following:\n\n{lines}\n\nBye.\n"
    )


@persistent
def render_cancel_handler(scene: bpy.types.Scene):
    global password
    # gets called after a render job was canceled
    lines = "\n".join(status_lines)
    send_smtp_message(
        f"Hello,\n\nthe render job for Scene '{scene.name}' was canceled and reported the following:\n\n{lines}\n\nBye.\n"
    )


@persistent
def render_stats_handler(stats: str):
    # gets called after every frame, but only when rendering an animation
    status_lines.append(stats)


# endregion

# region email

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


def verify_smtp_connection() -> bool:
    """Test the SMTP connection with current addon preferences.

    Attempts to establish an SMTP_SSL connection using the configured server,
    port, sender email, and password. Updates the global connection_status
    variable with the result.

    Returns:
        True if the connection and login were successful, False otherwise.
        Also returns False if online access is blocked by user settings.
    """
    global password
    global connection_status

    if bpy.app.online_access:  # or bpy.app.online_access_override  not needed, override indicates when overridden, that'all
        assert bpy.context.preferences is not None  # keep Pylance happy
        prefs: RenderDonePreferences = bpy.context.preferences.addons[
            __name__
        ].preferences  # type: ignore
        try:
            with SMTP_SSL(host=prefs.server, port=prefs.port) as smtp:
                smtp.login(user=prefs.sender, password=password)  # type: ignore (if password is None login will fail which is perfectly ok)
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
    global password
    global connection_status

    assert bpy.context.preferences is not None  # keep Pylance happy
    prefs: RenderDonePreferences = bpy.context.preferences.addons[__name__].preferences  # type: ignore

    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "Render job completed"
    msg["From"] = prefs.sender
    msg["To"] = prefs.email

    try:
        if bpy.app.online_access:
            with SMTP_SSL(host=prefs.server, port=prefs.port) as smtp:
                smtp.login(user=prefs.sender, password=password)  # type: ignore (if password is None login will fail which is perfectly ok)
                smtp.send_message(msg)
                smtp.quit()
                connection_status = "Connection: message sent"
            return True
        else:
            connection_status = "Connection: blocked by user (see prefs|system|network)"
            return False
    except (SMTPException, RuntimeError) as e:
        connection_status = f"Connection: error {str(e)}"
        return False


class VerifyServer(bpy.types.Operator):
    bl_idname = "workspace.verify_server"
    bl_label = "Verify SMTP server"

    def execute(self, context: Context) -> EXECUTE_RETURN:
        if verify_smtp_connection():
            self.report({"INFO"}, "SMTP server connection ok")
        else:
            self.report({"ERROR"}, "SMTP server connection failed")
        return {"FINISHED"}


connection_status = "Connection: unknown"


def reset_status(self, context):
    """
    helper function to reset the connection_status variable.
    """
    global connection_status
    connection_status = "Connection: unknown"


# endregion

# region preset handling

# The would typically be  ~/.config/blender/5.0/scripts/presets/addons/render_done
# (or its Windows or Mac equivalent).
PRESET_SUBDIR = f"addons/{__name__}"

# presets are not too complicated if you just want to provide operator presets,
# or have a simple panel somewhere, but here we want to save user preference
# properties and sometimes have the last preset choice reflected in the UI
# that is simple for the previous cases, but here we have to fiddle around a bit
# and it isn´t very pretty ...

# NOTE: this horrible looking class name is needed because not following this
# convention will result in warnings on the console. (And why do I think this is horrible?
# Well, the _PT_ idea clearly identifies it as a Panel type, but the ALL_CAPS prefix is
# just plain ugly imho)


# this panel will be embedded in our preferences
# it doesn't contain any layour for the header or body,
# that is something that will be filled in by the draw()
# method of the preferences
class RENDERDONE_PT_presets(PresetPanel, Panel):
    bl_idname = "RENDERDONE_PT_presets"
    bl_label = "Presets"
    preset_subdir = PRESET_SUBDIR
    preset_operator = "script.execute_preset"
    preset_add_operator = "renderdone.add_preset"


# NOTE: my remarks about name conventions for panels hold for menus too...


# this menu will be shown in the panel header we will draw as part of
# the preferences.
class RENDERDONE_MT_presets(Menu):
    bl_idname = "RENDERDONE_MT_presets"
    bl_label = "Mailing presets"
    preset_subdir = PRESET_SUBDIR
    preset_operator = "script.execute_preset"  # refers to the built-in operator that will load the chosen preset
    draw = Menu.draw_preset  # TODO: investigate type warning

    # this is undocumented, but it works. If this static method is present
    # it will be called after the preset is selected and executed, which
    # we use to record the name of the preset and to read the password
    # (from the filename that is one of the saved properties)
    @staticmethod
    def post_cb(context, filepath):
        assert bpy.context.preferences is not None
        bpy.context.preferences.addons[
            __name__
        ].preferences.last_selected_preset = RENDERDONE_MT_presets.bl_label  # type:ignore (last_selected_preset is a known attribute)
        read_password()


# NOTE: operator naming conventions are less strict and will not result in a warning whatever you call it


# this operator is responsible for creating a new preset.
# all the hard work is already implemented in the AddPresetBase mixin (which must be first in the base classes)
# all we have to do is define which properties to save and where to find those
class RenderDone_OT_AddMyPreset(AddPresetBase, bpy.types.Operator):  # type: ignore (base classes define execute methods differently; not something we can fix)
    bl_idname = "renderdone.add_preset"
    bl_label = "Add or remove a preset"
    preset_menu = "RENDERDONE_MT_presets"

    # Common variable used for all preset values
    # we only refer to our addon preferences here
    # note that we interpolate the __name__ here and put it between quotes
    # because when this will be executed __name__ might not actually be known (I think)
    preset_defines = [
        f'prefs = bpy.context.preferences.addons["{__name__}"].preferences',
    ]

    # Properties to store in the preset (everything exacpt the password, which isn´t a property anyway)
    preset_values = [
        "prefs.server",
        "prefs.port",
        "prefs.email",
        "prefs.sender",
        "prefs.password_file",
    ]

    # Directory to store the presets
    preset_subdir = PRESET_SUBDIR

    # undocumented, but when this method is defined, it will called before creating a new preset
    # we don´t need it however, because creating a new preset doesn´t change anything about the connection status
    # @staticmethod
    # def pre_cb(context):
    #     reset_status(None, context)


# endregion

# region preferences


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
    # don´t make these next two read only, otherwise we cannot even set them programmatically;
    # make them read only in the draw method (or don´t even show them)
    password_file: bpy.props.StringProperty(
        name="Password file",
        update=reset_status,
    )  # type: ignore
    password_loaded: bpy.props.BoolProperty(name="Password loaded", default=False)  # type: ignore

    # see the draw() method below
    last_selected_preset: bpy.props.StringProperty(
        name="Last selected preset", update=reset_status, default="Maling presets"
    )  # type: ignore

    def draw(self, context):
        global connection_status

        # NOTE: unlike with operators there is no default draw implementation so if you don´t add it, you see nothing
        layout = self.layout

        # embed the presets panel
        # panel_header will be a UILayout that will be empty
        # panel_body will be an empty UILayout or even None when the panel is closed
        panel_header, panel_body = layout.panel(
            RENDERDONE_PT_presets.bl_idname, default_closed=True
        )

        # normally the menu is supposed to show the last selected preset, but for some reason it doesn´t when we use it here
        # therefore out Menu has a callback that sets the last_selected_preset property, that we use here to set the text.
        # bit convoluted but it seems to work.
        panel_header.menu(
            RENDERDONE_MT_presets.bl_idname, text=self.last_selected_preset
        )
        # We present to operator to add a new prefix as a small button with a built-in icon
        panel_header.operator(
            RenderDone_OT_AddMyPreset.bl_idname, text="", icon="PRESET_NEW"
        )
        # the same operator can also remove the current preset, but there isn´t a nice built-in icon for it so we use a plain X
        panel_header.operator(
            RenderDone_OT_AddMyPreset.bl_idname, text="", icon="X"
        ).remove_active = True

        # if the panel body is shown, we add the properties we want the use to see
        # (that's all of them except the name of the password file)
        if panel_body:
            recipient_row = panel_body.row()
            address_row = panel_body.row()
            password_row = panel_body.row()
            server_row = panel_body.row()

            recipient_row.alert = not is_valid_email_address(self.email)
            recipient_row.prop(self, "email", text="Recipient")

            address_row.alert = not is_valid_email_address(self.sender)
            address_row.prop(self, "sender", text="Sender")

            # the checkbox that indicates if the password was loaded is only set programmatically
            # so here we show it disabled.
            row2 = password_row.row()
            row2.prop(context.window_manager, "password_loaded", text="Password")
            row2.enabled = False
            password_row.operator(ReadPasswordFromFile.bl_idname)

            server_row.prop(self, "server", text="Server")
            server_row.prop(self, "port", text="")

        # The connection status is always shown, regardless whether we see the properties or not
        status_col = layout.column()
        status_col.label(text=connection_status)
        status_col.operator(VerifyServer.bl_idname)


# endregion

# region addon management


classes = (
    RENDERDONE_PT_presets,
    RENDERDONE_MT_presets,
    RenderDone_OT_AddMyPreset,
    RenderDonePreferences,
    ReadPasswordFromFile,
    VerifyServer,
)


def register():
    bpy.app.handlers.render_init.append(render_init_handler)
    bpy.app.handlers.render_complete.append(render_complete_handler)
    bpy.app.handlers.render_stats.append(render_stats_handler)
    bpy.app.handlers.load_pre.append(load_pre_handler)
    # registering will not load the user preferences yet apparently
    for klass in classes:
        register_class(klass)
    bpy.types.WindowManager.password_loaded = bpy.props.BoolProperty(  # type: ignore (we can define a new attribute dynamically no problem)
        name="Password loaded", default=False
    )
    read_password()
    verify_smtp_connection()


def unregister():
    bpy.app.handlers.render_init.remove(render_init_handler)
    bpy.app.handlers.render_complete.remove(render_complete_handler)
    bpy.app.handlers.render_stats.remove(render_stats_handler)
    bpy.app.handlers.load_pre.remove(load_pre_handler)
    for klass in classes:
        unregister_class(klass)


# endregion

if __name__ == "__main__":
    register()
