"""
Ren'Py 项目打包器
根据场景数据和素材文件自动生成完整的Ren'Py视觉小说项目
"""

import os
import json
import shutil
from typing import List, Dict, Optional
from datetime import datetime


# Ren'Py 脚本模板
RPY_SCRIPT_TEMPLATE = '''\
# 本文件由 Galgame Studio 自动生成
# 生成时间: {generated_at}
# 原始小说: {novel_title}
# 模板: {template_name}

# ===== 初始化变量 =====
init python:
{init_python}

# ===== 角色定义 =====
{character_defines}

# ===== 图片声明 =====
{image_declarations}

# ===== 音频声明 =====
{audio_declarations}

# ===== 特殊效果定义 =====
{effect_defines}

# ===== 游戏开始 =====
label start:

    # 初始设置
    $ quick_menu = True
    scene black
    with fade

    # 标题画面
    call screen title_screen

    # 好感度初始化
{affection_init}

{scene_flow}

    # 游戏结束
    $ renpy.full_restart()
    return

# ===== 标题画面 =====
{title_screen}

# ===== CG画廊 =====
{cg_gallery_screen}

# ===== 好感度画面 =====
{affection_screen}
'''

SCENE_TEMPLATE = '''\
    # ==== {scene_id}: {scene_title} ====
    scene {bg_name}
    with {transition}
    play music {bgm_track} fadein 1.0
{sfx_commands}
{character_shows}
{lines}
{choices}
{character_hides}
    stop music fadeout 1.0

'''

OPTIONS_RPY = '''\
# options.rpy - Galgame Studio 自动生成

## 游戏标题
define config.name = "{title}"

## 窗口标题
define config.window_title = "{title}"

## 版本号
define config.version = "1.0"

## 存档
define config.has_autosave = True
define config.autosave_on_quit = True
define config.autosave_on_choice = True
define config.autosave_slots = 10

## 跳过
define config.skip_indicator = True
define config.allow_skipping = True

## 回滚
define config.rollback_enabled = True
define config.hard_rollback_limit = 100

## 文字速度
default preferences.text_cps = 40
default preferences.afm_time = 15

## 文字颜色和大小
define gui.text_color = "#FFFFFF"
define gui.text_size = 28

## 存档文件名编码 (支持中文存档)
define config.save_json_callbacks = []
'''

GUI_RPY = '''\
# gui.rpy - Galgame Studio 自动生成

## === 游戏分辨率 + 字体 (1280x720 视觉小说标准) ===
init python:
    gui.init(1280, 720)
    gui.text_font = "fonts/simhei.ttf"
    gui.name_text_font = "fonts/simhei.ttf"
    gui.interface_text_font = "fonts/simhei.ttf"
    gui.choice_button_text_font = "fonts/simhei.ttf"

## 对话框
define gui.dialogue_xpos = 0.5
define gui.dialogue_ypos = 0.85
define gui.dialogue_width = 0.8

## 名字
define gui.name_xpos = 0.35
define gui.name_ypos = 0.78
define gui.name_text_size = 24

## 文字框
define gui.textbox_height = 180

## 文字大小
define gui.text_size = 28
define gui.interface_text_size = 24
define gui.choice_button_text_size = 22

## 界面颜色
define gui.choice_button_text_idle_color = '#FFFFFF'
define gui.choice_button_text_hover_color = '#FFD700'
'''


# 标题画面模板
TITLE_SCREEN_TEMPLATE = '''\
screen title_screen():
    tag menu
    add "#0a0e17"

    vbox:
        xalign 0.5 yalign 0.35
        spacing 10
        text "{title}":
            size 56
            color "#d4a574"
            xalign 0.5
            outlines [(3, "#00000080")]

    vbox:
        xalign 0.5 yalign 0.65
        spacing 20
        textbutton "开始游戏":
            xysize (280, 48)
            text_size 22
            text_color "#ffffff"
            background "#d4a57430"
            hover_background "#d4a57470"
            action Return()

        textbutton "读取存档":
            xysize (280, 48)
            text_size 22
            text_color "#ffffff"
            background "#d4a57415"
            hover_background "#d4a57450"
            action ShowMenu("load")

        textbutton "退出":
            xysize (280, 48)
            text_size 22
            text_color "#ffffff"
            background "#d4a57415"
            hover_background "#d4a57450"
            action Quit(confirm=True)
'''



