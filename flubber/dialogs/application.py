from gi.repository import Gtk

from watson import Watson

class WatsonAddDialog(Gtk.Dialog):

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Add", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(150, 100)

        wat = Watson()

        box = self.get_content_area()

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        box.add(grid)

        # Label and combobox for project selection
        project_label = Gtk.Label("Project")
        grid.add(project_label)
        project_store = Gtk.ListStore(str, str)
        for project in wat.projects:
            project_store.append([project, project])
        self.project_combo = Gtk.ComboBox.new_with_model_and_entry(project_store)
        self.project_combo.set_entry_text_column(1)
        grid.add(self.project_combo)

        # Add label for tag list
        # tag_label = Gtk.Label("Tags")
        # grid.add(tag_label)

        # show all elements on the dialog
        self.show_all()