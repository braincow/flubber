from gi.repository import GLib, Gio, Gtk
from watson import Watson
from watson.utils import (
    sorted_groupby, format_timedelta,
    get_frame_from_argument)
import arrow
import operator
from functools import reduce
from flubber.dialogs import (
    FlubberAddFrameDialog, FlubberStartFrameDialog,
    FlubberEditFrameDialog)
from flubber.dialogs.util import (
    flubber_error_dialog, flubber_warning_dialog,
    flubber_info_dialog, flubber_confirm_dialog)
from flubber.util import beautify_tags


class FlubberAppWindow(Gtk.ApplicationWindow):

    welcome_enabled = False

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

        # button to delete frames
        self.del_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-delete")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.del_button.add(image)
        self.del_button.connect("clicked", self.on_del_button_clicked)
        self.hb.pack_end(self.del_button)

        # button to track project
        self.track_button = Gtk.Switch()
        # use button-press-event instead of notify::active so that
        #  state changes from elsewhere in code do not trigger this
        self.track_button.connect("button-press-event",
                                  self.on_track_switch_clicked)
        self.hb.pack_start(self.track_button)

        # Label to show tracking status
        self.track_status_label = Gtk.Label("Idle.")
        self.hb.pack_start(self.track_status_label)

        # assign grid to the window for element placement
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.add(self.grid)

        # Welcome message
        welcome_msg = ("No frames yet. You can "
                       "<a href='start'>start/stop tracking</a>"
                       " a project or <a href='add'>add a "
                       "existing</a> entry.")
        self.welcome_label = Gtk.Label()
        self.welcome_label.set_markup(welcome_msg)
        self.welcome_label.connect("activate-link", self.on_link_clicked)

        # the magic of the store is as follows:
        #  day (branch node) and project name (leaf) can share
        #  same first element
        self.store = Gtk.TreeStore(str, str, str, str, bool)

        # TreeView
        # the treeview shows the model
        # create a treeview on the model store
        self.view = Gtk.TreeView().new_with_model(self.store)

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

        # cellrender for project selection toggle
        rendered_select = Gtk.CellRendererToggle()
        column_select = Gtk.TreeViewColumn(
            "Select", rendered_select, active=4)
        rendered_select.connect("toggled", self.on_cell_toggled)
        self.view.append_column(column_select)

        # grab double click event on the list
        self.view.connect("row-activated", self.on_view_row_activated)

        # create scrollable window and place tree view inside it
        scrollable_treelist = Gtk.ScrolledWindow()
        scrollable_treelist.set_vexpand(True)
        self.grid.attach(scrollable_treelist, 0, 0, 8, 10)
        scrollable_treelist.add(self.view)

        # show all elements on this window
        self.show_all()

        # on first load show watson data
        self.reload_watson_data()

        # and start monitoring for changes in Watson state
        #  if user happens to change state through cmdline
        GLib.timeout_add(5000, self.sync_track_status)

    def on_link_clicked(self, label, uri):
        if uri == 'start':
            self.on_track_switch_clicked(self.track_button, None)
        elif uri == 'add':
            self.on_add_button_clicked(self.add_button)

    def on_del_button_clicked(self, button):
        # user wants to remove frames
        title = "Confirm frame remove"
        msg = "Do you really want to remove selected frame(s)?"
        response = flubber_confirm_dialog(self, title, msg)
        if response == Gtk.ResponseType.YES:
            # delete it from Watson db
            wat = Watson()
            # keep record of deleted frames
            deleted_frames = list()
            # go through the model and remove all selected frames
            for row in self.store:
                # get the iter associated with the path
                piter = self.store.get_iter(row.path)
                # get the iter associated with its first child
                citer = self.store.iter_children(piter)
                while citer is not None:
                    if self.store[citer][4]:
                        frame = get_frame_from_argument(wat,
                                                        self.store[citer][0])
                        del wat.frames[frame.id]
                        deleted_frames.append(frame.id)
                    citer = self.store.iter_next(citer)
            # save watson state and inform user
            if len(deleted_frames) > 0:
                try:
                    # save the state files
                    wat.save()
                except Exception as e:
                    # oh no, error while saving state files
                    msg = "Error while saving Watson state files"
                    flubber_error_dialog(self, msg, str(e))
                    # sync view with watson state
                    self.reload_watson_data()
                    # return here so that we dont process this
                    #  event any further
                    return

                flubber_info_dialog(self,
                                    "Frames deleted",
                                    "Frame(s) were deleted.")

                # update internal Watson state
                self.reload_watson_data()
            else:
                msg = "No frames selected or frame(s) were already removed."
                flubber_info_dialog(self,
                                    "No frames deleted",
                                    msg)

    def on_cell_toggled(self, widget, path):
        # the boolean value of the selected row
        current_value = self.store[path][4]
        # change the boolean value of the selected row in the model
        self.store[path][4] = not current_value
        # new current value!
        current_value = not current_value
        # if length of the path is 1 (that is, if we are selecting an day)
        if len(path) == 1:
            # get the iter associated with the path
            piter = self.store.get_iter(path)
            # get the iter associated with its first child
            citer = self.store.iter_children(piter)
            # while there are children, change the state of their boolean value
            # to the value of the day
            while citer is not None:
                self.store[citer][4] = current_value
                citer = self.store.iter_next(citer)
        # if the length of the path is not 1 (that is, if we are selecting a
        # project frame)
        elif len(path) != 1:
            # get the first child of the parent of the day (the first frame of
            # the day)
            citer = self.store.get_iter(path)
            piter = self.store.iter_parent(citer)
            citer = self.store.iter_children(piter)
            # check if all the children are selected
            all_selected = True
            while citer is not None:
                if self.store[citer][4] == False:
                    all_selected = False
                    break
                citer = self.store.iter_next(citer)
            # if they do, the day as well is selected; otherwise it is not
            self.store[piter][4] = all_selected

    def on_view_row_activated(self, treeview, treepath, column):
        # user double clicked a row on the tree
        # treepath always contains : if it is child of some day branch
        # (is there a more clean way to do this?)
        if ":" in str(treepath):
            model, treeiter = treeview.get_selection().get_selected()
            if treeiter is not None:
                wat = Watson()
                frame = get_frame_from_argument(wat, model[treeiter][0])
                # edit frame in a dialog
                dia = FlubberEditFrameDialog(self, frame)
                response = dia.run()
                if response == Gtk.ResponseType.OK:
                    # collect values from dialog
                    project = dia.project_combo.get_child().get_text()
                    selected_tags = list()
                    [selected_tags.append(row[0])
                        for row in dia.selected_tag_store]
                    start_date = dia.parsed_start_datetime
                    end_date = dia.parsed_end_datetime
                    # update frame and do watson save
                    wat.frames[frame.id] = (project,
                                            start_date,
                                            end_date,
                                            selected_tags)
                    message = "Edited project {}{}, from {} to {}.".format(
                                project,
                                beautify_tags(selected_tags),
                                start_date.humanize(),
                                end_date.humanize())
                    try:
                        # save the state files
                        wat.save()
                    except Exception as e:
                        dia.destroy()
                        # oh no, error while saving state files
                        msg = "Error while saving Watson state files"
                        flubber_error_dialog(self, msg, str(e))
                        # sync view with watson state
                        self.reload_watson_data()
                        # return here so that we dont process
                        #  this event any further
                        return

                    # show user info about the job just stopped
                    flubber_info_dialog(self, "Project frame edited", message)

                    # reload watson state
                    self.reload_watson_data()

                # in all other cases make sure the editor dialog
                #  is disposed properly
                dia.destroy()

    def on_track_switch_clicked(self, switch, gparam):
        wat = Watson()
        if switch.get_active():
            # we are stopping a running watson job
            if not wat.is_started:
                # for some reason Watson disagrees
                title = "No project started"
                msg = ("No project currently started. "
                       "Did you stop the project from command line instead?")
                flubber_warning_dialog(self, title, msg)
                # obviously our internal state is not in sync so sync it
                self.reload_watson_data()
                # return here so that main gui is again active
                return
            # stop the job
            frame = wat.stop()
            message = "Stopped project {}{}, started {}.".format(
                        frame.project,
                        beautify_tags(frame.tags),
                        frame.start.humanize())
            try:
                # save the state files
                wat.save()
            except Exception as e:
                # oh no, error while saving state files
                flubber_error_dialog(self,
                                     "Error while saving Watson state files",
                                     str(e))
                # sync view with watson state
                self.reload_watson_data()
                # return here so that we dont process this event any further
                return

            # show user info about the job just stopped
            flubber_info_dialog(self, "Project stopped", message)

            # update main view with watson state
            self.reload_watson_data()
        else:
            # we want to start a new watson run.
            # present dialog and verify data
            dia = FlubberStartFrameDialog(self)
            response = dia.run()
            if response == Gtk.ResponseType.OK:
                # read values from dialog
                project = dia.project_combo.get_child().get_text()
                selected_tags = list()
                [selected_tags.append(row[0])
                    for row in dia.selected_tag_store]
                # start new watson entry
                current = wat.start(project, selected_tags, restart=False)
                message = "Starting project {}{}, started {}.".format(
                            project,
                            beautify_tags(selected_tags),
                            current["start"].humanize())

                try:
                    # save the state files
                    wat.save()
                except Exception as e:
                    dia.destroy()
                    # oh no, error while saving state files
                    msg = "Error while saving Watson state files"
                    flubber_error_dialog(self, msg, str(e))
                    # sync view with watson state
                    self.reload_watson_data()

                    # return here so that we dont process
                    #  this event any further
                    return

                # show user info about the added job
                flubber_info_dialog(self, "Frame started", message)

                # and finally update watson active project status
                self.sync_track_status()

            # close dialog in all cases
            dia.destroy()

    def on_add_button_clicked(self, button):
        dia = FlubberAddFrameDialog(self)
        response = dia.run()

        if response == Gtk.ResponseType.OK:
            # fetch info from dialog
            project = dia.project_combo.get_child().get_text()
            start_date = dia.parsed_start_datetime
            end_date = dia.parsed_end_datetime
            selected_tags = list()
            [selected_tags.append(row[0])
                for row in dia.selected_tag_store]
            # save frame via watson, first validate values in the Add dialog
            wat = Watson()
            frame = wat.add(project=project,
                            tags=selected_tags,
                            from_date=start_date,
                            to_date=end_date)
            message = "Adding project {}{}, started {} and stopped {}.".format(
                        frame.project,
                        beautify_tags(frame.tags),
                        frame.start.humanize(),
                        frame.stop.humanize())
            try:
                # save the state files
                wat.save()
            except Exception as e:
                dia.destroy()
                # oh no, error while saving state files
                flubber_error_dialog(self,
                                     "Error while saving Watson state files",
                                     str(e))
                # sync view with watson state
                self.reload_watson_data()
                # return here so that we dont process this event any further
                return

            # show user info about the added job
            flubber_info_dialog(self, "Frame added", message)

            # and finally update watson status to main view
            self.reload_watson_data()

        # destroy dialog after we have read all
        #  the variables or if it was closed
        dia.destroy()

    def on_maximize_toggle(self, action, value):
        action.set_state(value)
        if value.get_boolean():
            self.maximize()
        else:
            self.unmaximize()
        # also refresh data while we are at it
        self.reload_watson_data()

    def on_reload_button_clicked(self, button):
        # update model
        self.reload_watson_data()

    def reload_watson_data(self):
        # as a test show frames from Watson
        wat = Watson()
        frames_by_day = sorted_groupby(wat.frames.filter(
            span=wat.frames.span(arrow.get("0"), arrow.now())),
            operator.attrgetter('day'), reverse=True
            )

        # clear the store for new appends
        self.store.clear()
        # loop through frames and populate the model
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
            piter = self.store.append(None,
                                      [day, None, daily_total, None, False])
            for frame in frames:
                tags = ', '.join(frame.tags)
                # here under branch (piter) we add a leaf
                #  see TreeStore definition above for field count
                # Watson uses in its TUI seven char length IDs; do the same
                clock_text = '{:HH:mm} to {:HH:mm} ({})'.format(
                                frame.start,
                                frame.stop,
                                format_timedelta(frame.stop - frame.start))
                self.store.append(piter,
                                  [frame.id[:7],
                                   frame.project,
                                   clock_text,
                                   tags,
                                   False])

        if len(self.store) > 0:
            if self.welcome_enabled:
                # hide welcome message
                self.remove(self.welcome_label)
                # show the main grid
                self.add(self.grid)
            # update treeview with the new model
            self.view.set_model(self.store)
            # enable delete button
            self.del_button.set_sensitive(True)
        else:
            # show welcome message and hide the main grid
            self.remove(self.grid)
            self.add(self.welcome_label)
            self.welcome_enabled = True
            # disable delete button
            self.del_button.set_sensitive(False)

        self.show_all()

        # sync track status too while we are at it
        self.sync_track_status()

    def sync_track_status(self):
        wat = Watson()
        # check if watson is running and
        #  change toggle button state based on that
        if wat.is_started:
            self.track_button.set_active(True)
            status_text = "{}{} {}".format(
                            wat.current["project"],
                            beautify_tags(wat.current["tags"]),
                            wat.current['start'].humanize())
            self.track_status_label.set_text(status_text)
        else:
            self.track_button.set_active(False)
            self.track_status_label.set_text("Idle.")

        # always return true to make
        #  GLib.timeout_add to reschedule
        return True
