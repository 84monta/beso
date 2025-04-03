"""
BESOトポロジー最適化GUI用の設定ファイル生成モジュール
このモジュールには設定ファイル生成のためのロジックが含まれています
"""

import os
import datetime
import FreeCAD as App
from femtools import ccxtools


def generate_material_block(material_data, multiplier=1.0):
    """材料データブロックを生成する"""
    modulus = material_data.get('modulus', 0) * multiplier
    poisson = material_data.get('poisson', 0)
    density = material_data.get('density', 0) * multiplier
    conductivity = material_data.get('conductivity', 0) * multiplier
    expansion = material_data.get('expansion', 0) * multiplier
    specific_heat = material_data.get('specific_heat', 0) * multiplier
    
    material_block = f"*ELASTIC\n{modulus:.6}, {poisson}\n"
    material_block += f"*DENSITY\n{density:.6}\n"
    
    if conductivity:
        material_block += f"*CONDUCTIVITY\n{conductivity:.6}\n"
    if expansion:
        material_block += f"*EXPANSION\n{expansion:.6}\n"
    if specific_heat:
        material_block += f"*SPECIFIC HEAT\n{specific_heat:.6}\n"
    
    return material_block


def process_material_data(material_obj):
    """FreeCADの材料オブジェクトからデータを抽出"""
    data = {}
    
    # ヤング率（弾性率）
    if material_obj.Material["YoungsModulus"].split()[1] == "MPa":
        data['modulus'] = float(material_obj.Material["YoungsModulus"].split()[0])  # MPa
    elif material_obj.Material["YoungsModulus"].split()[1] == "GPa":
        data['modulus'] = float(material_obj.Material["YoungsModulus"].split()[0]) * 1000  # GPa -> MPa
    elif material_obj.Material["YoungsModulus"].split()[1] == "kg/(mm*s^2)":
        data['modulus'] = float(material_obj.Material["YoungsModulus"].split()[0]) / 1000  # kPa -> MPa
    else:
        raise Exception(f" 単位が認識できません: {material_obj.Name}")
    
    # ポアソン比
    data['poisson'] = float(material_obj.Material["PoissonRatio"].split()[0])
    
    # 密度
    try:
        if material_obj.Material["Density"].split()[1] not in ["kg/m^3", "kg/m3"]:
            data['density'] = float(material_obj.Material["Density"].split()[0]) * 1e-12  # kg/m3 -> t/mm3
        elif material_obj.Material["Density"].split()[1] == "kg/mm^3":
            data['density'] = float(material_obj.Material["Density"].split()[0]) / 1000  # kg/mm3 -> t/mm3
        else:
            raise Exception(f" 単位が認識できません: {material_obj.Name}")
    except KeyError:
        data['density'] = 0.
    
    # 熱伝導率
    try:
        if material_obj.Material["ThermalConductivity"].split()[1] == "W/m/K":
            data['conductivity'] = float(material_obj.Material["ThermalConductivity"].split()[0])  # W/m/K
        elif material_obj.Material["ThermalConductivity"].split()[1] == "mm*kg/(s^3*K)":
            data['conductivity'] = float(material_obj.Material["ThermalConductivity"].split()[0]) / 1000  # mm*kg/(s^3*K) -> W/m/K
        else:
            raise Exception(f" 単位が認識できません: {material_obj.Name}")
    except KeyError:
        data['conductivity'] = 0.
    
    # 熱膨張係数
    try:
        if material_obj.Material["ThermalExpansionCoefficient"].split()[1] in ["um/m/K", "µm/m/K"]:
            data['expansion'] = float(material_obj.Material["ThermalExpansionCoefficient"].split()[0]) * 1e-6  # um/m/K -> mm/mm/K
        elif material_obj.Material["ThermalExpansionCoefficient"].split()[1] in ["m/m/K", "1/K"]:
            data['expansion'] = float(material_obj.Material["ThermalExpansionCoefficient"].split()[0])  # m/m/K -> mm/mm/K
        else:
            raise Exception(f" 単位が認識できません: {material_obj.Name}")
    except KeyError:
        data['expansion'] = 0.
    
    # 比熱
    try:
        if material_obj.Material["SpecificHeat"].split()[1] == "J/kg/K":
            data['specific_heat'] = float(material_obj.Material["SpecificHeat"].split()[0]) * 1e6  # J/kg/K -> mm^2/s^2/K
        elif material_obj.Material["SpecificHeat"].split()[1] == "kJ/kg/K":
            data['specific_heat'] = float(material_obj.Material["SpecificHeat"].split()[0]) * 1e9  # kJ/kg/K -> mm^2/s^2/K
        elif material_obj.Material["SpecificHeat"].split()[1] in ["mm^2/s^2/K", "mm^2/(s^2*K)"]:
            data['specific_heat'] = float(material_obj.Material["SpecificHeat"].split()[0])
        else:
            raise Exception(f" 単位が認識できません: {material_obj.Name}")
    except KeyError:
        data['specific_heat'] = 0.
    
    return data


