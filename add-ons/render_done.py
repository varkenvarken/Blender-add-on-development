# SPDX-FileCopyrightText: © 2026 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime
import re
from smtplib import SMTP_SSL, SMTPException
from email.message import EmailMessage

import bpy
from bpy.app.handlers import persistent
from bpy.utils import register_class, unregister_class
from bpy_extras.io_utils import ImportHelper
from bl_ui.utils import PresetPanel
from bpy.types import Panel, Menu
from bl_operators.presets import AddPresetBase

bl_info = {
    "name": "Mail when render is done",
    "author": "Michel Anders",
    "version": (0, 0, 1),
    "blender": (5, 0, 0),
    "location": "User preferences",
    "description": "Send a mail when rendering is done",
    "category": "Render",
}

# we do NOT store the password in a user preferences property because that would be persisted to disk
# in stead we keep a global variable that we initialize from a file, so when you close Blender
# it doesn´t linger around. This means we delegate password security to access management on the file system.
password = None


def read_password():
    global password
    password = read_first_line(
        bpy.context.preferences.addons[__name__].preferences.password_file
    )
    bpy.context.window_manager.password_loaded = password is not None


@persistent
def load_pre_handler(file: str):
    # gets called before loading a file
    if password is None:
        read_password()


status_lines = []


@persistent
def render_init_handler(scene: bpy.types.Scene):
    # gets called before a frame or before rendering an animation
    status_lines.clear()
    status_lines.append(
        f"Render init: Scene '{scene.name}' frames {scene.frame_start} - {scene.frame_end} (step {scene.frame_step}) started at {datetime.now()}"
    )


@persistent
def render_complete_handler(scene: bpy.types.Scene):
    global password
    # gets called after a frame or after rendering an animation
    lines = "\n".join(status_lines)
    send_smtp_message(
        f"Hello,\n\nthe render job for Scene '{scene.name}' was completed and reported the following:\n\n{lines}\n\nBye.\n"
    )


@persistent
def render_cancel_handler(scene: bpy.types.Scene):
    global password
    # gets called after a frame or animation was canceled
    lines = "\n".join(status_lines)
    send_smtp_message(
        f"Hello,\n\nthe render job for Scene '{scene.name}' was canceled and reported the following:\n\n{lines}\n\nBye.\n"
    )


@persistent
def render_stats_handler(stats: str):
    # gets called after every frame, but only when rendering an animation
    status_lines.append(stats)


def read_first_line(filepath: str) -> str | None:
    try:  # can fail for several reasons: file might not exist, or is not readable, etc.
        with open(filepath, "r", encoding="utf-8") as f:
            return f.readline().strip()
    except IOError:
        return None


# compile this only once so that the actual check can be quick
# note this email pattern might be overly restrictive,
# see: https://www.regular-expressions.info/email.html
valid_email_pattern = re.compile(
    r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE
)


def is_valid_email_address(email: str) -> bool:
    return valid_email_pattern.match(email) is not None


class ReadPasswordFromFile(bpy.types.Operator, ImportHelper):
    bl_idname = "import.password"
    bl_label = "Read password"

    def execute(self, context):
        context.preferences.addons[__name__].preferences.password_file = self.filepath
        read_password()
        return {"FINISHED"}


class VerifyServer(bpy.types.Operator):
    bl_idname = "workspace.verify_server"
    bl_label = "Verify SMTP server"

    def execute(self, context):
        if verify_smtp_connection():
            self.report({"INFO"}, "SMTP server connection ok")
        else:
            self.report({"ERROR"}, "SMTP server connection failed")
        return {"FINISHED"}


connection_status = "Connection: unknown"


def reset_status(self, context):
    global connection_status
    connection_status = "Connection: unknown"


# preset handling

PRESET_SUBDIR = f"addons/{__name__}"


class RenderDone_PT_presets(PresetPanel, Panel):
    bl_idname = "renderdone.panel_preset"
    bl_label = "Presets"
    preset_subdir = PRESET_SUBDIR
    preset_operator = "script.execute_preset"
    preset_add_operator = "renderdone.add_preset"


