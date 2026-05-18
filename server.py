"""
Galgame Studio - Web 服务器 (v0.2.1)
FastAPI + 静态文件服务
新增: 模板、i18n、预览、素材检测、标题/UI提示词、分支选项
修复: 字体/图片自适应/透明背景/预览持久化
"""

import os
import sys
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.novel_parser import parse_novel
from core.scene_analyzer import analyze_novel_to_scenes, generate_scene_summary
from core.prompt_generator import generate_all_prompts, STYLE_TEMPLATES
from core.renpy_packager import generate_renpy_project
from core.templates import get_all_templates, get_template, apply_template, PROJECT_TEMPLATES
from core.i18n import get_ui_strings, get_available_languages
from core.asset_scanner import scan_assets, scan_asset_directory
from core.preview_engine import build_preview_data, build_full_preview

app = FastAPI(title="Galgame Studio", version="0.2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_state = {
    "novel_data": None,
    "scenes": None,
    "prompts": None,
    "uploaded_novel_path": None,
    "project_dir": None,
    "template_id": None,
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# 启动时从磁盘恢复状态
_restore_scenes_path = os.path.join(OUTPUT_DIR, "scenes_analysis.json")
if os.path.exists(_restore_scenes_path):
    try:
        with open(_restore_scenes_path, "r", encoding="utf-8") as f:
            user_state["scenes"] = json.load(f)
    except Exception:
        pass


# ==================== 基础 API ====================

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.2.1"}


@app.post("/api/upload-novel")
async def upload_novel(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "未选择文件")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.txt', '.md', '.text']:
        raise HTTPException(400, "仅支持 .txt / .md 格式")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, file.filename)
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    try:
        novel_data = parse_novel(filepath)
    except Exception as e:
        raise HTTPException(500, f"解析小说失败: {str(e)}")
    
    user_state["novel_data"] = novel_data
    user_state["uploaded_novel_path"] = filepath
    user_state["scenes"] = None
    user_state["prompts"] = None
    
    return {
        "success": True,
        "novel": {
            "title": novel_data["title"],
            "filename": novel_data["filename"],
            "word_count": novel_data["word_count"],
            "chapter_count": len(novel_data["chapters"]),
            "preview": novel_data["full_text"][:500] + ("..." if len(novel_data["full_text"]) > 500 else ""),
        }
    }


@app.post("/api/analyze")
async def analyze_novel(
    api_key: str = Form(...),
    api_base: str = Form("https://api.openai.com/v1"),
    model: str = Form("gpt-4o"),
):
    if not user_state.get("novel_data"):
        raise HTTPException(400, "请先上传小说文件")
    
    novel_data = user_state["novel_data"]
    
    try:
        scenes = analyze_novel_to_scenes(
            novel_data=novel_data,
            api_key=api_key,
            api_base=api_base,
            model=model,
        )
    except Exception as e:
        raise HTTPException(500, f"场景分析失败: {str(e)}")
    
    if not scenes:
        raise HTTPException(500, "场景分析返回为空，请检查API配置")
    
    user_state["scenes"] = scenes
    
    scenes_path = os.path.join(OUTPUT_DIR, "scenes_analysis.json")
    with open(scenes_path, "w", encoding="utf-8") as f:
        json.dump(scenes, f, ensure_ascii=False, indent=2)
    
    # 检查有多少场景有分支选项
    choice_count = sum(1 for s in scenes if s.get("choices"))
    
    return {
        "success": True,
        "scene_count": len(scenes),
        "scenes": scenes,
        "summary": generate_scene_summary(scenes),
        "choice_scene_count": choice_count,
    }