def process_domain_data(domain_data, beso_gui_instance):
    """ドメインデータを処理し、設定ファイル用のエントリを生成"""
    domain_entries = []
    
    for domain_idx, domain in enumerate(domain_data):
        if not domain.get('material_idx', -1) >= 0:
            continue
        
        # 材料オブジェクト取得
        material_obj = beso_gui_instance.materials[domain['material_idx']]
        material_data = process_material_data(material_obj)
        
        # 厚みオブジェクト処理
        thickness = "0."
        thickness_obj = None
        if domain.get('thickness_idx', -1) >= 0:
            thickness_obj = beso_gui_instance.thicknesses[domain['thickness_idx']]
            thickness = str(thickness_obj.Thickness).split()[0]  # mm
            if str(thickness_obj.Thickness).split()[1] != "mm":
                raise Exception(f" 単位が認識できません: {thickness_obj.Name}")
            
            # セット名の設定
            elset_name = f"{material_obj.Name}{thickness_obj.Name}"
        else:
            # 厚みがない場合のセット名
            elset_name = f"{material_obj.Name}Solid"
        
        # 最適化フラグ
        optimized = domain.get('optimized', True)
        
        # 応力制限
        von_mises = 0.
        if domain.get('stress_limit') and domain['stress_limit'].strip():
            von_mises = float(domain['stress_limit'])
        
        # ドメインエントリ生成
        entry = f"elset_name = '{elset_name}'\n"
        entry += f"domain_optimized[elset_name] = {optimized}\n"
        entry += f"domain_density[elset_name] = [{material_data['density'] * 1e-6:.6e}, {material_data['density']:.6e}]\n"
        
        if thickness and thickness != "0.":
            entry += f"domain_thickness[elset_name] = [{thickness}, {thickness}]\n"
        
        if von_mises:
            entry += f"domain_FI[elset_name] = [[('stress_von_Mises', {von_mises * 1e6:.6})],\n"
            entry += f"                         [('stress_von_Mises', {von_mises:.6})]]\n"
        
        # 材料ブロック生成
        void_material = generate_material_block(material_data, 1e-6)
        solid_material = generate_material_block(material_data, 1.0)
        
        # 三重引用符を使用してマルチライン文字列として処理
        entry += f"domain_material[elset_name] = ['''{void_material}''',\n"
        entry += f"                               '''{solid_material}''']\n\n"
        
        domain_entries.append(entry)
    
    return "".join(domain_entries)


