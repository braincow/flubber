from gi.repository import Gtk

def flubber_dialog(parent, title, message, msgtype, btntype):
    dialog = Gtk.MessageDialog(parent, 0, msgtype,
        btntype, title)
    dialog.format_secondary_text(message)
    response = dialog.run()
    dialog.destroy()
    return response

def flubber_error_dialog(parent, title, message):
    # show an error message dialog
    flubber_dialog(parent, title, message,
                   Gtk.MessageType.ERROR,
                   Gtk.ButtonsType.CANCEL)

def flubber_warning_dialog(parent, title, message):
    # show an warning message dialog
    flubber_dialog(parent, title, message,
                   Gtk.MessageType.WARNING,
                   Gtk.ButtonsType.OK)

def flubber_info_dialog(parent, title, message):
    # show information message dialog
    flubber_dialog(parent, title, message,
                   Gtk.MessageType.INFO,
                   Gtk.ButtonsType.OK)

def flubber_confirm_dialog(parent, title, message):
    # show information message dialog
    return flubber_dialog(parent, title, message,
                   Gtk.MessageType.QUESTION,
                   Gtk.ButtonsType.YES_NO)
