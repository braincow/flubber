from gi.repository import GLib, Gio, Gtk
# from watson import Watson
# import arrow


class FlubberAppWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # This will be in the windows group and have the "win" prefix
        max_action = Gio.SimpleAction.new_stateful(
            "maximize", None, GLib.Variant.new_boolean(False))
        max_action.connect("change-state", self.on_maximize_toggle)
        self.add_action(max_action)

        # Keep it in sync with the actual state
        self.connect("notify::is-maximized",
                     lambda obj, pspec: max_action.set_state(
                        GLib.Variant.new_boolean(obj.props.is_maximized)))

        # create headerbar
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "Flubber"
        self.set_titlebar(hb)
        hb.show()

        # button = Gtk.Button()
        # icon = Gio.ThemedIcon(name="mail-send-receive-symbolic")
        # image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        # button.add(image)
        # hb.pack_end(button)
        # image.show()
        # button.show()

    def on_maximize_toggle(self, action, value):
        action.set_state(value)
        if value.get_boolean():
            self.maximize()
        else:
            self.unmaximize()