class RenderDone_MT_MyPresets(Menu):
    bl_idname = "RenderDone_MT_MyPresets"
    bl_label = "Presets"
    preset_subdir = PRESET_SUBDIR
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset


class RenderDone_OT_AddMyPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = "renderdone.add_preset"
    bl_label = "Add or remove a preset"
    preset_menu = "RenderDone_MT_MyPresets"

    # Common variable used for all preset values
    preset_defines = [
        f'prefs = bpy.context.preferences.addons["{__name__}"].preferences',
    ]

    # Properties to store in the preset
    preset_values = [
        "prefs.server",
        "prefs.port",
        "prefs.email",
        "prefs.sender",
        "prefs.password_file",
    ]

    # Directory to store the presets
    preset_subdir = PRESET_SUBDIR

    @staticmethod
    def pre_cb(context):
        reset_status(None, context)

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
    # don´t make these next two read only, otherwise we cannot even set them programmatically; make them read only in the draw method
    password_file: bpy.props.StringProperty(
        name="Password file",
        update=reset_status,
    )  # type: ignore
    password_loaded: bpy.props.BoolProperty(name="Password loaded", default=False)  # type: ignore

    def draw(self, context):
        global connection_status

        # note unlike with operators there is no default draw implementation so if you don´t add it, you see nothing
        layout = self.layout

        # embed the presets panel
        panel_header, panel_body = layout.panel(
            RenderDone_PT_presets.bl_idname, default_closed=False
        )
        panel_header.menu(RenderDone_MT_MyPresets.bl_idname)
        panel_header.operator(RenderDone_OT_AddMyPreset.bl_idname, text="", icon="PRESET_NEW")
        panel_header.operator(RenderDone_OT_AddMyPreset.bl_idname, text="", icon="X").remove_active = True

        recipient_row = layout.row()
        address_row = layout.row()
        password_row = layout.row()
        server_row = layout.row()
        status_row = layout.row()

        recipient_row.alert = not is_valid_email_address(self.email)
        recipient_row.prop(self, "email", text="Recipient")

        address_row.alert = not is_valid_email_address(self.sender)
        address_row.prop(self, "sender", text="Sender")

        box = password_row.row()
        box.prop(context.window_manager, "password_loaded", text="Password")
        box.enabled = False
        password_row.operator(ReadPasswordFromFile.bl_idname)
        password_row.operator(VerifyServer.bl_idname)

        server_row.prop(self, "server", text="Server")
        server_row.prop(self, "port", text="")
        status_row.label(text=connection_status)


def verify_smtp_connection():
    global password
    global connection_status

    if bpy.app.online_access or bpy.app.online_access_override:
        prefs = bpy.context.preferences.addons[__name__].preferences
        try:
            with SMTP_SSL(host=prefs.server, port=prefs.port) as smtp:
                smtp.login(user=prefs.sender, password=password)
                smtp.noop()
                connection_status = "Connection: ok"
            return True
        except Exception as e:  # not just smtp exceptions also socket.gaierror
            connection_status = "Connection: error"
            return False
    else:
        connection_status = "Connection: blocked by user (see prefs|system|network)"
        return False


def send_smtp_message(content: str):
    global password
    global connection_status
    prefs = bpy.context.preferences.addons[__name__].preferences

    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "Render job completed"
    msg["From"] = prefs.sender
    msg["To"] = prefs.email

    try:
        with SMTP_SSL(host=prefs.server, port=prefs.port) as smtp:
            smtp.login(user=prefs.sender, password=password)
            smtp.send_message(msg)
            smtp.quit()
            connection_status = "Connection: message sent"
        return True
    except (SMTPException, RuntimeError) as e:
        connection_status = "Connection: error"
        return False


classes = (
    RenderDone_PT_presets,
    RenderDone_MT_MyPresets,
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
    bpy.types.WindowManager.password_loaded = bpy.props.BoolProperty(
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


if __name__ == "__main__":
    register()