@app.post("/api/generate-prompts")
async def generate_prompts(
    style: str = Form("anime_default"),
    template_id: str = Form("none"),
):
    if not user_state.get("scenes"):
        raise HTTPException(400, "请先完成场景分析")
    
    scenes = user_state["scenes"]
    
    # 如果选择了模板，应用模板BGM和UI覆盖
    if template_id and template_id != "none" and template_id in PROJECT_TEMPLATES:
        template = PROJECT_TEMPLATES[template_id]
        style = template.get("default_style", style)
        user_state["template_id"] = template_id
    
    try:
        prompts = generate_all_prompts(scenes, style)
    except Exception as e:
        raise HTTPException(500, f"提示词生成失败: {str(e)}")
    
    # 如果是模板，注入模板专属UI提示词
    if user_state.get("template_id") and user_state["template_id"] != "none":
        template = PROJECT_TEMPLATES.get(user_state["template_id"])
        if template and "ui_prompts" in template:
            prompts["ui"]["title_screen"]["prompt"] = template["ui_prompts"]["title_bg"]
            prompts["ui"]["textbox"]["prompt"] = template["ui_prompts"]["textbox"]
            prompts["ui"]["choice_buttons"]["prompt"] = template["ui_prompts"]["choice_buttons"]
    
    user_state["prompts"] = prompts
    
    prompts_path = os.path.join(OUTPUT_DIR, "prompts_data.json")
    with open(prompts_path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    
    return {
        "success": True,
        "prompts": prompts,
        "style_name": STYLE_TEMPLATES.get(style, {}).get("name", style),
    }


@app.post("/api/export-prompts")
async def export_prompts():
    if not user_state.get("prompts"):
        raise HTTPException(400, "请先生成提示词")
    
    prompts = user_state["prompts"]
    md_content = _build_prompts_markdown(prompts)
    
    export_path = os.path.join(OUTPUT_DIR, "提示词清单.md")
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return {
        "success": True,
        "download_path": export_path,
        "filename": "提示词清单.md",
    }


@app.post("/api/pack")
async def pack_project(project_name: str = Form("MyGame")):
    if not user_state.get("scenes"):
        raise HTTPException(400, "请先完成场景分析")
    
    scenes = user_state["scenes"]
    novel_data = user_state.get("novel_data", {})
    
    try:
        project_dir = generate_renpy_project(
            scenes=scenes,
            novel_title=novel_data.get("title", project_name),
            output_dir=OUTPUT_DIR,
            project_name=project_name,
            template_id=user_state.get("template_id", "none"),
        )
    except Exception as e:
        raise HTTPException(500, f"项目打包失败: {str(e)}")
    
    user_state["project_dir"] = project_dir
    
    # 自动归类已导入的素材到对应子目录
    staging = os.path.join(OUTPUT_DIR, "assets_staging")
    if os.path.exists(staging):
        _auto_sort_assets_to_project(staging, project_dir)
    
    return {
        "success": True,
        "project_dir": project_dir,
        "message": f"Ren'Py项目已生成到: {project_dir}",
    }


# ==================== 模板 API ====================

@app.get("/api/templates")
async def get_templates():
    from fastapi.responses import Response
    import json as _json
    data = {"templates": get_all_templates()}
    return Response(
        content=_json.dumps(data, ensure_ascii=False),
        media_type="application/json; charset=utf-8"
    )


@app.get("/api/template/{template_id}")
async def get_template_detail(template_id: str):
    try:
        return {"template": get_template(template_id)}
    except Exception:
        raise HTTPException(404, "模板不存在")


@app.post("/api/apply-template")
async def apply_project_template(template_id: str = Form(...)):
    if not user_state.get("scenes"):
        raise HTTPException(400, "请先完成场景分析")
    
    try:
        result = apply_template(user_state["scenes"], template_id)
        user_state["template_id"] = template_id
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/auto-sort")
async def auto_sort_assets(project_name: str = Form("MyGame")):
    """
    一键自动归类素材到 Ren'Py 项目
    扫描 assets_staging 目录，智能映射到 game/ 下的 bg/ characters/ cg/ ui/ audio/
    """
    staging = os.path.join(OUTPUT_DIR, "assets_staging")
    if not os.path.exists(staging):
        return {"success": True, "message": "暂存区为空，请先导入素材", "sorted": 0, "details": []}
    
    # 自动归类规则
    TYPE_MAP = {
        "background": "bg",
        "character_sprite": "characters",
        "cg": "cg",
        "ui": "ui",
        "bgm": "audio",
        "sfx": "audio",
        "voice": "audio",
    }
    
    # 寻找已打包的项目
    target_project = None
    for name in os.listdir(OUTPUT_DIR):
        d = os.path.join(OUTPUT_DIR, name)
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "game")):
            if name == project_name or not target_project:
                target_project = d
            if name == project_name:
                break
    
    if not target_project:
        # 没有已打包项目，直接在 staging 下创建分类预览
        details = []
        for root, dirs, files in os.walk(staging):
            for f in files:
                rel = os.path.relpath(root, staging)
                category = TYPE_MAP.get(rel, "other")
                src = os.path.join(root, f)
                details.append({
                    "filename": f,
                    "category": category,
                    "source": rel,
                    "status": "pending"
                })
        return {
            "success": True,
            "message": f"暂存区有 {len(details)} 个文件。请先打包项目后再归类。",
            "sorted": 0,
            "details": details,
            "target": None
        }
    
    # 创建目标子目录
    game_dir = os.path.join(target_project, "game")
    target_dirs = {
        "background": os.path.join(game_dir, "bg"),
        "character_sprite": os.path.join(game_dir, "characters"),
        "cg": os.path.join(game_dir, "cg"),
        "ui": os.path.join(game_dir, "images"),
        "bgm": os.path.join(game_dir, "audio"),
        "sfx": os.path.join(game_dir, "audio"),
        "voice": os.path.join(game_dir, "audio"),
    }
    for d in target_dirs.values():
        os.makedirs(d, exist_ok=True)
    
    # 执行归类
    sorted_count = 0
    details = []
    
    for root, dirs, files in os.walk(staging):
        rel = os.path.relpath(root, staging)
        if rel == ".":
            target_dir = os.path.join(game_dir, "images")
        else:
            target_dir = target_dirs.get(rel, os.path.join(game_dir, "images"))
        
        for f in files:
            src = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            
            # 图片和音频分别处理
            if ext not in (".png", ".jpg", ".jpeg", ".webp", ".mp3", ".ogg", ".wav", ".opus"):
                continue
            
            dest = os.path.join(target_dir, f)
            overwritten = os.path.exists(dest)
            shutil.copy2(src, dest)
            
            category = TYPE_MAP.get(rel, "other")
            details.append({
                "filename": f,
                "category": category,
                "source": rel,
                "destination": str(Path(dest).relative_to(game_dir)),
                "overwritten": overwritten,
            })
            sorted_count += 1
    
    user_state["project_dir"] = target_project
    
    return {
        "success": True,
        "message": f"已归类 {sorted_count} 个文件到项目",
        "sorted": sorted_count,
        "project_dir": target_project,
        "details": details,
        "tree": _build_file_tree(target_project),
    }