def process_filter_data(filter_data):
    """フィルターデータを処理し、設定ファイル用のエントリを生成"""
    filter_entries = "filter_list = ["
    
    for filter_idx, filter_info in enumerate(filter_data):
        filter_type = filter_info.get('type')
        if not filter_type or filter_type == "None":
            continue
        
        # レンジ設定
        if filter_info.get('range_type') == "auto":
            range_value = '"auto"'
        else:
            range_value = filter_info.get('range_value', "0.")
        
        # フィルターエントリの構築
        filter_entry = f"['{filter_type}', {range_value}"
        
        # キャスティング方向ベクトル追加（キャスティングフィルターの場合）
        if filter_type == "casting":
            direction = filter_info.get('direction', "0, 0, 1")
            filter_entry += f", ({direction})"
        
        # 影響を受けるドメイン
        affected_domains = filter_info.get('affected_domains', [])
        if affected_domains:
            for domain in affected_domains:
                filter_entry += f", '{domain}'"
        
        # フィルターエントリを追加
        filter_entries += filter_entry
        
        # フィルターエントリ終了
        filter_entries += "],\n               "
    
    # 最終的な形式に整形
    if filter_entries.endswith(",\n               "):
        filter_entries = filter_entries[:-16] + "\n"
    
    filter_entries += "]\n\n"
    return filter_entries


