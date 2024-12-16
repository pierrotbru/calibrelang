#!/usr/bin/env python

__license__ = 'GPL v3'
__copyright__ = '2024, laverdure'
__docformat__ = 'restructuredtext en'

import os
import sys
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_file_location
from calibre.customize import InterfaceActionBase

class EmaLangPlugin(InterfaceActionBase):
    name = 'ema_lang'
    description = 'Override CreateCustomColumn and metadata widgets with custom EMA language implementation'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'laverdure'
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)
    actual_plugin = 'calibre_plugins.ema_lang.ui:InterfacePlugin'

    def initialize(self):
        try:
            # Import using relative import for custom column
            from .create_custom_column import ECCC
            from calibre.gui2.preferences.create_custom_column import CreateCustomColumn

            # Replace the CreateCustomColumn class in the module
            module = sys.modules['calibre.gui2.preferences.create_custom_column']
            original_class = module.CreateCustomColumn
            module.CreateCustomColumn = ECCC
            print(f"Successfully replaced CreateCustomColumn with ECCC")

            # Import Lang and BulkLang from custom_column_widgets
            from calibre.gui2.custom_column_widgets import populate_metadata_page   
            from .custom_column_widgets import Lang, BulkLang

            # Replace the widgets and bulk_widgets dictionaries
            custom_column_module = sys.modules['calibre.gui2.custom_column_widgets']

            if 'widgets' in custom_column_module.__dict__:
                custom_column_module.widgets['lang'] = Lang
                print(f"Successfully added Lang to widgets dictionary")

            if 'bulk_widgets' in custom_column_module.__dict__:
                custom_column_module.bulk_widgets['lang'] = BulkLang
                print(f"Successfully added BulkLang to bulk_widgets dictionary")

            # override the original populate_metadata_page function with the new one
            from .custom_column_widgets import populate_metadata_page as mypmp
            custom_column_module.populate_metadata_page = mypmp
            print(f"Successfully replaced populate_metadata_page with mypm")

        except Exception as e:
            import traceback
            print(f"Error during initialization: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