def _build_file_tree(project_dir: str) -> list:
    """构建素材目录树（仅bg/characters/cg/ui/audio）"""
    game_dir = os.path.join(project_dir, "game")
    tree = []
    for sub in ["bg", "characters", "cg", "images", "audio"]:
        sub_path = os.path.join(game_dir, sub)
        if os.path.exists(sub_path):
            files = [f for f in os.listdir(sub_path) if os.path.isfile(os.path.join(sub_path, f))]
            tree.append({"dir": sub, "count": len(files), "files": sorted(files)})
    return tree


@app.post("/api/clear-staging")
async def clear_staging():
    """清理素材暂存目录"""
    staging = os.path.join(OUTPUT_DIR, "assets_staging")
    if os.path.exists(staging):
        shutil.rmtree(staging)
    user_state["has_assets"] = False
    return {"success": True, "message": "素材暂存已清理"}


# ==================== i18n API ====================

@app.get("/api/i18n")
async def get_i18n(lang: str = Query("zh")):
    return {
        "strings": get_ui_strings(lang),
        "languages": get_available_languages(),
    }


# ==================== 预览 API ====================

@app.get("/api/preview")
async def get_preview(scene_index: int = Query(0)):
    scenes = _get_scenes()
    if not scenes:
        raise HTTPException(400, "请先完成场景分析")
    
    data = build_preview_data(scenes, scene_index)
    return {"success": True, "preview": data}


@app.get("/api/preview/all")
async def get_full_preview():
    scenes = _get_scenes()
    if not scenes:
        raise HTTPException(400, "请先完成场景分析")
    
    data = build_full_preview(scenes)
    return {"success": True, "data": data}


def _get_scenes():
    """获取场景数据 — 先从内存读，再从磁盘读"""
    if user_state.get("scenes"):
        return user_state["scenes"]
    # 回退：从磁盘加载
    scenes_path = os.path.join(OUTPUT_DIR, "scenes_analysis.json")
    if os.path.exists(scenes_path):
        try:
            with open(scenes_path, "r", encoding="utf-8") as f:
                scenes = json.load(f)
            user_state["scenes"] = scenes  # 缓存到内存
            return scenes
        except Exception:
            pass
    return None


