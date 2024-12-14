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
    description = 'Override CreateCustomColumn with custom EMA language implementation'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'laverdure'
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)
    actual_plugin = 'calibre_plugins.ema_lang.ui:InterfacePlugin'

    def initialize(self):
        try:
            # Import using relative import
            from .create_custom_column import ECCC
            from calibre.gui2.preferences.create_custom_column import CreateCustomColumn

            # Replace the CreateCustomColumn class in the module
            import sys
            module = sys.modules['calibre.gui2.preferences.create_custom_column']
            original_class = module.CreateCustomColumn
            module.CreateCustomColumn = ECCC
            print(f"Successfully replaced CreateCustomColumn with ECCC")
            
        except Exception as e:
            import traceback
            print(f"Error during initialization: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")

