#!/usr/bin/env python


__license__   = 'GPL v3'
__copyright__ = '2010, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import os
from collections import OrderedDict
from functools import partial

from qt.core import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QIcon,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QStyle,
    Qt,
    QToolButton,
    QUrl,
    QVBoxLayout,
    QWidget,
#ematest IS_LANG
    pyqtSignal,
#ematest IS_LANG
)

from calibre.ebooks.metadata import title_sort
from calibre.gui2 import UNDEFINED_QDATETIME, elided_text, error_dialog, gprefs
from calibre.gui2.comments_editor import Editor as CommentsEditor
from calibre.gui2.complete2 import EditWithComplete as EWC
from calibre.gui2.dialogs.tag_editor import TagEditor
from calibre.gui2.library.delegates import ClearingDoubleSpinBox, ClearingSpinBox
from calibre.gui2.markdown_editor import Editor as MarkdownEditor
from calibre.gui2.widgets2 import DateTimeEdit as DateTimeEditBase
from calibre.gui2.widgets2 import RatingEditor
from calibre.library.comments import comments_to_html
from calibre.utils.config import tweaks
from calibre.utils.date import as_local_time, as_utc, internal_iso_format_string, is_date_undefined, now, qt_from_dt, qt_to_dt
from calibre.utils.icu import lower as icu_lower
from calibre.utils.icu import sort_key

#ematest IS_LANG
from calibre.gui2.languages import LanguagesEdit as LE
#ematest IS_LANG

#ematest IS_LANG
class Lang(Base, LE):
    allow_undo = True
    LABEL = _('&Languages:')
    TOOLTIP = _('A comma separated list of languages for this book')
    FIELD_NAME = 'languages'
    data_changed = pyqtSignal()

    def setup_ui(self, parent):
        LE.__init__(self, parent)
        self.set_clear_button_enabled(False)
        self.textChanged.connect(self.data_changed)
        self.setToolTip(self.TOOLTIP)
        self.sep = self.col_metadata['multiple_seps']
        self.key = self.db.field_metadata.label_to_key(self.col_metadata['label'],
                                                       prefer_custom=True)
        w = self
        self.set_to_undefined = w.clear
        self.widgets = [QLabel(label_string(self.col_metadata['name']), parent)]
        self.finish_ui_setup(parent, lambda parent: w)
                          
    @property
    def current_val(self):
        return self.lang_codes

    @current_val.setter
    def current_val(self, val):
        self.set_lang_codes(val, self.allow_undo)

    def initialize(self, id_):
        self.init_langs(self.db)
        langs = self.db.get_custom(id_, num=self.col_id, index_is_id=True)
        self.current_val = langs
        self.original_val = self.current_val

    def validate_for_commit(self):
        bad = self.validate()
        if bad:
            msg = ngettext('The language %s is not recognized', 'The languages %s are not recognized', len(bad)) % (', '.join(bad))
            return _('Unknown language'), msg, ''
        return None, None, None
#ematest IS_LANG


widgets = {
        'bool' : Bool,
        'rating' : Rating,
        'int': Int,
        'float': Float,
        'datetime': DateTime,
        'text' : Text,
        'comments': comments_factory,
        'series': Series,
        'enumeration': Enumeration,
#ematest IS_LANG
        'lang': Lang,
#ematest IS_LANG        
}


def populate_metadata_page(layout, db, book_id, bulk=False, two_column=False, parent=None):
    def widget_factory(typ, key):
        if bulk:
            w = bulk_widgets[typ](db, key, parent)
        else:
            w = widgets[typ](db, key, parent)
        if book_id is not None:
            w.initialize(book_id)
        return w

    fm = db.field_metadata

    # Get list of all non-composite custom fields. We must make widgets for these
    cols = get_custom_columns_to_display_in_editor(db)
    # This deals with the historical behavior where comments fields go to the
    # bottom, starting on the left hand side. If a comment field is moved to
    # somewhere else then it isn't moved to either side.
    comments_at_end = 0
    for k in cols[::-1]:
        if not column_is_comments(k, fm):
            break
        comments_at_end += 1
    comments_not_at_end = len([k for k in cols if column_is_comments(k, fm)]) - comments_at_end

    count = len(cols)
    layout_rows_for_comments = 9
    if two_column:
        turnover_point = int(((count - comments_at_end + 1) +
                                int(comments_not_at_end*(layout_rows_for_comments-1)))/2)
    else:
        # Avoid problems with multi-line widgets
        turnover_point = count + 1000
    ans = []
    column = row = base_row = max_row = 0
    label_width = 0
    do_elision = gprefs['edit_metadata_elide_labels']
    elide_pos = gprefs['edit_metadata_elision_point']
    elide_pos = elide_pos if elide_pos in {'left', 'middle', 'right'} else 'right'
    # make room on the right side for the scrollbar
    sb_width = QApplication.instance().style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent)
    layout.setContentsMargins(0, 0, sb_width, 0)
    for key in cols:
        if not fm[key]['is_editable']:
            continue  # The job spy plugin can change is_editable
        dt = fm[key]['datatype']
        if dt == 'composite' or (bulk and dt == 'comments'):
            continue
        is_comments = column_is_comments(key, fm)
#ematest IS_LANG
        is_lang=fm[key]['display'].get('is_lang')
        if is_lang :
            dt = 'lang'
