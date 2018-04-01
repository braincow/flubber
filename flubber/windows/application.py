from gi.repository import GLib, Gio, Gtk
from watson import Watson
from watson.utils import sorted_groupby, format_timedelta, get_frame_from_argument
import arrow
import operator
from functools import reduce
from flubber.dialogs import FlubberAddFrameDialog
from flubber.dialogs.util import flubber_error_dialog, flubber_warning_dialog, flubber_info_dialog


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

        # button to add a frame
        self.add_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="document-new")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.add_button.add(image)
        self.add_button.connect("clicked", self.on_add_button_clicked)
        self.hb.pack_end(self.add_button)

        # button to track project
        self.track_button = Gtk.Switch()
        # use button-press-event instead of notify::active so that
        #  state changes from elsewhere in code do not trigger this
        self.track_button.connect("button-press-event", self.on_track_switch_clicked)
        self.hb.pack_start(self.track_button)

        # Label to show tracking status
        self.track_status_label = Gtk.Label("Idle.")
        self.hb.pack_start(self.track_status_label)

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
            "Frames by day", renderer_days, text=0)
        # and it is appended to the treeview
        self.view.append_column(column_days)

        # cellrender for project name
        rendered_project = Gtk.CellRendererText()
        column_project = Gtk.TreeViewColumn(
            "Project", rendered_project, text=1)
        self.view.append_column(column_project)

        # cellrender for project/day length
        rendered_length = Gtk.CellRendererText()
        column_length = Gtk.TreeViewColumn(
            "Project / day length", rendered_length, text=2)
        self.view.append_column(column_length)

        # cellrender for project tags
        rendered_tags = Gtk.CellRendererText()
        column_tags = Gtk.TreeViewColumn(
            "Project tags", rendered_tags, text=3)
        self.view.append_column(column_tags)

        # cellrender for project start time
        rendered_start = Gtk.CellRendererText()
        column_start = Gtk.TreeViewColumn(
            "Project start time", rendered_start, text=4)
        self.view.append_column(column_start)

        # grab double click event on the list
        self.view.connect("row-activated", self.on_view_row_activated)

        # create scrollable window and place tree view inside it
        scrollable_treelist = Gtk.ScrolledWindow()
        scrollable_treelist.set_vexpand(True)
        grid.attach(scrollable_treelist, 0, 0, 8, 10)
        scrollable_treelist.add(self.view)

        # show all elements on this window
        self.show_all()

        # on first load show watson data
        self.reload_watson_data()

    def on_view_row_activated(self, treeview, treepath, column):
        # user double clicked a row on the tree
        # treepath always contains : if it is child of some day branch
        # (is there a more clean way to do this?)
        if ":" in str(treepath):
            model, treeiter = treeview.get_selection().get_selected()
            if treeiter is not None:
                #wat = Watson()
                #frame = get_frame_from_argument(wat, model[treeiter][0])
                # TODO: edit frame in a dialog
                # TODO: or delete frame and verify command
                pass

    def on_track_switch_clicked(self, switch, gparam):
        wat = Watson()
        print(switch.get_active())
        if switch.get_active():
            # we are stopping a running watson job
            if not wat.is_started:
                # for some reason Watson disagrees
                flubber_warning_dialog(self,
                                       "No project started",
                                       "No project currently started. Did you stop the project from command line instead?")
                # obviously our internal state is not in sync so sync it
                self.reload_watson_data()
                # return here so that main gui is again active
                return
            # stop the job
            frame = wat.stop()
            message = "Stopped project {} {}, started {}.".format(
                                                                frame.project,
                                                                ', '.join(frame.tags),
                                                                frame.start.humanize())
            try:
                # save the state files
                wat.save()
            except Exception as e:
                # oh no, error while saving state files
                flubber_error_dialog(self,
                                     "Error while saving Watson state files",
                                     e)
                # return here so that we dont process this event any further
                return
                
            # show user info about the job just stopped
            flubber_info_dialog(self, "Project stopped", message)

            # and finally update watson status to main view
            self.reload_watson_data()

    def on_add_button_clicked(self, button):
        dia = FlubberAddFrameDialog(self)
        response = dia.run()

        if response == Gtk.ResponseType.OK:
            # fetch info from dialog
            project = dia.project_combo.get_child().get_text()
            start_date = dia.parsed_start_datetime
            end_date = dia.parsed_end_datetime
            selected_tags = list()
            [ selected_tags.append(row[0]) for row in dia.selected_tag_store ]
            # save frame via watson, first validate values in the Add dialog
            wat = Watson()
            frame = wat.add(project=project,
                               tags=selected_tags,
                               from_date=start_date,
                               to_date=end_date)
            message = "Adding project {}{}, started {} and stopped {}.".format(
                                                                               frame.project,
                                                                               ', '.join(selected_tags),
                                                                               frame.start.humanize(),
                                                                               frame.stop.humanize())
            try:
                # save the state files
                wat.save()
            except Exception as e:
                # oh no, error while saving state files
                flubber_error_dialog(self,
                                     "Error while saving Watson state files",
                                     e)
                # return here so that we dont process this event any further
                return

            # show user info about the job just stopped
            flubber_info_dialog(self, "Project stopped", message)

            # and finally update watson status to main view
            self.reload_watson_data()

        # destroy dialog after we have read all the variables or if it was closed
        dia.destroy()

    def on_maximize_toggle(self, action, value):
        action.set_state(value)
        if value.get_boolean():
            self.maximize()
        else:
            self.unmaximize()

    def on_reload_button_clicked(self, button):
        # update model
        self.reload_watson_data()

    def reload_watson_data(self):
        print("Reloading Watson state")
        # as a test show frames from Watson
        wat = Watson()
        frames_by_day = sorted_groupby(wat.frames.filter(
            span=wat.frames.span(arrow.get("0"), arrow.now())),
            operator.attrgetter('day'), reverse=True
            )

        # the magic of the store is as follows:
        #  day (branch node) and project name (leaf) can share
        #  same first element
        self.store = Gtk.TreeStore(str, str, str, str, str)
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
            piter = self.store.append(None, [day, None, daily_total, None, None])
            for frame in frames:
                tags = ', '.join(frame.tags)
                # here under branch (piter) we add a leaf
                #  see TreeStore definition above for field count
                # Watson uses in its TUI seven char length IDs; do the same
                self.store.append(piter,
                                  [frame.id[:7],
                                   frame.project,
                                   format_timedelta(frame.stop - frame.start),
                                   tags,
                                   str(frame.start)])

        # update treeview with the new model
        self.view.set_model(self.store)

        # check if watson is running and change toggle button state based on that
        if wat.is_started:
            self.track_button.set_active(True)
            status_text = "{} {} {}".format(
                                            wat.current["project"],
                                            ', '.join(wat.current["tags"]),
                                            wat.current['start'].humanize())
            self.track_status_label.set_text(status_text)
        else:
            self.track_button.set_active(False)
            self.track_status_label.set_text("Idle.")