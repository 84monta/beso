# simple GUI to be used as FreeCAD macro
# all beso python files should be in the macro directory

__title__ = "BESO Topology Optimization"
__author__ = "František Löffelmann"
__date__ = "21/07/2021"
__Wiki__ = "https://github.com/fandaL/beso/wiki/Example-4:-GUI-in-FreeCAD"
__Status__ = "experimental"
__Requires__ = "FreeCAD >=0.18, Python 3"

import os
import sys
import threading
import time
import webbrowser
import beso_lib

from PySide.QtGui import (QDialog, QWidget, QLabel, QFileDialog, QPushButton, QLineEdit, QComboBox, QCheckBox,
                          QListWidget, QSlider, QAbstractItemView, QFont)
from PySide.QtCore import Qt
import FreeCADGui
import FreeCAD as App
from femtools import ccxtools

# Module imports
try:
    from beso_gui_components import (create_label, create_combobox, create_textbox, create_checkbox, 
                                   create_listwidget, setup_domain_controls, setup_filter_controls)
    from beso_gui_handlers import (update_domains, on_domain_change, on_filter_change, on_filter_range_change,
                                 generate_config_callback, edit_config_callback, run_optimization_callback,
                                 run_threaded_optimization, open_example_callback, open_conf_comments_callback,
                                 open_log_file_callback, RunOptimization)
except ImportError:
    print("Warning: Modules not found, falling back to default implementation")


class SelectFile(QDialog):
    """File selection dialog"""
    def __init__(self):
        super().__init__()
        self.title = 'Select input file'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        beso_gui.inp_file = QFileDialog.getOpenFileName(self, "Select CalculiX input file", 
                                                     os.path.dirname(beso_gui.inp_file), 
                                                     "CalculiX input file (*.inp)")[0]
        self.close()


