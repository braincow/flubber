from gi.repository import Gtk, Gio
from watson import Watson
from flubber.dialogs.util import flubber_error_dialog
from flubber.util import arrow_parse_datetime
from arrow.parser import ParserError

date_format = 'YYYY-MM-DD'
time_format = 'HH:mm:ss'
datetime_format = '{} {}'.format(date_format, time_format)


class FlubberEditFrameDialog(Gtk.Dialog):

    # these booleans all need to switch to True state for OK button to release
    project_validated = False
    start_date_validated = False
    end_date_validated = False

    # these fields contain the parsed datetime object
    parsed_start_datetime = None
    parsed_end_datetime = None

    def __init__(self, parent, watson_frame):
        Gtk.Dialog.__init__(self, "Edit frame", parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        # store the watson frame to self for manipulation
        self.watson_frame = watson_frame

        # init Watson to read in existing projects and tags from it
        wat = Watson()

        # set default size and border to 10 pixels
        self.set_default_size(150, 100)
        self.set_border_width(10)

        # in gtk dialog all content needs to go inside "the box"
        box = self.get_content_area()

        # notebook interface for users convinience
        notebook = Gtk.Notebook()
        box.add(notebook)

        # page1 of notebook contains project settings
        page1 = Gtk.Box()
        page1.set_border_width(10)
        notebook.append_page(page1, Gtk.Label('Project'))

        # we place grid interface to page1
        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        page1.add(grid)

        # Label and combobox for project selection
        project_label = Gtk.Label("Project")
        grid.add(project_label)
        project_store = Gtk.ListStore(str, str)
        for project in wat.projects:
            project_store.append([project, project])
        self.project_combo = Gtk.ComboBox(has_entry=True)
        self.project_combo.set_model(project_store)
        self.project_combo.set_entry_text_column(1)
        # prepopulate the combobox text field with frames project
        self.project_combo.get_child().set_text(self.watson_frame.project)
        self.on_project_combo_changed(self.project_combo)
        self.project_combo.connect("changed", self.on_project_combo_changed)
        # also add completion to the entry text field inside the combobox
        project_completion = Gtk.EntryCompletion()
        project_completion.set_model(project_store)
        project_completion.set_text_column(0)
        self.project_combo.get_child().set_completion(project_completion)
        # add combobox to grid
        grid.attach_next_to(self.project_combo, project_label,
                            Gtk.PositionType.RIGHT, 1, 1)
        # Add label and entry field for start date input
        start_label = Gtk.Label("Start date and time")
        grid.attach_next_to(start_label, project_label,
                            Gtk.PositionType.BOTTOM, 1, 1)
        self.start_entry = Gtk.Entry()
        # prepopulate date text field with frames start time
        start_pre = self.watson_frame.start.format(datetime_format)
        self.start_entry.set_text(start_pre)
        self.on_start_entry_changed(self.start_entry)
        self.start_entry.connect("changed", self.on_start_entry_changed)
        grid.attach_next_to(self.start_entry, start_label,
                            Gtk.PositionType.RIGHT, 1, 1)
        # add label and entry field for end date input
        end_label = Gtk.Label("End date and time")
        grid.attach_next_to(end_label, start_label,
                            Gtk.PositionType.BOTTOM, 1, 1)
        self.end_entry = Gtk.Entry()
        # prepopulate date text field with frames stop time
        end_pre = self.watson_frame.stop.format(datetime_format)
        self.end_entry.set_text(end_pre)
        self.on_end_entry_changed(self.end_entry)
        self.end_entry.connect("changed", self.on_end_entry_changed)
        grid.attach_next_to(self.end_entry, end_label,
                            Gtk.PositionType.RIGHT, 1, 1)

        # page2 of notebook interface is for tag input
        page2 = Gtk.Box()
        page2.set_border_width(10)
        notebook.append_page(page2, Gtk.Label('Tags'))

        # add grid layout to page2
        grid2 = Gtk.Grid()
        grid2.set_column_homogeneous(True)
        grid2.set_row_homogeneous(True)
        page2.add(grid2)

        # editable combobox to add existing/new tags to listbox
        existing_tag_store = Gtk.ListStore(str, str)
        for tag in wat.tags:
            existing_tag_store.append([tag, tag])
        self.tag_combo = Gtk.ComboBox(has_entry=True)
        self.tag_combo.set_model(existing_tag_store)
        self.tag_combo.set_entry_text_column(1)
        # also add completion to the entry text field inside the combobox
        tag_completion = Gtk.EntryCompletion()
        tag_completion.set_model(existing_tag_store)
        tag_completion.set_text_column(0)
        self.tag_combo.get_child().set_completion(tag_completion)
        # add combobox to grid
        grid2.add(self.tag_combo)
        # interface button to add items to list
        add_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="list-add")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        add_button.add(image)
        grid2.attach_next_to(add_button, self.tag_combo,
                             Gtk.PositionType.RIGHT, 1, 1)
        # action method for add button
        add_button.connect("clicked", self.on_add_clicked)
        # ro listbox to show added elements
        self.selected_tag_store = Gtk.ListStore(str, str)
        # prepopulate the tag store with frames tags
        for tag in self.watson_frame.tags:
            self.selected_tag_store.append([tag, tag])
        self.tag_view = Gtk.TreeView(model=self.selected_tag_store)
        col = Gtk.TreeViewColumn("Tag", Gtk.CellRendererText(), text=1)
        self.tag_view.append_column(col)
        # create a scrollable viewport to prevent dialog borders from expanding
        scrollable_treelist = Gtk.ScrolledWindow()
        scrollable_treelist.set_vexpand(True)
        scrollable_treelist.add(self.tag_view)
        grid2.attach_next_to(scrollable_treelist, self.tag_combo,
                             Gtk.PositionType.BOTTOM, 1, 3)
        # interface button to delete selected item from list
        self.del_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="list-remove")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.del_button.add(image)
        grid2.attach_next_to(self.del_button, scrollable_treelist,
                             Gtk.PositionType.RIGHT, 1, 1)
        # action method for del button
        self.del_button.connect("clicked", self.on_del_clicked)
        # delete button is disabled if list is empty
        if len(self.selected_tag_store) == 0:
            self.del_button.set_sensitive(False)

        # show all elements on the dialog
        self.show_all()

    def self_validate(self):
        if False in [self.project_validated,
                     self.start_date_validated,
                     self.end_date_validated]:
            # by default the OK button is grayed out until all fields report OK
            # does not count the tags as that can be empty too
            self.set_response_sensitive(Gtk.ResponseType.OK, False)
        else:
            self.set_response_sensitive(Gtk.ResponseType.OK, True)

    def on_start_entry_changed(self, entry):
        try:
            # try to parse the input field contents with arrow
            self.parsed_start_datetime = arrow_parse_datetime(entry.get_text())
            self.start_date_validated = True
        except ParserError:
            self.start_date_validated = False
        finally:
            # test toggle of OK button
            self.self_validate()

    def on_end_entry_changed(self, entry):
        try:
            # try to parse the input field contents with arrow
            self.parsed_end_datetime = arrow_parse_datetime(entry.get_text())
            self.end_date_validated = True
            # check that end date comes after start time
            if self.parsed_end_datetime < self.parsed_start_datetime:
                raise ValueError("Start time has to occur before end time.")
        except ValueError:
            self.end_date_validated = False
        except ParserError:
            self.end_date_validated = False
        finally:
            # test toggle of OK button
            self.self_validate()

    def on_project_combo_changed(self, combo):
        # toggle validation for project name field
        text = combo.get_child().get_text()
        if text == "":
            self.project_validated = False
        else:
            self.project_validated = True
        # test toggle of OK button
        self.self_validate()

    def on_del_clicked(self, button):
        # user wants to remove selected entry from list
        selection = self.tag_view.get_selection()
        model, paths = selection.get_selected_rows()
        for path in paths:
            it = model.get_iter(path)
            model.remove(it)

        # if last entry was removed from view disable button
        if len(model) == 0:
            self.del_button.set_sensitive(False)

    def on_add_clicked(self, button):
        # user wanted to add text formatted tag from combobox to list
        # check that it is not empty
        selected_tag = self.tag_combo.get_child().get_text()
        if selected_tag is None or selected_tag == '' or selected_tag is '':
            flubber_error_dialog(self, "Selected tag is empty",
                                 "Adding a empty tag is not allowed.")
            # return here so that we dont process the empty entry
            return

        # check that selected_tag is not already in the list
        for key, value in self.selected_tag_store:
            if key == selected_tag:
                msg = ("Adding a duplicate tag '{}' "
                       "is not allowed".format(value))
                flubber_error_dialog(self, "Adding a duplicate tag", msg)
                # return here so that we dont process the dumplicate entry
                return

        # checks concluded, add the tag to selection list
        self.selected_tag_store.append([selected_tag, selected_tag])

        # enable del button
        self.del_button.set_sensitive(True)

        # clear selection from combobox to prepare it for next input
        self.tag_combo.get_child().set_text("")