# ==================== 素材扫描 API ====================

@app.get("/api/scan-assets")
async def api_scan_assets():
    if not user_state.get("project_dir") and not _get_scenes():
        raise HTTPException(400, "请先打包项目或完成场景分析")
    
    project_dir = user_state.get("project_dir", "")
    scenes = _get_scenes()
    
    if not project_dir and scenes:
        # 尝试找到已打包的项目
        for name in os.listdir(OUTPUT_DIR):
            d = os.path.join(OUTPUT_DIR, name)
            if os.path.isdir(d) and os.path.exists(os.path.join(d, "game")):
                project_dir = d
                break
    
    if not project_dir:
        raise HTTPException(400, "请先打包项目")
    
    result = scan_assets(project_dir, scenes)
    return {"success": True, "scan": result}


@app.post("/api/scan-directory")
async def api_scan_directory(path: str = Form(...)):
    if not os.path.exists(path):
        raise HTTPException(400, "目录不存在")
    
    result = scan_asset_directory(path)
    return {"success": True, "scan": result}


@app.post("/api/import-asset")
async def import_asset(
    file: UploadFile = File(...),
    asset_type: str = Form(...),
    asset_label: str = Form(...),
    filename: str = Form(...),
):
    """
    导入单个素材文件，自动归类和命名
    asset_type: character_sprite | background | cg | bgm | sfx | ui
    asset_label: 如 "林川_shy" 或 "bg_图书馆"
    filename: 目标文件名（已规范化）
    """
    if not filename:
        raise HTTPException(400, "文件名不能为空")
    
    # 安全化文件名，去除路径遍历危险字符
    import re as _re
    filename = _re.sub(r'[\\/*?:"<>|]', '_', filename)
    filename = _re.sub(r'\.\.', '_', filename)
    
    # 素材目录
    assets_dir = os.path.join(OUTPUT_DIR, "assets_staging")
    type_dir = os.path.join(assets_dir, asset_type)
    os.makedirs(type_dir, exist_ok=True)
    
    # 确保扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.webp', '.mp3', '.ogg', '.wav', '.opus']:
        ext = '.png' if asset_type in ('character_sprite', 'background', 'cg', 'ui') else '.ogg'
    
    target = os.path.join(type_dir, filename)
    if not target.endswith(ext):
        target += ext
    
    # 检查文件是否已存在
    overwritten = os.path.exists(target)
    
    content = await file.read()
    with open(target, "wb") as f:
        f.write(content)
    
    user_state["has_assets"] = True
    
    return {
        "success": True,
        "asset_type": asset_type,
        "asset_label": asset_label,
        "filename": os.path.basename(target),
        "path": target,
        "overwritten": overwritten,
    }


@app.get("/api/imported-assets")
async def get_imported_assets():
    """获取已导入的素材列表"""
    assets_dir = os.path.join(OUTPUT_DIR, "assets_staging")
    if not os.path.exists(assets_dir):
        return {"success": True, "assets": {}}
    
    result = {}
    for asset_type in os.listdir(assets_dir):
        type_dir = os.path.join(assets_dir, asset_type)
        if os.path.isdir(type_dir):
            result[asset_type] = os.listdir(type_dir)
    
    return {"success": True, "assets": result}


# ==================== 其他 ====================

@app.get("/api/export-scenes")
async def export_scenes_json():
    if not user_state.get("scenes"):
        raise HTTPException(400, "无可用数据")
    return JSONResponse(user_state["scenes"])


@app.get("/api/styles")
async def get_styles():
    return {
        "styles": [
            {"id": k, "name": v["name"]} 
            for k, v in STYLE_TEMPLATES.items()
        ]
    }


@app.post("/api/reset")
async def reset():
    for key in user_state:
        user_state[key] = None
    return {"success": True}