class beso_gui(QDialog):
    """BESO topology optimization GUI"""
    def __init__(self):
        super().__init__()
        self.title = 'BESO Topology Optimization (experimental)'
        self.left = 250
        self.top = 30
        self.width = 550
        self.height = 730

        beso_gui.inp_file = ""
        beso_gui.beso_dir = os.path.dirname(__file__)
        if beso_gui.beso_dir not in sys.path:
            sys.path.append(beso_gui.beso_dir)

        self.initUI()

    def initUI(self):
        """Initialize GUI"""
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # 解析ファイル選択ボタン
        button = QPushButton('Select analysis file', self)
        button.setFont(QFont('Arial', 8))
        button.setToolTip('*.inp CalculiX analysis file.')
        button.move(10, 10)
        button.clicked.connect(self.on_click)

        # ファイル名テキストボックス
        self.textbox_file_name = QLineEdit(self)
        self.textbox_file_name.move(120, 15)
        self.textbox_file_name.resize(420, 20)
        self.textbox_file_name.setText("None analysis file selected")
        self.textbox_file_name.setFont(QFont('Arial', 8))
        self.textbox_file_name.setToolTip('Analysis file.')

        # ドメイン更新ボタン
        button1 = QPushButton('Update domains', self)
        button1.setFont(QFont('Arial', 8))
        button1.setToolTip('Update naming inputs and material data from FreeCAD.')
        button1.move(10, 50)
        button1.clicked.connect(self.on_click1)
        
        # ドメイン定義ラベル
        create_label(self, 'Domain 0', 10, True, (120, 50))
        create_label(self, 'Domain 1', 10, True, (260, 50))
        create_label(self, 'Domain 2', 10, True, (400, 50))
        create_label(self, 'Material object', 8, False, (20, 80))
        create_label(self, 'Thickness object', 8, False, (20, 110))
        create_label(self, 'As design domain', 8, False, (20, 140))
        create_label(self, 'Stress limit [MPa]', 8, False, (20, 170))

        # ドメイン0のコントロール
        domain0_controls = setup_domain_controls(self, 0, 120, 
                                              {'on_change': self.on_change})
        self.combo = domain0_controls['combo']
        self.combo0t = domain0_controls['combo_t']
        self.checkbox = domain0_controls['checkbox']
        self.textbox = domain0_controls['textbox']

        # ドメイン1のコントロール
        domain1_controls = setup_domain_controls(self, 1, 260, 
                                              {'on_change1': self.on_change1})
        self.combo1 = domain1_controls['combo']
        self.combo1t = domain1_controls['combo_t']
        self.checkbox1 = domain1_controls['checkbox']
        self.textbox1 = domain1_controls['textbox']

        # ドメイン2のコントロール
        domain2_controls = setup_domain_controls(self, 2, 400, 
                                              {'on_change2': self.on_change2})
        self.combo2 = domain2_controls['combo']
        self.combo2t = domain2_controls['combo_t']
        self.checkbox2 = domain2_controls['checkbox']
        self.textbox2 = domain2_controls['textbox']

        # フィルターラベル
        create_label(self, 'Filter 0', 10, True, (120, 220))
        create_label(self, 'Filter 1', 10, True, (260, 220))
        create_label(self, 'Filter 2', 10, True, (400, 220))
        create_label(self, 'Type', 8, False, (20, 240))
        create_label(self, 'Range [mm]', 8, False, (20, 270))
        create_label(self, 'Direction vector', 8, False, (20, 300))
        create_label(self, 'Apply to', 8, False, (20, 330))

        # フィルター0のコントロール
        filter0_callbacks = {
            'on_change6': self.on_change6,
            'on_change6r': self.on_change6r
        }
        filter0_controls = setup_filter_controls(self, 0, 120, filter0_callbacks)
        self.combo6 = filter0_controls['combo']
        self.combo6r = filter0_controls['combo_r']
        self.textbox6 = filter0_controls['textbox_range']
        self.textbox9 = filter0_controls['textbox_direction']
        self.widget = filter0_controls['widget']

        # フィルター1のコントロール
        filter1_callbacks = {
            'on_change7': self.on_change7,
            'on_change7r': self.on_change7r
        }
        filter1_controls = setup_filter_controls(self, 1, 260, filter1_callbacks)
        self.combo7 = filter1_controls['combo']
        self.combo7r = filter1_controls['combo_r']
        self.textbox7 = filter1_controls['textbox_range']
        self.textbox10 = filter1_controls['textbox_direction']
        self.widget1 = filter1_controls['widget']

        # フィルター2のコントロール
        filter2_callbacks = {
            'on_change8': self.on_change8,
            'on_change8r': self.on_change8r
        }
        filter2_controls = setup_filter_controls(self, 2, 400, filter2_callbacks)
        self.combo8 = filter2_controls['combo']
        self.combo8r = filter2_controls['combo_r']
        self.textbox8 = filter2_controls['textbox_range']
        self.textbox11 = filter2_controls['textbox_direction']
        self.widget2 = filter2_controls['widget']

        # その他の設定
        label40 = create_label(self, 'Other settings', 10, True, (10, 470))

        # イテレーションごとの変化率スライダー
        label41 = create_label(self, 'Change per iteration:   low', 8, False, (10, 500), 160)
        label42 = create_label(self, 'high', 8, False, (240, 500))

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(1, 3)
        self.slider.setSingleStep(1)
        self.slider.setValue(2)
        self.slider.move(150, 500)
        self.slider.resize(80, 30)
        self.slider.setToolTip('Sets mass change per iteration, which is controlled as\n'
                             'slow:   mass_addition_ratio=0.01,  mass_removal_ratio=0.02\n'
                             'middle: mass_addition_ratio=0.015, mass_removal_ratio=0.03\n'
                             'fast:   mass_addition_ratio=0.03,  mass_removal_ratio=0.06')

        # 最適化ベースコンボボックス
        label51 = create_label(self, 'Optimization base', 8, False, (10, 530))
        self.combo51 = create_combobox(
            self,
            tooltip='Basic principle to determine if element should remain or be removed:\n'
                    '"stiffness" to maximize stiffness (minimize compliance),\n'
                    '"heat" to maximize heat flow.',
            position=(120, 530),
            items=["stiffness", "heat"]
        )

        # 質量目標比率
        label52 = create_label(self, 'Mass goal ratio', 8, False, (10, 560))
        self.textbox52 = create_textbox(
            self,
            tooltip='Fraction of all design domains masses to be achieved;\n'
                   'between 0 and 1.',
            position=(120, 560),
            size=(50, 20),
            text="0.4"
        )

        # --- デバッグモード、ベクトル化フィルター、KDTreeチェックボックス ---
        self.debug_mode_checkbox = create_checkbox(
            self,
            tooltip='Enable detailed time measurement logging in the .log file.',
            position=(120, 585),
            checked=False
        )
        label_debug = create_label(self, 'Enable Debug Mode', 8, False, (140, 585))

        self.vectorized_filters_checkbox = create_checkbox(
            self,
            tooltip='Use faster, vectorized implementation for simple filter (requires numpy).',
            position=(300, 585),
            checked=False
        )
        label_vect = create_label(self, 'Use Vectorized Filters', 8, False, (320, 585))
        
        self.kdtree_checkbox = create_checkbox(
            self,
            tooltip='Use KDTree spatial data structure for faster neighbor search (requires scipy).',
            position=(120, 610),
            checked=False
        )
        label_kdtree = create_label(self, 'Use KDTree Spatial Search', 8, False, (140, 610))
        # --- チェックボックス終了 ---

        # 設定ファイル生成ボタン
        button21 = QPushButton('Generate conf. file', self)
        button21.setFont(QFont('Arial', 8))
        button21.setToolTip('Writes configuration file with optimization parameters.')
        button21.move(10, 640)
        button21.clicked.connect(self.on_click21)

        # 設定ファイル編集ボタン
        button22 = QPushButton('Edit conf. file', self)
        button22.setFont(QFont('Arial', 8))
        button22.setToolTip('Opens configuration file for hand modifications.')
        button22.move(10, 670)
        button22.clicked.connect(self.on_click22)

        # 最適化実行ボタン
        button23 = QPushButton('Run optimization', self)
        button23.setFont(QFont('Arial', 8))
        button23.setToolTip('Writes configuration file and runs optimization.')
        button23.move(10, 700)
        button23.clicked.connect(self.on_click23)

        # 設定ファイル生成と最適化実行ボタン
        button24 = QPushButton('Generate conf.\nfile and run\noptimization', self)
        button24.setFont(QFont('Arial', 8))
        button24.setToolTip('Writes configuration file and runs optimization.')
        button24.move(120, 640)
        button24.resize(100, 90)
        button24.clicked.connect(self.on_click24)

        # ヘルプボタン
        label41_help = create_label(self, 'Help', 10, True, (440, 600))

        button31 = QPushButton('Example', self)
        button31.setFont(QFont('Arial', 8))
        button31.setToolTip('https://github.com/fandaL/beso/wiki/Example-4:-GUI-in-FreeCAD')
        button31.move(440, 630)
        button31.clicked.connect(self.on_click31)

        button32 = QPushButton('Conf. comments', self)
        button32.setFont(QFont('Arial', 8))
        button32.setToolTip('https://github.com/fandaL/beso/blob/master/beso_conf.py')
        button32.move(440, 660)
        button32.clicked.connect(self.on_click32)

        button33 = QPushButton('Close', self)
        button33.setFont(QFont('Arial', 8))
        button33.move(440, 705)
        button33.clicked.connect(self.on_click33)

        # ログファイルを開くボタン
        button40 = QPushButton('Open log file', self)
        button40.setFont(QFont('Arial', 8))
        button40.setToolTip('Opens log file in your text editor.\n'
                         '(Does not refresh automatically.)')
        button40.move(230, 705)
        button40.clicked.connect(self.on_click40)

        # 初期更新
        self.on_click1()
        self.show()

    def closeEvent(self, event):
        """ダイアログが閉じられる際のイベントハンドラ"""
        # ここでウィジェットの参照を明示的に削除したり、
        # deleteLater() を呼び出すなどのクリーンアップ処理を行う
        # 例: self.combo = None, self.textbox_file_name.deleteLater() など
        # ただし、どのウィジェットをどのようにクリーンアップすべきかは
        # FreeCAD/PySideの挙動に依存するため、慎重な検討が必要
        print("BESO GUI closing... Attempting to clean up widgets.") # クリーンアップ処理のログ（必要に応じて）

        # 主要なウィジェットに対して deleteLater() を呼び出す
        widgets_to_delete = [
            'textbox_file_name', 'combo', 'combo0t', 'checkbox', 'textbox',
            'combo1', 'combo1t', 'checkbox1', 'textbox1',
            'combo2', 'combo2t', 'checkbox2', 'textbox2',
            'combo6', 'combo6r', 'textbox6', 'textbox9', 'widget',
            'combo7', 'combo7r', 'textbox7', 'textbox10', 'widget1',
            'combo8', 'combo8r', 'textbox8', 'textbox11', 'widget2',
            'slider', 'combo51', 'textbox52',
            'debug_mode_checkbox', 'vectorized_filters_checkbox', 'kdtree_checkbox'
        ]
        for attr_name in widgets_to_delete:
            widget = getattr(self, attr_name, None)
            if widget:
                try:
                    widget.deleteLater()
                    # print(f"Scheduled {attr_name} for deletion.") # 詳細ログ
                except Exception as e:
                    print(f"Error scheduling {attr_name} for deletion: {e}")

        super(beso_gui, self).closeEvent(event)

    # イベントハンドラーメソッド
    def on_click(self):
        """Analysis file selection button click handler"""
        ex2 = SelectFile()
        self.show()
        self.textbox_file_name.setText(self.inp_file)

    def on_click1(self):
        """ドメイン更新ボタンクリックハンドラー"""
        try:
            # モジュール分割版の関数を使用
            update_domains(self)
        except NameError:
            # 従来版の実装（フォールバック）
            # 材料オブジェクトと厚みオブジェクトの取得
            self.materials = []
            self.thicknesses = []
            try:
                App.ActiveDocument.Objects
            except AttributeError:
                App.newDocument("Unnamed")
                print("Warning: Missing active document with FEM analysis. New document have been created.")
            for obj in App.ActiveDocument.Objects:
                if obj.Name[:23] == "MechanicalSolidMaterial":
                    self.materials.append(obj)
                elif obj.Name[:13] == "MaterialSolid":
                    self.materials.append(obj)
                elif obj.Name[:13] == "SolidMaterial":
                    self.materials.append(obj)
                elif obj.Name[:17] == "ElementGeometry2D":
                    self.thicknesses.append(obj)
            # UIの更新
            self.combo.clear()
            self.combo.addItem("None")
            self.combo1.clear()
            self.combo1.addItem("None")
            self.combo2.clear()
            self.combo2.addItem("None")
            self.combo0t.clear()
            self.combo0t.addItem("None")
            self.combo1t.clear()
            self.combo1t.addItem("None")
            self.combo2t.clear()
            self.combo2t.addItem("None")
            self.widget.clear()
            self.widget.addItem("All defined")
            self.widget.addItem("Domain 0")
            self.widget.addItem("Domain 1")
            self.widget.addItem("Domain 2")
            self.widget.setCurrentItem(self.widget.item(0))
            self.widget1.clear()
            self.widget1.addItem("All defined")
            self.widget1.addItem("Domain 0")
            self.widget1.addItem("Domain 1")
            self.widget1.addItem("Domain 2")
            self.widget1.setCurrentItem(self.widget1.item(0))
            self.widget2.clear()
            self.widget2.addItem("All defined")
            self.widget2.addItem("Domain 0")
            self.widget2.addItem("Domain 1")
            self.widget2.addItem("Domain 2")
            self.widget2.setCurrentItem(self.widget2.item(0))
            for mat in self.materials:
                self.combo.addItem(mat.Label)
                self.combo1.addItem(mat.Label)
                self.combo2.addItem(mat.Label)
            if self.materials:
                self.combo.setCurrentIndex(1)
            for th in self.thicknesses:
                self.combo0t.addItem(th.Label)
                self.combo1t.addItem(th.Label)
                self.combo2t.addItem(th.Label)

    def on_click21(self):
        """設定ファイル生成ボタンクリックハンドラー"""
        try:
            # モジュール分割版の関数を使用
            return generate_config_callback(self)
        except NameError:
            from beso_gui_orig_DONOTMODIFY import beso_gui as OrigBesGUI
            # 従来版の実装（フォールバック）
            orig_instance = OrigBesGUI()
            orig_instance.on_click21()
            return os.path.join(self.beso_dir, "beso_conf.py")

    def on_click22(self):
        """設定ファイル編集ボタンクリックハンドラー"""
        try:
            # モジュール分割版の関数を使用
            edit_config_callback(self)
        except NameError:
            # 従来版の実装（フォールバック）
            conf_file_path = self.on_click21()
            FreeCADGui.insert(os.path.normpath(conf_file_path))

    def on_click23(self):
        """最適化実行ボタンクリックハンドラー"""
        try:
            # モジュール分割版の関数を使用
            run_optimization_callback(self)
        except NameError:
            # 従来版の実装（フォールバック）
            self.on_click21()  # 設定ファイル生成
            # foregroundで実行（FreeCADがフリーズ、UTF-8エンコーディングを明示的に指定）
            exec(open(os.path.join(beso_gui.beso_dir, "beso_main.py"), encoding="utf-8").read())

    def on_click24(self):
        """設定ファイル生成と最適化実行ボタンクリックハンドラー"""
        self.on_click21()  # 設定ファイル生成
        self.on_click23()  # 最適化実行

    def on_click31(self):
        """サンプル例を開くボタンクリックハンドラー"""
        try:
            # モジュール分割版の関数を使用
            open_example_callback(self)
        except NameError:
            # 従来版の実装（フォールバック）
            webbrowser.open_new_tab("https://github.com/fandaL/beso/wiki/Example-4:-GUI-in-FreeCAD")

    def on_click32(self):
        """設定コメントを開くボタンクリックハンドラー"""
        try:
            # モジュール分割版の関数を使用
            open_conf_comments_callback(self)
        except NameError:
            # 従来版の実装（フォールバック）
            webbrowser.open_new_tab("https://github.com/fandaL/beso/blob/master/beso_conf.py")

    def on_click33(self):
        """閉じるボタンクリックハンドラー"""
        self.close()

    def on_click40(self):
        """ログファイルを開くボタンクリックハンドラー"""
        try:
            # モジュール分割版の関数を使用
            open_log_file_callback(self)
        except NameError:
            # 従来版の実装（フォールバック）
            if self.textbox_file_name.text() in ["None analysis file selected", ""]:
                print("None analysis file selected")
            else:
                log_file = os.path.normpath(self.textbox_file_name.text()[:-4] + ".log")
                try:
                    FreeCADGui.open(log_file)
                except:
                    print(f"No log file found at {log_file}")

    def on_change(self, i):
        """ドメイン0選択変更ハンドラー"""
        try:
            # モジュール分割版の関数を使用
            on_domain_change(self, 0, i)
        except NameError:
            # 従来版の実装（フォールバック）
            if i == 0:  # None
                self.combo0t.setEnabled(False)
                self.checkbox.setEnabled(False)
                self.textbox.setEnabled(False)
            else:
                self.combo0t.setEnabled(True)
                self.checkbox.setEnabled(True)
                self.textbox.setEnabled(True)

    def on_change1(self, i):
        """ドメイン1選択変更ハンドラー"""
        try:
            # モジュール分割版の関数を使用
            on_domain_change(self, 1, i)
        except NameError:
            # 従来版の実装（フォールバック）
            if i == 0:  # None
                self.combo1t.setEnabled(False)
                self.checkbox1.setEnabled(False)
                self.textbox1.setEnabled(False)
            else:
                self.combo1t.setEnabled(True)
                self.checkbox1.setEnabled(True)
                self.textbox1.setEnabled(True)

    def on_change2(self, i):
        """ドメイン2選択変更ハンドラー"""
        try:
            # モジュール分割版の関数を使用
            on_domain_change(self, 2, i)
        except NameError:
            # 従来版の実装（フォールバック）
            if i == 0:  # None
                self.combo2t.setEnabled(False)
                self.checkbox2.setEnabled(False)
                self.textbox2.setEnabled(False)
            else:
                self.combo2t.setEnabled(True)
                self.checkbox2.setEnabled(True)
                self.textbox2.setEnabled(True)

    def on_change6(self, i):
        """フィルター0タイプ変更ハンドラー"""
        try:
            # モジュール分割版の関数を使用
            on_filter_change(self, 0, i)
        except NameError:
            # 従来版の実装（フォールバック）
            if i == 0:  # None
                self.combo6r.setEnabled(False)
                self.textbox6.setEnabled(False)
                self.textbox9.setEnabled(False)
                self.widget.setEnabled(False)
            elif i == 2:  # casting
                self.combo6r.setEnabled(True)
                if self.combo6r.currentText() == "manual":
                    self.textbox6.setEnabled(True)
                self.textbox9.setEnabled(True)
                self.widget.setEnabled(True)
            else:
                self.combo6r.setEnabled(True)
                if self.combo6r.currentText() == "manual":
                    self.textbox6.setEnabled(True)
                self.textbox9.setEnabled(False)
                self.widget.setEnabled(True)

    def on_change7(self, i):
        """フィルター1タイプ変更ハンドラー"""
        try:
            # モジュール分割版の関数を使用
            on_filter_change(self, 1, i)
        except NameError:
            # 従来版の実装（フォールバック）
            if i == 0:  # None
                self.combo7r.setEnabled(False)
                self.textbox7.setEnabled(False)
                self.textbox10.setEnabled(False)
                self.widget1.setEnabled(False)
            elif i == 2:  # casting
                self.combo7r.setEnabled(True)
                if self.combo7r.currentText() == "manual":
                    self.textbox7.setEnabled(True)
                self.textbox10.setEnabled(True)
                self.widget1.setEnabled(True)
            else:
                self.combo7r.setEnabled(True)
                if self.combo7r.currentText() == "manual":
                    self.textbox7.setEnabled(True)
                self.textbox10.setEnabled(False)
                self.widget1.setEnabled(True)

    def on_change8(self, i):
        """フィルター2タイプ変更ハンドラー"""
        try:
            # モジュール分割版の関数を使用
            on_filter_change(self, 2, i)
        except NameError:
            # 従来版の実装（フォールバック）
            if i == 0:  # None
                self.combo8r.setEnabled(False)
                self.textbox8.setEnabled(False)
                self.textbox11.setEnabled(False)
                self.widget2.setEnabled(False)
            elif i == 2:  # casting
                self.combo8r.setEnabled(True)
                if self.combo8r.currentText() == "manual":
                    self.textbox8.setEnabled(True)
                self.textbox11.setEnabled(True)
                self.widget2.setEnabled(True)
            else:
                self.combo8r.setEnabled(True)
                if self.combo8r.currentText() == "manual":
                    self.textbox8.setEnabled(True)
                self.textbox11.setEnabled(False)
                self.widget2.setEnabled(True)

    def on_change6r(self, i):
        """フィルター0レンジタイプ変更ハンドラー"""
        try:
            # モジュール分割版の関数を使用
            on_filter_range_change(self, 0, i)
        except NameError:
            # 従来版の実装（フォールバック）
            if i == 0:  # auto
                self.textbox6.setEnabled(False)
            else:
                self.textbox6.setEnabled(True)

    def on_change7r(self, i):
        """フィルター1レンジタイプ変更ハンドラー"""
        try:
            # モジュール分割版の関数を使用
            on_filter_range_change(self, 1, i)
        except NameError:
            # 従来版の実装（フォールバック）
            if i == 0:  # auto
                self.textbox7.setEnabled(False)
            else:
                self.textbox7.setEnabled(True)

    def on_change8r(self, i):
        """フィルター2レンジタイプ変更ハンドラー"""
        try:
            # モジュール分割版の関数を使用
            on_filter_range_change(self, 2, i)
        except NameError:
            # 従来版の実装（フォールバック）
            if i == 0:  # auto
                self.textbox8.setEnabled(False)
            else:
                self.textbox8.setEnabled(True)


# FreeCADマクロとして実行
if __name__ == '__main__':
    ex = beso_gui()
