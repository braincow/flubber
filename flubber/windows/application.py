from gi.repository import GLib, Gio, Gtk
from watson import Watson
from watson.utils import sorted_groupby
import arrow
import operator


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

        # button to refresh the interface
        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="view-refresh")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        hb.pack_end(button)

        # as a test show frames from Watson
        wat = Watson()
        frames_by_day = sorted_groupby(wat.frames.filter(
            span = wat.frames.span(arrow.get("0"), arrow.now())),
            operator.attrgetter('day'), reverse=True
            )

        store = Gtk.ListStore(str,str,str,str,str)

        for i, (day, frames) in enumerate(frames_by_day):
            for frame in frames:
                #print("{} {}".format(day, frame))
                day = str(day)
                start = str(frame.start)
                stop = str(frame.stop)
                project = frame.project
                tags = '+{}'.format(' +'.join(frame.tags))
                store.append((day,start,stop,project,tags))

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        self.add(grid)

        treeview = Gtk.TreeView.new_with_model(store)
        for i, column_title in enumerate(["Day", "Start time", "End time", "Project", "Tags"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            treeview.append_column(column)
        scrollable_treelist = Gtk.ScrolledWindow()
        scrollable_treelist.set_vexpand(True)
        grid.attach(scrollable_treelist, 0, 0, 8, 10)
        scrollable_treelist.add(treeview)
        self.show_all()

    def on_maximize_toggle(self, action, value):
        action.set_state(value)
        if value.get_boolean():
            self.maximize()
        else:
            self.unmaximize()
