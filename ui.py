#!/usr/bin/env python

from calibre.gui2.actions import InterfaceAction

class InterfacePlugin(InterfaceAction):
    name = 'ema_lang'
    action_spec = ('EMA Language Column', None, 'Configure EMA Language Column', None)

    def genesis(self):
        self.qaction.triggered.connect(self.show_dialog)

    def show_dialog(self):
        pass  # We don't need a dialog as we're just overriding the column creation
