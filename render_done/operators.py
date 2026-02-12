# SPDX-FileCopyrightText: © 2026 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy_extras.io_utils import ImportHelper

from .mail import verify_smtp_connection
from .utils import get_package_name, read_password


class ReadPasswordFromFile(bpy.types.Operator, ImportHelper):  # type: ignore (check() method defined differently in each base class; not something we can fix)
    """
    Lets the user select a file using the standard Blender file dialog
    and sets the password to the first line of this file.
    """

    bl_idname = "import.password"
    bl_label = "Read password"

    def execute(self, context):
        context.preferences.addons[
            get_package_name()
        ].preferences.password_file = self.filepath  # type: ignore (password_file is an attribute as is filepath)
        read_password()
        return {"FINISHED"}


class VerifyServer(bpy.types.Operator):
    bl_idname = "workspace.verify_server"
    bl_label = "Verify SMTP server"

    def execute(self, context):
        ok = verify_smtp_connection()
        if ok:
            self.report({"INFO"}, bpy.context.window_manager.connection_status)  # type: ignore
        else:
            self.report({"ERROR"}, bpy.context.window_manager.connection_status)  # type: ignore
        return {"FINISHED"}
