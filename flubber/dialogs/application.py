from gi.repository import Gtk, Gio

from watson import Watson

class FlubberFrameDialog(Gtk.Dialog):

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Add", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))

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
        self.project_combo = Gtk.ComboBox.new_with_model_and_entry(project_store)
        self.project_combo.set_entry_text_column(1)
        grid.attach_next_to(self.project_combo, project_label, Gtk.PositionType.RIGHT, 1, 1)
        # Add label and entry field for start date input
        start_label = Gtk.Label("Start date")
        grid.attach_next_to(start_label, project_label, Gtk.PositionType.BOTTOM, 1, 1)
        self.start_entry = Gtk.Entry()
        grid.attach_next_to(self.start_entry, start_label, Gtk.PositionType.RIGHT, 1, 1)
        # add label and entry field for end date input
        end_label = Gtk.Label("End date")
        grid.attach_next_to(end_label, start_label, Gtk.PositionType.BOTTOM, 1, 1)
        self.end_entry = Gtk.Entry()
        grid.attach_next_to(self.end_entry, end_label, Gtk.PositionType.RIGHT, 1, 1)

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
        self.tag_combo = Gtk.ComboBox.new_with_model_and_entry(existing_tag_store)
        self.tag_combo.set_entry_text_column(1)
        grid2.add(self.tag_combo)
        # interface button to add items to list
        add_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="list-add")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        add_button.add(image)
        grid2.attach_next_to(add_button, self.tag_combo, Gtk.PositionType.RIGHT, 1, 1)
        # action method for add button
        add_button.connect("clicked", self.on_add_clicked)
        # ro listbox to show added elements
        self.selected_tag_store = Gtk.ListStore(str, str)
        self.tag_view = Gtk.TreeView(model=self.selected_tag_store)
        col = Gtk.TreeViewColumn("Tag", Gtk.CellRendererText(), text=1)
        self.tag_view.append_column(col)
        # create a scrollable viewport to prevent dialog borders from expanding
        scrollable_treelist = Gtk.ScrolledWindow()
        scrollable_treelist.set_vexpand(True)
        scrollable_treelist.add(self.tag_view)
        grid2.attach_next_to(scrollable_treelist, self.tag_combo, Gtk.PositionType.BOTTOM, 1, 3)
        # interface button to delete selected item from list
        self.del_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="list-remove")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.del_button.add(image)
        grid2.attach_next_to(self.del_button, scrollable_treelist, Gtk.PositionType.RIGHT, 1, 1)
        # action method for del button
        self.del_button.connect("clicked", self.on_del_clicked)
        # by default delete button is disabled
        self.del_button.set_sensitive(False)

        # show all elements on the dialog
        self.show_all()

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
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.CANCEL, "Selected tag is empty")
            dialog.format_secondary_text(
                "Adding a empty tag is not allowed.")
            dialog.run()
            dialog.destroy()
            # return here so that we dont process the empty entry
            return

        # check that selected_tag is not already in the list
        for key, value in self.selected_tag_store:
            if key == selected_tag:
                dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.CANCEL, "Selected tag is already added")
                dialog.format_secondary_text(
                    "Adding a duplicate tag '{}' is not allowed.".format(value))
                dialog.run()
                dialog.destroy()
                # return here so that we dont process the dumplicate entry
                return

        # checks concluded, add the tag to selection list
        self.selected_tag_store.append([selected_tag, selected_tag])

        # enable del button
        self.del_button.set_sensitive(True)

        # clear selection from combobox to prepare it for next input
        self.tag_combo.get_child().set_text("")