#ematest IS_LANG            
        w = widget_factory(dt, fm[key]['colnum'])
        ans.append(w)
        if two_column and is_comments:
            # Here for compatibility with old layout. Comments always started
            # in the left column
            comments_not_at_end -= 1
            # no special processing if the comment field was named in the tweak
            if comments_not_at_end < 0 and comments_at_end > 0:
                # Force a turnover, adding comments widgets below max_row.
                # Save the row to return to if we turn over again
                column = 0
                row = max_row
                base_row = row
                turnover_point = row + int((comments_at_end * layout_rows_for_comments)/2)
                comments_at_end = 0

        l = QGridLayout()
        if is_comments:
            layout.addLayout(l, row, column, layout_rows_for_comments, 1)
            layout.setColumnStretch(column, 100)
            row += layout_rows_for_comments
        else:
            layout.addLayout(l, row, column, 1, 1)
            layout.setColumnStretch(column, 100)
            row += 1
        for c in range(0, len(w.widgets), 2):
            if not is_comments:
                # Set the label column width to a fixed size. Elide labels that
                # don't fit
                wij = w.widgets[c]
                if label_width == 0:
                    font_metrics = wij.fontMetrics()
                    colon_width = font_metrics.horizontalAdvance(':')
                    if bulk:
                        label_width = (font_metrics.averageCharWidth() *
                               gprefs['edit_metadata_bulk_cc_label_length']) - colon_width
                    else:
                        label_width = (font_metrics.averageCharWidth() *
                               gprefs['edit_metadata_single_cc_label_length']) - colon_width
                wij.setMaximumWidth(label_width)
                if c == 0:
                    wij.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
                    l.setColumnMinimumWidth(0, label_width)
                wij.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                t = str(wij.text())
                if t:
                    if do_elision:
                        wij.setText(elided_text(t, font=font_metrics,
                                            width=label_width, pos=elide_pos) + ':')
                    else:
                        wij.setText(t + ':')
                        wij.setWordWrap(True)
                wij.setBuddy(w.widgets[c+1])
                l.addWidget(wij, c, 0)
                l.addWidget(w.widgets[c+1], c, 1)
            else:
                l.addWidget(w.widgets[0], 0, 0, 1, 2)
        max_row = max(max_row, row)
        if row >= turnover_point:
            column = 1
            turnover_point = count + 1000
            row = base_row

    items = []
    if len(ans) > 0:
        items.append(QSpacerItem(10, 10, QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding))
        layout.addItem(items[-1], layout.rowCount(), 0, 1, 1)
        layout.setRowStretch(layout.rowCount()-1, 100)
    return ans, items

#ematest IS_LANG
class BulkLang(Base, LE):

    gui_val = []
    allow_undo = True
    LABEL = _('&Languages:')
    TOOLTIP = _('A comma separated list of languages for this book')
    FIELD_NAME = 'languages'
    data_changed = pyqtSignal()

    def setup_ui(self, parent):
        LE.__init__(self, parent)
        self.set_clear_button_enabled(False)
        self.textChanged.connect(self.data_changed)
        self.setToolTip(self.TOOLTIP)
        self.sep = self.col_metadata['multiple_seps']
        self.key = self.db.field_metadata.label_to_key(self.col_metadata['label'],
                                                       prefer_custom=True)

        values = self.all_values = list(set(self.db.all_custom(num=self.col_id)))

        w = RemoveTags(parent, values)
        w.remove_tags_button.clicked.connect(self.edit_remove)

        w = self
        self.set_to_undefined = w.clear
        self.widgets = [QLabel(label_string(self.col_metadata['name']), parent)]

        self.finish_ui_setup(parent, lambda parent: w)

    def edit_remove(self):
        self.edit(widget=self.removing_widget.tags_box)
                          
    @property
    def current_val(self):
        return list(set(self.lang_codes))

    @current_val.setter
    def current_val(self, val):
        self.set_lang_codes(val, self.allow_undo)

    def initialize(self, id_):
        tmp = []
        self.init_langs(self.db)
        for id in id_:
            val = self.db.get_custom(id, num=self.col_id, index_is_id=True)
            tmp.extend(val)

        langs=list(set(tmp))

        self.current_val = list(set(langs))
        self.original_val = self.current_val

    def commit(self, book_ids, notify=False):
#verificare se, come e quando mettere la checkbox
#        if not self.a_c_checkbox.isChecked():
#            return

        ism = self.col_metadata['multiple_seps']
        remove = set(self.original_val)
        add = set(self.current_val)
        self.db.set_custom_bulk_multiple(book_ids, add=add,
                                    remove=remove, num=self.col_id)


    def validate_for_commit(self):
        bad = self.validate()
        if bad:
            msg = ngettext('The language %s is not recognized', 'The languages %s are not recognized', len(bad)) % (', '.join(bad))
            return _('Unknown language'), msg, ''
        return None, None, None
#ematest IS_LANG


bulk_widgets = {
        'bool' : BulkBool,
        'rating' : BulkRating,
        'int': BulkInt,
        'float': BulkFloat,
        'datetime': BulkDateTime,
        'text' : BulkText,
        'series': BulkSeries,
        'enumeration': BulkEnumeration,
#ematest IS_LANG        
        'lang' : BulkLang,
#ematest IS_LANG        
}