def generate_config_file(beso_gui_instance, additional_settings=None):
    """設定ファイルを生成"""
    # 基本情報の取得
    file_name = os.path.split(beso_gui_instance.textbox_file_name.text())[1]
    path = os.path.split(beso_gui_instance.textbox_file_name.text())[0].replace("\\", "\\\\")
    
    # CalculiXパス
    fea = ccxtools.FemToolsCcx()
    fea.setup_ccx()
    path_calculix = os.path.normpath(fea.ccx_binary).replace("\\", "\\\\")
    
    # 最適化ベース
    optimization_base = beso_gui_instance.combo51.currentText()
    
    # ドメインデータ収集
    domain_data = []
    for i in range(3):  # 3つのドメイン
        combo_attr = f"combo{i if i else ''}"
        combo_t_attr = f"combo{i}t"
        checkbox_attr = f"checkbox{i if i else ''}"
        textbox_attr = f"textbox{i if i else ''}"
        
        if hasattr(beso_gui_instance, combo_attr):
            combo = getattr(beso_gui_instance, combo_attr)
            combo_t = getattr(beso_gui_instance, combo_t_attr, None)
            checkbox = getattr(beso_gui_instance, checkbox_attr, None)
            textbox = getattr(beso_gui_instance, textbox_attr, None)
            
            domain = {
                'material_idx': combo.currentIndex() - 1,
                'thickness_idx': combo_t.currentIndex() - 1 if combo_t else -1,
                'optimized': checkbox.isChecked() if checkbox else True,
                'stress_limit': textbox.text() if textbox else ""
            }
            domain_data.append(domain)
    
    # フィルターデータ収集
    filter_data = []
    for i in range(3):  # 3つのフィルター
        combo_idx = 6 + i
        combo_attr = f"combo{combo_idx}"
        combo_r_attr = f"combo{combo_idx}r"
        textbox_range_attr = f"textbox{6+i}"
        textbox_dir_attr = f"textbox{9+i}"
        widget_attr = f"widget{i if i else ''}"
        
        if hasattr(beso_gui_instance, combo_attr):
            combo = getattr(beso_gui_instance, combo_attr)
            combo_r = getattr(beso_gui_instance, combo_r_attr, None)
            textbox_range = getattr(beso_gui_instance, textbox_range_attr, None)
            textbox_dir = getattr(beso_gui_instance, textbox_dir_attr, None)
            widget = getattr(beso_gui_instance, widget_attr, None)
            
            # 選択されたドメイン
            affected_domains = []
            if widget:
                selection = [item.text() for item in widget.selectedItems()]
                if "All defined" not in selection:
                    for d_idx, domain_text in enumerate(["Domain 0", "Domain 1", "Domain 2"]):
                        if domain_text in selection and d_idx < len(domain_data) and domain_data[d_idx]['material_idx'] >= 0:
                            material_obj = beso_gui_instance.materials[domain_data[d_idx]['material_idx']]
                            if domain_data[d_idx]['thickness_idx'] >= 0:
                                thickness_obj = beso_gui_instance.thicknesses[domain_data[d_idx]['thickness_idx']]
                                elset_name = f"{material_obj.Name}{thickness_obj.Name}"
                            else:
                                elset_name = f"{material_obj.Name}Solid"
                            affected_domains.append(elset_name)
            
            filter_info = {
                'type': combo.currentText(),
                'range_type': combo_r.currentText() if combo_r else "auto",
                'range_value': textbox_range.text() if textbox_range else "0.",
                'direction': textbox_dir.text() if textbox_dir else "0, 0, 1",
                'affected_domains': affected_domains
            }
            filter_data.append(filter_info)
    
    # 追加設定の取得
    mass_goal_ratio = beso_gui_instance.textbox52.text()
    
    # スライダー位置から変更率を決定
    slider_position = beso_gui_instance.slider.value()
    if slider_position == 1:
        mass_addition_ratio = 0.01
        mass_removal_ratio = 0.02
    elif slider_position == 2:
        mass_addition_ratio = 0.015
        mass_removal_ratio = 0.03
    else:  # slider_position == 3
        mass_addition_ratio = 0.03
        mass_removal_ratio = 0.06
    
    # 拡張機能の設定（デフォルト：オフ）
    debug_mode = False
    use_vectorized_filters = False
    use_kdtree = False
    
    # 拡張機能の有効/無効チェック
    if hasattr(beso_gui_instance, 'debug_mode_checkbox'):
        debug_mode = beso_gui_instance.debug_mode_checkbox.isChecked()
    if hasattr(beso_gui_instance, 'vectorized_filters_checkbox'):
        use_vectorized_filters = beso_gui_instance.vectorized_filters_checkbox.isChecked()
    if hasattr(beso_gui_instance, 'kdtree_checkbox'):
        use_kdtree = beso_gui_instance.kdtree_checkbox.isChecked()
    
    # 設定ファイル本文生成
    conf_file_text = "# This is the configuration file with input parameters. It will be executed as python commands\n"
    conf_file_text += f"# Written by beso_fc_gui.py at {datetime.datetime.now()}\n\n"
    conf_file_text += f"path_calculix = '{path_calculix}'\n"
    conf_file_text += f"path = '{path}'\n"
    conf_file_text += f"file_name = '{file_name}'\n\n"
    
    # ドメイン情報追加
    conf_file_text += process_domain_data(domain_data, beso_gui_instance)
    
    # 質量目標比
    conf_file_text += f"mass_goal_ratio = {mass_goal_ratio}\n\n"
    
    # フィルターリスト
    conf_file_text += process_filter_data(filter_data)
    
    # 最適化ベース
    conf_file_text += f"optimization_base = '{optimization_base}'\n\n"
    
    # 質量追加・削除比率
    conf_file_text += f"mass_addition_ratio = {mass_addition_ratio}\n"
    conf_file_text += f"mass_removal_ratio = {mass_removal_ratio}\n"
    conf_file_text += "ratio_type = 'relative'\n\n"
    
    # 拡張機能設定
    conf_file_text += "# Debug mode flag (set to True to enable time measurement logging)\n"
    conf_file_text += f"debug_mode = {debug_mode}\n\n"
    
    conf_file_text += "# Use vectorized filters (requires numpy)\n"
    conf_file_text += f"use_vectorized_filters = {use_vectorized_filters}\n\n"
    
    conf_file_text += "# Use KDTree spatial search (requires scipy)\n"
    conf_file_text += f"use_kdtree = {use_kdtree}\n"
    
    return conf_file_text


def write_config_file(beso_gui_instance, path=None):
    """設定ファイルを指定されたパスに書き込む"""
    conf_file_text = generate_config_file(beso_gui_instance)
    
    if not path:
        # デフォルトでは現在の日時でファイル名を生成
        conf_file = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + "_beso_conf.py"
        
        # 入力ファイルのディレクトリを使用
        if beso_gui_instance.inp_file:
            conf_file_path = os.path.join(os.path.dirname(beso_gui_instance.inp_file), conf_file)
        else:
            # 入力ファイルがない場合はホームディレクトリを使用
            conf_file_path = os.path.join(os.path.expanduser("~"), conf_file)
    else:
        conf_file_path = path
    
    # ファイル書き込み
    with open(conf_file_path, "w") as f:
        f.write(conf_file_text)
    
    print(f"Configuration saved to {conf_file_path}")
    return conf_file_path
