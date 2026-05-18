"""
预览引擎
将场景数据转换为浏览器可播放的格式
不装Ren'Py也能在浏览器里预览演出效果
"""

import os
from typing import List, Dict


# assets_staging 目录 (与 server.py 中的 /assets 静态挂载对应)
def _get_assets_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "assets_staging")


def _check_asset_url(subdir: str, filename: str) -> str:
    """检查素材文件是否存在，返回URL或空字符串"""
    assets_dir = _get_assets_dir()
    full_path = os.path.join(assets_dir, subdir, filename)
    if os.path.exists(full_path):
        return f"/assets/{subdir}/{filename}"
    return ""


def _safe_filename(s: str) -> str:
    """安全化文件名"""
    import re
    return re.sub(r'[\\/*?:"<>|]', '_', s)


def build_preview_data(
    scenes: List[Dict],
    current_scene_index: int = 0,
    characters: Dict = None,
) -> Dict:
    """
    构建预览所需的数据
    
    返回前端可以直接消费的预览数据结构
    """
    if not scenes:
        return {"scenes": [], "current": None}
    
    if characters is None:
        characters = {}
        for scene in scenes:
            for char in scene.get("characters_in_scene", []):
                name = char.get("name", "")
                if name not in characters:
                    characters[name] = {
                        "name": name,
                        "role": char.get("role", ""),
                        "appearance": char.get("appearance", ""),
                        "sprites": [s for s in char.get("sprites_needed", ["default"]) if s],
                    }
    
    current_scene = scenes[current_scene_index] if 0 <= current_scene_index < len(scenes) else scenes[0]
    
    return {
        "scenes": scenes,
        "total_scenes": len(scenes),
        "current_index": current_scene_index,
        "current": _build_scene_preview(current_scene, characters),
        "characters": characters,
    }


def _build_scene_preview(scene: Dict, characters: Dict) -> Dict:
    """构建单个场景的预览数据"""
    
    # 当前场景的角色
    chars_in_scene = {}
    for char in scene.get("characters_in_scene", []):
        name = char.get("name", "")
        if name and name in characters:
            c_info = characters[name]
            sprites = [s for s in c_info.get("sprites", ["default"]) if s]
            safe_name = _safe_filename(name)
            
            # 检查每个表情的实际图片是否存在
            sprite_urls = {}
            for expr in sprites:
                url = _check_asset_url("character_sprite", f"{safe_name}_{expr}.png")
                if url:
                    sprite_urls[expr] = url
            # default 的备选
            if "default" not in sprite_urls:
                url = _check_asset_url("character_sprite", f"{safe_name}_default.png")
                if url:
                    sprite_urls["default"] = url
            
            chars_in_scene[name] = {
                "name": name,
                "appearance": char.get("appearance", c_info.get("appearance", "")),
                "role": c_info.get("role", ""),
                "sprites": sprites,
                "current_expression": "default",
                "sprite_urls": sprite_urls,
                "has_asset": len(sprite_urls) > 0,
            }
    
    # 背景图检查
    bg_url = ""
    loc = scene.get("location", "")
    if loc:
        safe_loc = _safe_filename(loc)
        bg_url = _check_asset_url("background", f"bg_{safe_loc}.png")
    
    # 分离台词和说话人
    lines = []
    for line in scene.get("lines", []):
        speaker = line.get("speaker", "")
        text = line.get("text", "")
        line_type = line.get("type", "narration")
        expression = line.get("expression")
        if not expression or not isinstance(expression, str):
            expression = "default"
        
        lines.append({
            "speaker": speaker,
            "text": text,
            "type": line_type,
            "expression": expression,
        })
    
    return {
        "scene_id": scene.get("scene_id", ""),
        "scene_title": scene.get("scene_title", ""),
        "location": loc,
        "time": scene.get("time", ""),
        "mood": scene.get("mood", ""),
        "bg_description": scene.get("bg_description", ""),
        "bgm_mood": scene.get("bgm_mood", ""),
        "transition": scene.get("transition", "dissolve"),
        "characters_in_scene": chars_in_scene,
        "lines": lines,
        "choices": scene.get("choices", []),
        "has_choices": bool(scene.get("choices")),
        "bg_url": bg_url,
        "prev_scene_index": max(0, int(scene.get("scene_id", "scene_000").split("_")[-1]) - 2),
        "next_scene_index": int(scene.get("scene_id", "scene_000").split("_")[-1]),
    }


def build_full_preview(scenes: List[Dict]) -> Dict:
    """
    构建完整预览数据，包含所有场景的索引和导航
    """
    if not scenes:
        return {"scenes": [], "total_lines": 0}
    
    preview_scenes = []
    total_lines = 0
    
    for i, scene in enumerate(scenes):
        preview = {
            "index": i,
            "scene_id": scene.get("scene_id", f"scene_{i+1:03d}"),
            "scene_title": scene.get("scene_title", ""),
            "location": scene.get("location", ""),
            "time": scene.get("time", ""),
            "mood": scene.get("mood", ""),
            "bg_description": scene.get("bg_description", ""),
            "bgm_mood": scene.get("bgm_mood", ""),
            "has_choices": bool(scene.get("choices")),
            "choices": scene.get("choices", []),
            "line_count": len(scene.get("lines", [])),
            "characters": [
                c.get("name", "") for c in scene.get("characters_in_scene", [])
            ],
        }
        total_lines += preview["line_count"]
        preview_scenes.append(preview)
    
    return {
        "scenes": preview_scenes,
        "total_scenes": len(preview_scenes),
        "total_lines": total_lines,
    }