def generate_renpy_project(
    scenes: List[Dict],
    novel_title: str,
    output_dir: str,
    project_name: str = None,
    asset_dir: str = None,
    template_id: str = "none",
) -> str:
    """
    生成完整的Ren'Py项目
    
    Args:
        scenes: 场景列表
        novel_title: 小说标题
        output_dir: 输出根目录
        project_name: 项目名（默认用小说标题）
        asset_dir: 素材目录（用户放图片/音频的地方）
    
    Returns:
        生成的Ren'Py项目路径
    """
    if not project_name:
        project_name = _safe_name(novel_title)
    
    project_dir = os.path.join(output_dir, project_name)
    game_dir = os.path.join(project_dir, "game")
    images_dir = os.path.join(game_dir, "images")
    audio_dir = os.path.join(game_dir, "audio")
    
    # 创建目录结构
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    
    # 复制中文字体（黑体，解决方框问题）
    fonts_dir = os.path.join(game_dir, "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    
    _font_copied = False
    _font_sources = [
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\SimHei.ttf",
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\msyhbd.ttf",
    ]
    for _fs in _font_sources:
        if os.path.exists(_fs):
            try:
                shutil.copy2(_fs, os.path.join(fonts_dir, "simhei.ttf"))
                _font_copied = True
                break
            except Exception:
                continue
    
    if not _font_copied:
        # 尝试从系统字体目录递归查找任一中文字体
        try:
            for root, dirs, files in os.walk(r"C:\Windows\Fonts"):
                for f in files:
                    if f.lower().endswith('.ttf') or f.lower().endswith('.ttc'):
                        candidate = os.path.join(root, f)
                        try:
                            shutil.copy2(candidate, os.path.join(fonts_dir, "simhei.ttf"))
                            _font_copied = True
                            break
                        except Exception:
                            continue
                if _font_copied:
                    break
        except Exception:
            pass
    
    # 收集所有角色
    characters = _collect_characters(scenes)
    
    # 生成角色定义
    character_defines = _generate_character_defines(characters)
    
    # 生成图片声明
    image_declarations = _generate_image_declarations(scenes, characters)
    
    # 生成音频声明
    audio_declarations = _generate_audio_declarations(scenes)
    
    # 生成场景流程
    scene_flow = _generate_scene_flow(scenes, characters)
    
    # 生成特殊效果定义
    effect_defines, is_adult = _generate_effect_defines(template_id)
    
    # 生成好感度初始化
    affection_init = _generate_affection_init(template_id)
    
    # 生成CG画廊
    cg_gallery_screen = _generate_cg_gallery(template_id, scenes)
    
    # 生成好感度查看画面
    affection_screen = _generate_affection_screen(template_id)
    
    # 生成init python块
    init_python = _generate_init_python(template_id, is_adult)
    
    # 模板名
    template_name = _get_template_name(template_id)
    
    # 生成标题画面
    title_screen_content = TITLE_SCREEN_TEMPLATE.format(title=novel_title)
    
    # 生成主脚本
    script_content = RPY_SCRIPT_TEMPLATE.format(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        novel_title=novel_title,
        template_name=template_name,
        character_defines=character_defines,
        image_declarations=image_declarations,
        audio_declarations=audio_declarations,
        effect_defines=effect_defines,
        affection_init=affection_init,
        scene_flow=scene_flow,
        title_screen=title_screen_content,
        cg_gallery_screen=cg_gallery_screen,
        affection_screen=affection_screen,
        init_python=init_python,
    )
    
    with open(os.path.join(game_dir, "script.rpy"), "w", encoding="utf-8") as f:
        f.write(script_content)
    
    # 生成配置文件
    with open(os.path.join(game_dir, "options.rpy"), "w", encoding="utf-8") as f:
        f.write(OPTIONS_RPY.format(title=novel_title))
    
    with open(os.path.join(game_dir, "gui.rpy"), "w", encoding="utf-8") as f:
        f.write(GUI_RPY)
    
    # 生成素材清单
    asset_manifest = _generate_asset_manifest(scenes, characters)
    with open(os.path.join(project_dir, "素材清单.md"), "w", encoding="utf-8") as f:
        f.write(asset_manifest)
    
    # 复制素材（如果有）
    if asset_dir and os.path.exists(asset_dir):
        _copy_assets(asset_dir, images_dir, audio_dir)
    
    # 保存场景数据JSON（调试用）
    with open(os.path.join(project_dir, "scenes_data.json"), "w", encoding="utf-8") as f:
        json.dump(scenes, f, ensure_ascii=False, indent=2)
    
    return project_dir


def _collect_characters(scenes: List[Dict]) -> Dict:
    """从场景中收集所有角色"""
    characters = {}
    for scene in scenes:
        for char in scene.get("characters_in_scene", []):
            name = char.get("name", "未知")
            if name not in characters:
                characters[name] = {
                    "name": name,
                    "role": char.get("role", "角色"),
                    "appearance": char.get("appearance", ""),
                    "sprites": [s for s in char.get("sprites_needed", ["default"]) if s],
                }
            else:
                # 合并sprites，过滤None
                existing = set(s for s in characters[name]["sprites"] if s)
                new = set(s for s in char.get("sprites_needed", ["default"]) if s)
                characters[name]["sprites"] = list(existing | new)
    
    return characters


def _generate_character_defines(characters: Dict) -> str:
    """生成Ren'Py角色定义"""
    defines = []
    color_map = _get_character_colors(len(characters))
    
    for i, (name, info) in enumerate(characters.items()):
        color = color_map[i % len(color_map)]
        var_name = _safe_var(name)
        defines.append(
            f'define {var_name} = Character("{name}", color="{color}", '
            f'who_outlines=[(2, "#000000")], '
            f'what_outlines=[(1, "#00000080")])'
        )
    
    return "\n".join(defines) if defines else "# 无角色"


def _generate_image_declarations(scenes: List[Dict], characters: Dict) -> str:
    """生成Ren'Py图片声明"""
    declarations = []
    seen_bgs = set()
    seen_sprites = set()
    
    # 背景图
    for scene in scenes:
        loc = scene.get("location", "")
        if loc and loc not in seen_bgs:
            seen_bgs.add(loc)
            safe_loc = _safe_name(loc)
            declarations.append(
                f'image bg_{safe_loc} = "images/bg_{safe_loc}.png"'
            )
    
    # 角色立绘: 从sprites列表和lines中实际使用的表达式合并
    for name, info in characters.items():
        safe_name = _safe_name(name)
        # 收集所有需要声明的表情
        all_exprs = set(e for e in info.get("sprites", []) if e)
        # 从所有场景的台词中收集实际使用的表情
        for scene in scenes:
            for line in scene.get("lines", []):
                if line.get("speaker", "") == name:
                    expr = line.get("expression")
                    if expr and isinstance(expr, str):
                        all_exprs.add(expr)
        # 始终确保有 default
        all_exprs.add("default")
        for expr in sorted(all_exprs):
            sprite_key = f"{safe_name}_{expr}"
            if sprite_key not in seen_sprites:
                seen_sprites.add(sprite_key)
                # 所有表情都指向 default 图片文件 (用户只需提供 default)
                # 如果有对应表情文件就用，否则回退到 default 图片
                if expr == "default":
                    declarations.append(
                        f'image {safe_name}_{expr} = "images/{safe_name}_{expr}.png"'
                    )
                else:
                    # 表情差分：声明为独立image，文件不存在时Ren'Py会用灰色占位
                    # 但用 ConditionSwitch 更优雅
                    declarations.append(
                        f'image {safe_name}_{expr} = ConditionSwitch(\n'
                        f'    "renpy.loadable(\\"images/{safe_name}_{expr}.png\\")", "images/{safe_name}_{expr}.png",\n'
                        f'    "True", "images/{safe_name}_default.png"\n'
                        f')'
                    )
    
    # CG
    for scene in scenes:
        for cg in scene.get("cg_suggestions", []):
            cg_id = cg.get("cg_id", "")
            if cg_id:
                declarations.append(
                    f'image {cg_id} = "images/{cg_id}.png"'
                )
    
    return "\n".join(declarations) if declarations else "# 无图片"


def _generate_audio_declarations(scenes: List[Dict]) -> str:
    """生成Ren'Py音频声明"""
    declarations = []
    seen_moods = set()
    
    for scene in scenes:
        mood = scene.get("bgm_mood", "")
        if mood and mood not in seen_moods:
            seen_moods.add(mood)
            declarations.append(
                f'define audio.bgm_{mood} = "audio/bgm_{mood}.ogg"'
            )
    
    return "\n".join(declarations) if declarations else "# 无音频"


def _generate_scene_flow(scenes: List[Dict], characters: Dict) -> str:
    """生成场景流程代码"""
    flow_parts = []
    
    for scene in scenes:
        bg_name = f"bg_{_safe_name(scene.get('location', ''))}"
        # 清洗 transition：把 LLM 返回的 'none' 变为 Ren'Py 的 None
        transition = scene.get("transition", "dissolve")
        if transition and transition.lower() == "none":
            transition = "None"
        elif transition and transition not in ("dissolve", "fade", "pixellate", "None"):
            transition = "dissolve"
        bgm_mood = scene.get("bgm_mood", "")
        
        # SFX
        sfx_commands = ""
        for sfx in scene.get("sfx", []):
            sfx_commands += f'    play sound "audio/{sfx}.ogg"\n'
        
        # 角色上场和位置分配
        character_shows = ""
        char_positions = {}  # name -> position
        scene_chars = scene.get("characters_in_scene", [])
        for i, char in enumerate(scene_chars):
            name = char.get("name", "")
            if name not in characters:
                continue
            safe = _safe_name(name)
            positions = ["sprite_center", "sprite_left", "sprite_right"]
            pos = positions[i % 3] if i < 3 else "center"
            char_positions[name] = pos
            # 初始显示 default 表情
            character_shows += f'    show {safe}_default at {pos} with dissolve\n'
        
        # 台词 — 智能表情切换（只在表情变化时才show）
        lines_code = ""
        current_expr = {}  # name -> current expression
        for line in scene.get("lines", []):
            speaker = line.get("speaker", "")
            text = line.get("text", "")
            line_type = line.get("type", "narration")
            
            # 转义引号
            text = text.replace('"', '\\"')
            
            if line_type == "narration" or speaker == "旁白":
                lines_code += f'    "{text}"\n'
            elif speaker in characters:
                var_name = _safe_var(speaker)
                expression = line.get("expression", "default")
                safe_speaker = _safe_name(speaker)
                
                # 只在表情变化时才show新表情
                prev_expr = current_expr.get(speaker, "default")
                if expression != prev_expr:
                    lines_code += f'    show {safe_speaker}_{expression} with dissolve\n'
                    current_expr[speaker] = expression
                
                lines_code += f'    {var_name} "{text}"\n'
            else:
                # 未识别的角色，用旁白显示
                lines_code += f'    "{speaker}：{text}"\n'
        
        # 分支选项
        choices_code = ""
        choices_data = scene.get("choices", [])
        if choices_data:
            choices_code += "    menu:\n"
            for ch in choices_data:
                choice_text = ch.get("text", "...").replace('"', '\\"')
                target_label = f"label_{scene.get('scene_id', '')}_{_safe_var(ch.get('choice_id', 'unk'))}"
                choices_code += f'        "{choice_text}":\n'
                choices_code += f"            jump {target_label}\n"
            choices_code += "\n"
        
        # 角色退场
        character_hides = ""
        for char in scene_chars:
            name = char.get("name", "")
            if name not in characters:
                continue
            safe = _safe_name(name)
            character_hides += f'    hide {safe}_default\n'
        
        # 构建场景代码
        scene_code = SCENE_TEMPLATE.format(
            scene_id=scene.get("scene_id", ""),
            scene_title=scene.get("scene_title", ""),
            bg_name=bg_name,
            transition=transition,
            bgm_track=f"bgm_{bgm_mood}" if bgm_mood else "...",
            sfx_commands=sfx_commands,
            character_shows=character_shows,
            lines=lines_code,
            choices=choices_code,
            character_hides=character_hides,
        )
        
        flow_parts.append(scene_code)
    
    return "\n".join(flow_parts)


def _generate_asset_manifest(scenes: List[Dict], characters: Dict) -> str:
    """生成素材清单（Markdown）"""
    lines = [
        f"# 素材清单",
        f"",
        f"请将生成的素材文件放入对应的文件夹中。",
        f"",
        f"## 目录结构",
        f"```",
        f"游戏项目/game/",
        f"├── images/       ← 立绘、背景、CG放这里",
        f"└── audio/        ← BGM、音效放这里",
        f"```",
        f"",
        f"## 需要准备的图片",
        f"",
    ]
    
    # 背景
    seen_bgs = set()
    lines.append("### 背景图")
    lines.append("")
    for scene in scenes:
        loc = scene.get("location", "")
        if loc and loc not in seen_bgs:
            seen_bgs.add(loc)
            safe_loc = _safe_name(loc)
            lines.append(f"- `bg_{safe_loc}.png` — {loc}")
    lines.append("")
    
    # 立绘
    lines.append("### 角色立绘")
    lines.append("")
    for name, info in characters.items():
        safe_name = _safe_name(name)
        lines.append(f"#### {name} ({info['role']})")
        for expr in info["sprites"]:
            lines.append(f"- `{safe_name}_{expr}.png` — {expr}")
        lines.append("")
    
    # CG
    lines.append("### 事件CG")
    lines.append("")
    for scene in scenes:
        for cg in scene.get("cg_suggestions", []):
            cg_id = cg.get("cg_id", "")
            lines.append(
                f"- `{cg_id}.png` — {scene.get('scene_title', '')} - "
                f"{cg.get('description', '')[:50]}..."
            )
    lines.append("")
    
    # 音频
    lines.append("## 需要准备的音频")
    lines.append("")
    seen_moods = set()
    for scene in scenes:
        mood = scene.get("bgm_mood", "")
        if mood and mood not in seen_moods:
            seen_moods.add(mood)
            lines.append(f"- `bgm_{mood}.ogg` — BGM: {mood}")
    lines.append("")
    
    return "\n".join(lines)


def _copy_assets(asset_dir: str, images_dir: str, audio_dir: str):
    """复制素材文件到Ren'Py项目"""
    for root, dirs, files in os.walk(asset_dir):
        for f in files:
            src = os.path.join(root, f)
            ext = f.lower()
            if ext.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                dst = os.path.join(images_dir, f)
            elif ext.endswith(('.mp3', '.ogg', '.wav', '.opus')):
                dst = os.path.join(audio_dir, f)
            else:
                continue
            if not os.path.exists(dst):
                shutil.copy2(src, dst)


def _get_character_colors(count: int) -> List[str]:
    """生成角色颜色列表"""
    base_colors = [
        "#FF6B6B",  # 珊瑚红
        "#4ECDC4",  # 青绿
        "#45B7D1",  # 天蓝
        "#96CEB4",  # 薄荷绿
        "#FFEAA7",  # 暖黄
        "#DDA0DD",  # 梅紫
        "#FF8C69",  # 橙红
        "#87CEEB",  # 浅蓝
        "#F0E68C",  # 卡其
        "#DDA0DD",  # 紫
        "#98FB98",  # 浅绿
        "#FFB6C1",  # 粉红
    ]
    return base_colors[:max(count, 1)]


def _safe_name(name: str) -> str:
    """安全化文件名"""
    import re
    name = re.sub(r'[\\/*?:"<>|\s]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')


def _safe_var(name: str) -> str:
    """安全化变量名（Re'Py 变量名规则）"""
    import re
    # 只保留字母数字和下划线
    name = re.sub(r'[^\w]', '_', name)
    if name and name[0].isdigit():
        name = 'c_' + name
    if not name:
        name = 'unknown'
    return name


def _get_template_name(template_id: str) -> str:
    """获取模板中文名"""
    names = {
        "campus": "校园恋爱",
        "ancient_chinese": "古风仙侠",
        "sci_fi": "科幻未来",
        "mystery_horror": "悬疑惊悚",
        "fantasy": "异世界奇幻",
        "adult_romance": "成人恋爱",
    }
    return names.get(template_id, "通用")


def _generate_effect_defines(template_id: str) -> tuple:
    """生成特殊效果定义 (effect_code, is_adult)"""
    if template_id == "adult_romance":
        code = '''\
# ===== 角色立绘自适应缩放变换 =====
init:
    transform sprite_left:
        xalign 0.18 yalign 1.0
        zoom 0.48
        subpixel True

    transform sprite_center:
        xalign 0.5 yalign 1.0
        zoom 0.52
        subpixel True

    transform sprite_right:
        xalign 0.82 yalign 1.0
        zoom 0.48
        subpixel True

# 画面震动效果
init:
    transform shake_light:
        easein 0.05 xoffset -3
        easein 0.05 xoffset 3
        easein 0.05 xoffset -2
        easein 0.05 xoffset 2
        easein 0.05 xoffset 0

    transform shake_heavy:
        easein 0.03 xoffset -8
        easein 0.03 xoffset 8
        easein 0.03 xoffset -6
        easein 0.03 xoffset 6
        easein 0.03 xoffset -4
        easein 0.03 xoffset 4
        easein 0.03 xoffset -2
        easein 0.03 xoffset 2
        easein 0.03 xoffset 0

    transform heartbeat_shake:
        easein 0.12 xoffset -4
        easein 0.12 xoffset 4
        easein 0.12 xoffset -4
        easein 0.12 xoffset 4
        repeat

# CG解锁标记
init python:
    _cg_gallery = dict()
    def unlock_cg(cg_id):
        global _cg_gallery
        _cg_gallery[cg_id] = True
        renpy.notify("CG解锁: " + cg_id)
'''
        return (code, True)
    else:
        return ('''\
# ===== 角色立绘自适应缩放变换 =====
init:
    transform sprite_left:
        xalign 0.18 yalign 1.0
        zoom 0.48
        subpixel True

    transform sprite_center:
        xalign 0.5 yalign 1.0
        zoom 0.52
        subpixel True

    transform sprite_right:
        xalign 0.82 yalign 1.0
        zoom 0.48
        subpixel True
''', False)


def _generate_init_python(template_id: str, is_adult: bool) -> str:
    """生成init python初始化块"""
    if not is_adult:
        return "    pass"
    code = '''\
    # 成人模板 - 好感度系统
    affection_y1 = 0  # 女1好感度
    affection_y2 = 0  # 女2好感度
    affection_y3 = 0  # 女3好感度
    affection_max = 100

    # CG画廊数据
    _cg_gallery = dict()

    def add_affection(girl, amount):
        """增加好感度"""
        global affection_y1, affection_y2, affection_y3
        if girl == 1:
            affection_y1 = min(affection_y1 + amount, affection_max)
        elif girl == 2:
            affection_y2 = min(affection_y2 + amount, affection_max)
        elif girl == 3:
            affection_y3 = min(affection_y3 + amount, affection_max)
        renpy.notify("好感度 +" + str(amount))

    def get_affection(girl):
        if girl == 1:
            return affection_y1
        elif girl == 2:
            return affection_y2
        elif girl == 3:
            return affection_y3
        return 0

    def check_affection(girl, threshold):
        return get_affection(girl) >= threshold
'''
    return code


def _generate_affection_init(template_id: str) -> str:
    """生成好感度初始化代码"""
    if template_id == "adult_romance":
        return '''\
    # 好感度初始化
    $ affection_y1 = 0
    $ affection_y2 = 0
    $ affection_y3 = 0
'''
    return ""


def _generate_cg_gallery(template_id: str, scenes: List[Dict]) -> str:
    """生成CG画廊屏幕代码"""
    if template_id != "adult_romance":
        return ""
    
    # 收集所有CG
    cg_list = []
    for scene in scenes:
        for cg in scene.get("cg_suggestions", []):
            cg_id = cg.get("cg_id", "")
            if cg_id:
                cg_list.append(cg_id)
    
    if not cg_list:
        cg_list = ["cg_placeholder"]
    
    cg_buttons = "\n".join([
        f'        if "{cg}" in _cg_gallery:\n'
        f'            imagebutton idle "images/{cg}.png" action Show("cg_view", cg="{cg}")\n'
        f'        else:\n'
        f'            null'
        for cg in cg_list[:12]
    ])
    
    code = f'''\
screen cg_gallery():
    tag menu
    add "#1A0A10"
    vbox:
        xalign 0.5 yalign 0.05
        text "CG Gallery" size 36 color "#FF69B4" xalign 0.5
        text "解锁进度: [len(_cg_gallery)]/{len(cg_list)}" size 18 color "#999" xalign 0.5

    grid 4 3:
        xalign 0.5 yalign 0.5
        spacing 10
{cg_buttons}

    textbutton "返回" action Return() xalign 0.5 yalign 0.95

screen cg_view(cg):
    add "images/" + cg
    textbutton "关闭" action Hide("cg_view") xalign 0.98 yalign 0.02
'''
    return code


def _generate_affection_screen(template_id: str) -> str:
    """生成好感度查看画面"""
    if template_id != "adult_romance":
        return ""
    code = '''\
screen affection_status():
    tag menu
    add "#1A0A10"
    vbox:
        xalign 0.5 yalign 0.3
        spacing 20
        text "好感度状态" size 32 color "#FF69B4" xalign 0.5
        
        hbox:
            spacing 30
            xalign 0.5
            vbox:
                text "女主1" size 20 color "#FF6B6B"
                bar value affection_y1 range 100 xsize 200
                text "[affection_y1]/100" size 14 color "#999"
            vbox:
                text "女主2" size 20 color "#4ECDC4"
                bar value affection_y2 range 100 xsize 200
                text "[affection_y2]/100" size 14 color "#999"
            vbox:
                text "女主3" size 20 color "#DDA0DD"
                bar value affection_y3 range 100 xsize 200
                text "[affection_y3]/100" size 14 color "#999"

    textbutton "返回" action Return() xalign 0.5 yalign 0.9
'''
    return code
