"""
BESOトポロジー最適化GUIのコンポーネント
このモジュールにはUI要素作成のヘルパー関数が含まれています
"""

from PySide.QtGui import QLabel, QComboBox, QLineEdit, QCheckBox, QFont, QListWidget, QAbstractItemView


def create_label(parent, text, font_size=8, bold=False, position=(0, 0), fixed_width=None):
    """ラベルを作成する汎用関数"""
    label = QLabel(text, parent)
    label.setFont(QFont('Arial', font_size))
    if bold:
        label.setStyleSheet("font-weight: bold")
    label.move(position[0], position[1])
    if fixed_width:
        label.setFixedWidth(fixed_width)
    return label


def create_combobox(parent, tooltip="", position=(0, 0), size=(140, 30), font_size=8, enabled=True, items=None, 
                   current_index=0, on_change=None):
    """コンボボックスを作成する汎用関数"""
    combo = QComboBox(parent)
    combo.setFont(QFont('Arial', font_size))
    combo.setToolTip(tooltip)
    combo.move(position[0], position[1])
    combo.resize(size[0], size[1])
    combo.setEnabled(enabled)
    
    if items:
        for item in items:
            combo.addItem(item)
    
    if current_index is not None:
        combo.setCurrentIndex(current_index)
    
    if on_change:
        combo.currentIndexChanged.connect(on_change)
    
    return combo


def create_textbox(parent, tooltip="", position=(0, 0), size=(40, 20), font_size=8, enabled=True, text=""):
    """テキストボックスを作成する汎用関数"""
    textbox = QLineEdit(parent)
    textbox.setFont(QFont('Arial', font_size))
    textbox.move(position[0], position[1])
    textbox.resize(size[0], size[1])
    textbox.setToolTip(tooltip)
    textbox.setEnabled(enabled)
    if text:
        textbox.setText(text)
    return textbox


def create_checkbox(parent, tooltip="", position=(0, 0), checked=True):
    """チェックボックスを作成する汎用関数"""
    checkbox = QCheckBox('', parent)
    checkbox.setChecked(checked)
    checkbox.setToolTip(tooltip)
    checkbox.move(position[0], position[1])
    return checkbox


def create_listwidget(parent, tooltip="", position=(0, 0), size=(140, 120), font_size=8, enabled=True, 
                     selection_mode=QAbstractItemView.MultiSelection, items=None, selected_indices=None):
    """リストウィジェットを作成する汎用関数"""
    listwidget = QListWidget(parent)
    listwidget.setFont(QFont('Arial', font_size))
    listwidget.setToolTip(tooltip)
    listwidget.move(position[0], position[1])
    listwidget.resize(size[0], size[1])
    listwidget.setSelectionMode(selection_mode)
    listwidget.setEnabled(enabled)
    
    if items:
        for item in items:
            listwidget.addItem(item)
    
    if selected_indices:
        for index in selected_indices:
            listwidget.setCurrentItem(listwidget.item(index))
    
    return listwidget


def setup_domain_controls(parent, domain_index, x_offset, callback_dict):
    """ドメイン関連のコントロールを設定する関数"""
    # ドメインコントロールを作成する共通コード
    # Domain material combo box
    combo = create_combobox(
        parent, 
        tooltip='Material object to define the domain.',
        position=(x_offset, 80),
        on_change=callback_dict.get(f'on_change{domain_index}' if domain_index else 'on_change')
    )
    
    # Domain thickness combo box
    combo_t = create_combobox(
        parent,
        tooltip='Thickness object to specify if domain is for shells.',
        position=(x_offset, 110),
    )
    
    # Domain checkbox
    checkbox = create_checkbox(
        parent,
        tooltip='Check to be the design domain.',
        position=(x_offset, 140)
    )
    
    # Domain stress limit textbox
    textbox = create_textbox(
        parent,
        tooltip='Von Mises stress [MPa] limit, when reached, material removing will stop.',
        position=(x_offset, 170)
    )
    
    return {
        'combo': combo,
        'combo_t': combo_t,
        'checkbox': checkbox,
        'textbox': textbox
    }


def setup_filter_controls(parent, filter_index, x_offset, callback_dict):
    """フィルター関連のコントロールを設定する関数"""
    # フィルタータイプのコンボボックス
    combo = create_combobox(
        parent,
        tooltip='Filters:\n'
                '"simple" to suppress checkerboard effect,\n'
                '"casting" to prescribe casting direction (opposite to milling direction)\n'
                'Recommendation: for casting use as first "casting" and as second "simple"',
        position=(x_offset, 240),
        items=["None", "simple", "casting"],
        current_index=1 if filter_index == 0 else 0,
        on_change=callback_dict.get(f'on_change{6+filter_index}')
    )
    
    # フィルターレンジのコンボボックス
    combo_r = create_combobox(
        parent,
        tooltip='auto - automatically calculates element size and uses two times for the filter range\n',
        position=(x_offset, 270),
        items=["auto", "manual"],
        enabled=(filter_index == 0),
        on_change=callback_dict.get(f'on_change{6+filter_index}r')
    )
    
    # 手動レンジのテキストボックス
    textbox_range = create_textbox(
        parent,
        tooltip='Manual filter range [mm], \nrecommended two times mesh size.',
        position=(x_offset + 70, 270),
        size=(50, 20),
        text="0.",
        enabled=False
    )
    
    # キャスティング方向ベクトルのテキストボックス
    textbox_direction = create_textbox(
        parent,
        tooltip='Casting direction vector, e.g. direction in z axis:\n'
                '0, 0, 1\n\n'
                'solid              void\n'
                'XXXXXX.................\n'
                'XXX........................\n'
                'XX...........................          --> z axis\n'
                'XXXXX....................\n'
                'XXXXXXXXXXX......',
        position=(x_offset, 300),
        size=(80, 20),
        text="0, 0, 1",
        enabled=False
    )
    
    # 適用先リストウィジェット
    widget = create_listwidget(
        parent,
        tooltip='Domains affected by the filter.\n'
                'Select only from domains which you defined above.',
        position=(x_offset, 330),
        enabled=(filter_index == 0)
    )
    
    return {
        'combo': combo,
        'combo_r': combo_r,
        'textbox_range': textbox_range,
        'textbox_direction': textbox_direction,
        'widget': widget
    }