def _build_prompts_markdown(prompts: dict) -> str:
    """构建提示词的Markdown导出（含UI）"""
    md = []
    md.append(f"# Galgame Studio - AI提示词清单")
    md.append(f"画风: {prompts.get('style_name', '')}")
    md.append("")
    
    summary = prompts.get("scene_summary", {})
    md.append("## 📊 场景统计")
    md.append(f"- 总场景数: {summary.get('total_scenes', 0)}")
    md.append(f"- 总台词数: {summary.get('total_lines', 0)}")
    md.append(f"- 角色数: {summary.get('character_count', 0)}")
    md.append("")
    
    # 角色立绘
    md.append("---\n## 🎨 角色立绘提示词\n")
    for char in prompts.get("characters", []):
        md.append(f"### {char['character_name']} ({char['role']})")
        md.append(f"外观: {char['appearance']}\n")
        for sprite in char["sprites"]:
            md.append(f"#### {sprite['expression']}")
            md.append(f"```\n{sprite['prompt']}\n```")
            md.append(f"文件名: `{sprite['filename_template']}`\n")
    
    # 背景
    md.append("---\n## 🖼️ 背景提示词\n")
    for bg in prompts.get("backgrounds", []):
        md.append(f"### {bg['location']}")
        md.append(f"```\n{bg['prompt']}\n```")
        md.append(f"文件名: `{bg['filename_template']}`\n")
    
    # CG
    if prompts.get("cgs"):
        md.append("---\n## 🎬 事件CG提示词\n")
        for cg in prompts["cgs"]:
            md.append(f"### {cg['cg_id']} — {cg['scene_title']}")
            md.append(f"```\n{cg['prompt']}\n```\n")
    
    # UI
    if prompts.get("ui"):
        ui = prompts["ui"]
        md.append("---\n## 🖥️ 标题画面/UI提示词\n")
        md.append(ui.get("guide", ""))
        md.append(f"\n### 标题画面背景\n```\n{ui['title_screen']['prompt']}\n```")
        md.append(f"\n### 对话框\n```\n{ui['textbox']['prompt']}\n```")
        md.append(f"\n### 选项按钮\n```\n{ui['choice_buttons']['prompt']}\n```")
        md.append(f"\n### 名字框\n```\n{ui['namebox']['prompt']}\n```")
    
    # BGM
    md.append("---\n## 🎵 BGM制作指南\n")
    bgm = prompts.get("bgm", {})
    md.append(bgm.get("guide", ""))
    for track in bgm.get("bgm_tracks", []):
        md.append(f"### {track['style_cn']} ({track['mood']})")
        md.append(f"- Suno风格: `{track['suno_genre']}`")
        md.append(f"- 提示词: `{track['ai_prompt']}`\n")
    
    # 配音
    md.append("---\n## 🎙️ 配音制作指南\n")
    voice = prompts.get("voice", {})
    md.append(voice.get("guide", ""))
    for char in voice.get("characters", []):
        md.append(f"### {char['name']} ({char['role']})")
        md.append(f"- 台词量: {char['total_lines']}句\n")
    
    return "\n".join(md)


# ==================== 静态文件 ====================

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 素材文件静态服务 (预览用)
assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "assets_staging")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Galgame Studio API", "docs": "/docs"}


@app.get("/preview")
async def preview_page():
    """预览模式专用页面"""
    preview_path = os.path.join(static_dir, "preview.html")
    if os.path.exists(preview_path):
        return FileResponse(preview_path)
    return {"message": "预览页面尚未生成"}


def _auto_sort_assets_to_project(staging: str, project_dir: str):
    """把 assets_staging 里的素材自动归类到 Ren'Py 项目子目录"""
    game_dir = os.path.join(project_dir, "game")
    
    TYPE_TO_DIR = {
        "background": "bg",
        "character_sprite": "characters",
        "cg": "cg",
        "ui": "images",
        "bgm": "audio",
        "sfx": "audio",
        "voice": "audio",
    }
    
    for sub in ["bg", "characters", "cg", "images", "audio"]:
        os.makedirs(os.path.join(game_dir, sub), exist_ok=True)
    
    for root, dirs, files in os.walk(staging):
        rel = os.path.relpath(root, staging)
        target_sub = TYPE_TO_DIR.get(rel, "images")
        target_dir = os.path.join(game_dir, target_sub)
        
        for f in files:
            src = os.path.join(root, f)
            ext = f.lower()
            if ext not in (".png", ".jpg", ".jpeg", ".webp", ".mp3", ".ogg", ".wav", ".opus"):
                continue
            dest = os.path.join(target_dir, f)
            if not os.path.exists(dest):
                shutil.copy2(src, dest)


def start_server(host: str = "127.0.0.1", port: int = 8888):
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server()
