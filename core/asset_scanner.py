"""
素材自动导入检测器
扫描项目目录，检测已有素材，给出缺失清单
"""

import os
import json
from typing import List, Dict


def scan_assets(project_dir: str, scenes: List[Dict] = None) -> Dict:
    """
    扫描项目素材目录，检测已有和缺失的素材
    
    Returns:
        {
            "total_required": int,
            "present": int,
            "missing": int,
            "completion_pct": float,
            "images": {
                "backgrounds": [{"name": str, "status": "present"|"missing"}],
                "sprites": [...],
                "cgs": [...],
            },
            "audio": {
                "bgm": [...],
                "sfx": [...],
            },
            "missing_list": [str, ...],
        }
    """
    game_dir = os.path.join(project_dir, "game")
    images_dir = os.path.join(game_dir, "images")
    audio_dir = os.path.join(game_dir, "audio")
    
    result = {
        "total_required": 0,
        "present": 0,
        "missing": 0,
        "completion_pct": 0.0,
        "images": {"backgrounds": [], "sprites": [], "cgs": []},
        "audio": {"bgm": [], "sfx": []},
        "missing_list": [],
    }
    
    # 扫描已存在的文件
    existing_images = set()
    existing_audio = set()
    
    if os.path.exists(images_dir):
        for f in os.listdir(images_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                existing_images.add(f)
    
    if os.path.exists(audio_dir):
        for f in os.listdir(audio_dir):
            if f.lower().endswith(('.mp3', '.ogg', '.wav', '.opus')):
                existing_audio.add(f)
    
    if not scenes:
        # 尝试从scenes_data.json读取
        json_path = os.path.join(project_dir, "scenes_data.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                scenes = json.load(f)
    
    if not scenes:
        return result
    
    # 统计需要的素材
    from .renpy_packager import _safe_name, _collect_characters
    
    characters = _collect_characters(scenes)
    
    # 背景图
    seen_bgs = set()
    for scene in scenes:
        loc = scene.get("location", "")
        if loc and loc not in seen_bgs:
            seen_bgs.add(loc)
            fname = f"bg_{_safe_name(loc)}.png"
            status = "present" if fname in existing_images else "missing"
            item = {"name": f"bg_{_safe_name(loc)}.png", "location": loc, "status": status}
            result["images"]["backgrounds"].append(item)
            result["total_required"] += 1
            if status == "present":
                result["present"] += 1
            else:
                result["missing"] += 1
                result["missing_list"].append(f"背景: {loc}")
    
    # 角色立绘
    for name, info in characters.items():
        safe_name = _safe_name(name)
        for expr in info["sprites"]:
            fname = f"{safe_name}_{expr}.png"
            status = "present" if fname in existing_images else "missing"
            item = {
                "name": fname,
                "character": name,
                "expression": expr,
                "status": status,
            }
            result["images"]["sprites"].append(item)
            result["total_required"] += 1
            if status == "present":
                result["present"] += 1
            else:
                result["missing"] += 1
                result["missing_list"].append(f"立绘: {name}_{expr}")
    
    # CG
    for scene in scenes:
        for cg in scene.get("cg_suggestions", []):
            cg_id = cg.get("cg_id", "")
            if cg_id:
                fname = f"{cg_id}.png"
                status = "present" if fname in existing_images else "missing"
                item = {
                    "name": fname,
                    "scene": scene.get("scene_title", ""),
                    "status": status,
                }
                result["images"]["cgs"].append(item)
                result["total_required"] += 1
                if status == "present":
                    result["present"] += 1
                else:
                    result["missing"] += 1
                    result["missing_list"].append(f"CG: {cg_id}")
    
    # BGM
    seen_moods = set()
    for scene in scenes:
        mood = scene.get("bgm_mood", "")
        if mood and mood not in seen_moods:
            seen_moods.add(mood)
            fname = f"bgm_{mood}.ogg"
            status = "present" if fname in existing_audio else "missing"
            item = {"name": fname, "mood": mood, "status": status}
            result["audio"]["bgm"].append(item)
            result["total_required"] += 1
            if status == "present":
                result["present"] += 1
            else:
                result["missing"] += 1
                result["missing_list"].append(f"BGM: {mood}")
    
    # SFX
    for scene in scenes:
        for sfx in scene.get("sfx", []):
            fname = f"{sfx}.ogg"
            status = "present" if fname in existing_audio else "missing"
            item = {"name": fname, "sfx": sfx, "status": status}
            result["audio"]["sfx"].append(item)
            result["total_required"] += 1
            if status == "present":
                result["present"] += 1
            else:
                result["missing"] += 1
                result["missing_list"].append(f"SFX: {sfx}")
    
    if result["total_required"] > 0:
        result["completion_pct"] = round(
            result["present"] / result["total_required"] * 100, 1
        )
    
    return result


def scan_asset_directory(asset_dir: str) -> Dict:
    """
    扫描任意目录中的素材文件
    
    Returns:
        {
            "images": [{"name": str, "size_kb": float}],
            "audio": [...],
            "total_images": int,
            "total_audio": int,
        }
    """
    result = {"images": [], "audio": [], "total_images": 0, "total_audio": 0}
    
    if not os.path.exists(asset_dir):
        return result
    
    for root, dirs, files in os.walk(asset_dir):
        for f in files:
            filepath = os.path.join(root, f)
            size = os.path.getsize(filepath) / 1024
            ext = f.lower()
            
            if ext.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                result["images"].append({
                    "name": f,
                    "path": filepath,
                    "size_kb": round(size, 1),
                })
                result["total_images"] += 1
            elif ext.endswith(('.mp3', '.ogg', '.wav', '.opus', '.flac')):
                result["audio"].append({
                    "name": f,
                    "path": filepath,
                    "size_kb": round(size, 1),
                })
                result["total_audio"] += 1
    
    return result
