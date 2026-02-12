# SPDX-FileCopyrightText: © 2026 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bl_ui.utils import PresetPanel
from bpy.types import Panel, Menu
from bl_operators.presets import AddPresetBase

from .utils import get_package_name, read_password,preview_collections
from .mail import is_valid_email_address
from .operators import ReadPasswordFromFile, VerifyServer

print(f"XXX {id(preview_collections)=}")

PRESET_SUBDIR = f"addons/{get_package_name()}"

def reset_status(self, context):
    """
    helper function to reset the connection_status variable.
    """
    bpy.context.window_manager.connection_status = "Connection: unknown"


class RENDERDONE_PT_presets(PresetPanel, Panel):
    bl_idname = "RENDERDONE_PT_presets"
    bl_label = "Presets"
    preset_subdir = PRESET_SUBDIR
    preset_operator = "script.execute_preset"
    preset_add_operator = "renderdone.add_preset"


class RENDERDONE_MT_presets(Menu):
    bl_idname = "RENDERDONE_MT_presets"
    bl_label = "Mailing presets"
    preset_subdir = PRESET_SUBDIR
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset  # TODO: investigate type warning

    @staticmethod
    def post_cb(context, filepath):
        assert bpy.context.preferences is not None
        bpy.context.preferences.addons[
            get_package_name()
        ].preferences.last_selected_preset = RENDERDONE_MT_presets.bl_label  # type:ignore (last_selected_preset is a known attribute)
        read_password()


class RenderDone_OT_AddMyPreset(AddPresetBase, bpy.types.Operator):  # type: ignore (base classes define execute methods differently; not something we can fix)
    bl_idname = "renderdone.add_preset"
    bl_label = "Add or remove a preset"
    preset_menu = "RENDERDONE_MT_presets"

    preset_defines = [
        f'prefs = bpy.context.preferences.addons["{get_package_name()}"].preferences',
    ]

    preset_values = [
        "prefs.server",
        "prefs.port",
        "prefs.email",
        "prefs.sender",
        "prefs.password_file",
    ]

    # Directory to store the presets
    preset_subdir = PRESET_SUBDIR


class RenderDonePreferences(bpy.types.AddonPreferences):
    bl_idname = get_package_name()  # important: this links these preferences with the current add-on; you still need to register the class though

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

    # see the draw() method below
    last_selected_preset: bpy.props.StringProperty(
        name="Last selected preset", update=reset_status, default="Mailing presets"
    )  # type: ignore

    def draw(self, context):

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
        # the same operator can also remove the current preset, but there isn´t a nice built-in icon for it so we provide it ourselves
        try:
            print(f"ICON {id(preview_collections)=}")
            print(f"{preview_collections.keys()=}")
            print(f"{preview_collections['operator_icons'].keys()=}")
            icon = preview_collections["operator_icons"]["preset_remove"]
            print(f"loaded {icon=}")
            panel_header.operator(
                RenderDone_OT_AddMyPreset.bl_idname, text="", icon_value=icon.icon_id
            ).remove_active = True
        except Exception as e:  # we provide a fallback but mainly for development purposes
            print(f"exception loading operator_icons preset_remove {type(e)}")
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
        status_col.label(text=bpy.context.window_manager.connection_status)
        status_col.operator(VerifyServer.bl_idname)
