import sys
import os
import signal
from gi.repository import GLib, Gio, Gtk
from flubber.windows import FlubberAppWindow


class FlubberApp(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="fi.iki.bcow.flubber",
                         **kwargs)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        builder = Gtk.Builder.new_from_file(
            os.path.join(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), "resources"), "menu.xml"))
        self.set_app_menu(builder.get_object("app-menu"))

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = FlubberAppWindow(application=self, title="Flubber")

        self.window.present()

    def on_quit(self, action, param):
        self.quit()


def main():
    app = FlubberApp()
    # bind SIGINT (CTRL+C) to app quit
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, app.quit)
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main)
