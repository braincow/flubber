from gi.repository import GLib, Gio, Gtk
from watson import Watson
from watson.utils import sorted_groupby, format_timedelta
import arrow
import operator
from functools import reduce


class FlubberAppWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(800, 600)

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
        self.hb = Gtk.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.props.title = "Flubber"
        self.set_titlebar(self.hb)

        # button to refresh the interface
        self.reload_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="view-refresh")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.reload_button.add(image)
        self.reload_button.connect("clicked", self.on_reload_button_clicked)
        self.hb.pack_end(self.reload_button)

        # assign grid to the window for element placement
        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        self.add(grid)

        # TreeView
        # the treeview shows the model
        # create a treeview on the model store
        self.view = Gtk.TreeView()

        # the cellrenderer for the column - text
        renderer_days = Gtk.CellRendererText()
        # the column is created (note to self:
        #  text= actually indicates the list position
        #  from store.append(...))
        column_days = Gtk.TreeViewColumn(
            "Projects by day", renderer_days, text=0)
        # and it is appended to the treeview
        self.view.append_column(column_days)

        # cellrender for project/day length
        rendered_length = Gtk.CellRendererText()
        column_length = Gtk.TreeViewColumn(
            "Project / day length", rendered_length, text=1)
        self.view.append_column(column_length)

        # cellrender for project tags
        rendered_tags = Gtk.CellRendererText()
        column_tags = Gtk.TreeViewColumn(
            "Project tags", rendered_tags, text=2)
        self.view.append_column(column_tags)

        # cellrender for project start time
        rendered_start = Gtk.CellRendererText()
        column_start = Gtk.TreeViewColumn(
            "Project start time", rendered_start, text=3)
        self.view.append_column(column_start)

        # create scrollable window and place tree view inside it
        scrollable_treelist = Gtk.ScrolledWindow()
        scrollable_treelist.set_vexpand(True)
        grid.attach(scrollable_treelist, 0, 0, 8, 10)
        scrollable_treelist.add(self.view)

        # show all elements on this window
        self.show_all()

        # on first load show watson data
        self.reload_watson_data()

    def on_maximize_toggle(self, action, value):
        action.set_state(value)
        if value.get_boolean():
            self.maximize()
        else:
            self.unmaximize()

    def on_reload_button_clicked(self, button):
        self.reload_watson_data()

    def reload_watson_data(self):
        # as a test show frames from Watson
        wat = Watson()
        frames_by_day = sorted_groupby(wat.frames.filter(
            span=wat.frames.span(arrow.get("0"), arrow.now())),
            operator.attrgetter('day'), reverse=True
            )

        # the magic of the store is as follows:
        #  day (branch node) and project name (leaf) can share
        #  same first element
        self.store = Gtk.TreeStore(str, str, str, str)
        for i, (day, frames) in enumerate(frames_by_day):
            # convert itertools grouper object into list first
            #  https://stackoverflow.com/questions/44490079/how-to-turn-an-itertools-grouper-object-into-a-list#44490269
            frames = list(frames)
            day = "{:dddd DD MMMM YYYY}".format(day)
            daily_total = format_timedelta(reduce(
                operator.add,
                (frame.stop - frame.start for frame in frames)
            ))
            # piter refers to branch, use it to add leaf later (see below)
            #  all other entries are None, including top branch as we have none
            piter = self.store.append(None, [day, daily_total, None, None])
            for frame in frames:
                tags = ', '.join(frame.tags)
                # here under branch (piter) we add a leaf
                #  see TreeStore definition above for field count
                self.store.append(piter,
                                  [frame.project,
                                   format_timedelta(frame.stop - frame.start),
                                   tags,
                                   str(frame.start)])

        # update treeview with the new model
        self.view.set_model(self.store)
