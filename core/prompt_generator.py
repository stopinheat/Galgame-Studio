"""
提示词生成器
根据场景分析结果生成AI绘图、BGM、配音的提示词和操作指南
"""

from typing import List, Dict


# === 绘图风格模板 ===
STYLE_TEMPLATES = {
    "anime_default": {
        "name": "日系动漫标准",
        "base_prompt": "masterpiece, best quality, anime style, highly detailed, "
                       "soft lighting, clean linework, vibrant colors, 2D illustration",
        "negative": "lowres, bad anatomy, bad hands, text, error, missing fingers, "
                    "extra digit, fewer digits, cropped, worst quality, low quality, "
                    "normal quality, jpeg artifacts, signature, watermark, username, blurry",
    },
    "anime_realistic": {
        "name": "日系写实",
        "base_prompt": "masterpiece, best quality, anime style, semi-realistic, "
                       "detailed eyes, cinematic lighting, photorealistic render, 8k",
        "negative": "lowres, bad anatomy, bad hands, text, cropped, worst quality, "
                    "low quality, normal quality, jpeg artifacts, signature, watermark",
    },
    "manga_style": {
        "name": "黑白漫画",
        "base_prompt": "masterpiece, best quality, manga style, black and white, "
                       "hatching, screentone, pen and ink, comic art",
        "negative": "color, lowres, bad anatomy, bad hands, text, cropped, worst quality, "
                    "signature, watermark",
    },
    "chinese_ink": {
        "name": "水墨古风",
        "base_prompt": "masterpiece, best quality, Chinese ink painting style, "
                       "traditional Chinese art, ink wash, watercolor, elegant, poetic atmosphere",
        "negative": "lowres, bad anatomy, 3D, photorealistic, western style, "
                    "signature, watermark, text",
    },
    "light_novel": {
        "name": "轻小说插画风",
        "base_prompt": "masterpiece, best quality, light novel illustration style, "
                       "soft colors, ethereal, detailed background, beautiful lighting, "
                       "character focus, anime art, visual novel cg",
        "negative": "lowres, bad anatomy, bad hands, text, error, missing fingers, "
                    "cropped, worst quality, low quality, jpeg artifacts, signature, watermark",
    },
}


def generate_character_prompts(
    scenes: List[Dict],
    style: str = "anime_default",
) -> List[Dict]:
    """
    生成角色立绘的AI绘图提示词
    
    返回每个角色的完整立绘提示词，包含不同表情差分
    """
    style_cfg = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["anime_default"])
    
    # 收集所有角色及其信息
    characters = {}
    for scene in scenes:
        for char in scene.get("characters_in_scene", []):
            name = char.get("name", "未知角色")
            if name not in characters:
                characters[name] = {
                    "name": name,
                    "role": char.get("role", "角色"),
                    "appearance": char.get("appearance", ""),
                    "sprites_needed": set(),
                    "first_appearance_scene": scene.get("scene_id", ""),
                }
            characters[name]["sprites_needed"].update(
                s for s in char.get("sprites_needed", ["default"]) if s
            )
    
    # 为每个角色的每个表情生成提示词（过滤掉None）
    result = []
    for name, info in characters.items():
        sprites = []
        for expr in sorted(e for e in info["sprites_needed"] if e):
            prompt = _build_sprite_prompt(
                name, info["appearance"], expr, style_cfg
            )
            sprites.append({
                "expression": expr,
                "filename_template": f"{name}_{expr}.png",
                "prompt": prompt["positive"],
                "negative_prompt": prompt["negative"],
                "notes": prompt.get("notes", ""),
            })
        
        result.append({
            "character_name": name,
            "role": info["role"],
            "appearance": info["appearance"],
            "first_scene": info["first_appearance_scene"],
            "total_sprites": len(sprites),
            "sprites": sprites,
        })
    
    return result


def _build_sprite_prompt(
    name: str,
    appearance: str,
    expression: str,
    style_cfg: Dict,
) -> Dict:
    """为单个角色立绘生成提示词"""
    # 表情映射
    expression_map = {
        "default": "neutral expression, natural standing pose, looking at viewer",
        "happy": "happy expression, smiling, bright eyes, cheerful",
        "sad": "sad expression, slightly crying or sorrowful, drooping eyebrows",
        "angry": "angry expression, furrowed brows, clenched teeth or pouting",
        "shy": "shy expression, blushing cheeks, looking away, embarrassed, flustered",
        "surprised": "surprised expression, wide eyes, slightly open mouth",
        "serious": "serious expression, determined look, furrowed brows",
        "flustered": "flustered expression, panicked, blushing heavily, sweating",
        "gentle": "gentle smile, kind eyes, warm expression",
        "crying": "crying expression, tears streaming, emotional",
        "evil": "evil smirk, sinister eyes, dark expression",
        "pout": "pouting expression, slightly annoyed, cute angry",
        "thinking": "thoughtful expression, hand on chin, looking upward",
    }
    
    expr_desc = expression_map.get(expression, f"{expression} expression")
    
    positive = (
        f"{style_cfg['base_prompt']}, "
        f"1girl, solo, character design sheet, {appearance}, "
        f"{expr_desc}, "
        f"full body portrait, standing pose, solid white background, "
        f"visual novel sprite, character turnaround, sprite sheet style, "
        f"uniform lighting, front facing, simple background"
    )
    
    return {
        "positive": positive,
        "negative": style_cfg["negative"],
        "notes": (
            f"角色「{name}」的{expression}表情立绘。\n"
            f"⚠️ 重要：生成后请用背景去除工具（如 remove.bg 或 Photoshop）"
            f"去除背景，导出为透明背景 PNG。\n"
            f"如果立绘自带背景，在 Ren'Py 中会遮挡背景图。"
        )
    }


def generate_background_prompts(
    scenes: List[Dict],
    style: str = "anime_default",
) -> List[Dict]:
    """
    生成场景背景的AI绘图提示词
    自动去重相同/相似的场景
    """
    style_cfg = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["anime_default"])
    
    # 收集所有场景，按location去重
    seen_locations = {}
    bg_prompts = []
    
    for scene in scenes:
        loc = scene.get("location", "未知地点")
        bg_desc = scene.get("bg_description", "")
        
        location_key = loc.strip()
        
        if location_key not in seen_locations:
            seen_locations[location_key] = True
            
            positive = (
                f"{style_cfg['base_prompt']}, "
                f"background art, scenery, {bg_desc}, "
                f"no humans, no characters, detailed background, "
                f"architectural details, atmospheric perspective, wide shot"
            )
            
            bg_prompts.append({
                "location": loc,
                "filename_template": f"bg_{_safe_filename(loc)}.png",
                "used_in_scenes": [scene["scene_id"]],
                "prompt": positive,
                "negative_prompt": f"{style_cfg['negative']}, character, person, human, girl, boy",
                "mood": scene.get("mood", ""),
            })
        else:
            # 添加引用
            for bg in bg_prompts:
                if bg["location"] == loc:
                    bg["used_in_scenes"].append(scene["scene_id"])
                    break
    
    return bg_prompts


def generate_cg_prompts(
    scenes: List[Dict],
    style: str = "anime_default",
) -> List[Dict]:
    """
    生成事件CG的AI绘图提示词
    """
    style_cfg = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["anime_default"])
    
    cg_prompts = []
    for scene in scenes:
        for cg in scene.get("cg_suggestions", []):
            # 收集场景中的角色信息
            chars_in_scene = scene.get("characters_in_scene", [])
            char_appearances = ", ".join([
                f"{c['name']}({c.get('appearance', '')})" 
                for c in chars_in_scene[:3]  # 最多3个角色
            ])
            
            positive = (
                f"{style_cfg['base_prompt']}, "
                f"illustration, event CG, visual novel cg, "
                f"{cg.get('description', '')}, "
                f"characters: {char_appearances}, "
                f"background: {scene.get('bg_description', '')}, "
                f"dramatic composition, cinematic angle, story illustration"
            )
            
            cg_prompts.append({
                "cg_id": cg.get("cg_id", f"cg_{len(cg_prompts)+1:03d}"),
                "scene_id": scene["scene_id"],
                "scene_title": scene.get("scene_title", ""),
                "description": cg.get("description", ""),
                "filename_template": f"cg_{cg.get('cg_id', '')}.png",
                "prompt": positive,
                "negative_prompt": style_cfg["negative"],
            })
    
    return cg_prompts


def generate_bgm_guide(scenes: List[Dict]) -> Dict:
    """
    生成BGM制作指南
    包含每个氛围类型的AI音乐提示词和推荐
    """
    BGM_STYLE_MAP = {
        "calm_piano": {
            "prompt": "calm solo piano, gentle and sentimental, minor key, slow tempo, emotional ballad, Japanese visual novel background music, peaceful",
            "style": "钢琴独奏",
            "suno_genre": "calm piano ballad",
        },
        "tense_strings": {
            "prompt": "tense string quartet, suspenseful, building tension, dramatic, thriller soundtrack, minimal, repetitive motif",
            "style": "弦乐紧张",
            "suno_genre": "suspense film score",
        },
        "romantic": {
            "prompt": "romantic piano and strings, warm, gentle, love theme, sweet melody, visual novel romance bgm, tender and emotional",
            "style": "浪漫温馨",
            "suno_genre": "romantic orchestral pop",
        },
        "sad": {
            "prompt": "sad piano or violin, melancholic, emotional, rainy day mood, tearful, slow, minor key progression, nostalgic",
            "style": "悲伤哀婉",
            "suno_genre": "sad emotional piano",
        },
        "upbeat": {
            "prompt": "upbeat pop instrumental, happy, cheerful, energetic, bright piano and light drums, slice of life bgm, positive vibes",
            "style": "欢快日常",
            "suno_genre": "upbeat jpop instrumental",
        },
        "mysterious": {
            "prompt": "mysterious ambient, soft pads, subtle tension, eerie but not horror, mysterious discovery, visual novel mystery bgm",
            "style": "神秘悬疑",
            "suno_genre": "ambient mystery",
        },
        "warm_library": {
            "prompt": "warm acoustic guitar, cozy atmosphere, library ambience, gentle fingerpicking, soft room tone, nostalgic study music",
            "style": "温暖安静",
            "suno_genre": "acoustic lofi",
        },
        "rainy_street": {
            "prompt": "rainy day jazz, soft piano, gentle rain ambience, melancholic city, romantic noir, slow tempo",
            "style": "雨夜都市",
            "suno_genre": "rainy jazz noir",
        },
        "tense_room": {
            "prompt": "tense minimal ambient, close room atmosphere, uncomfortable silence, subtle drone, psychological tension",
            "style": "压抑紧张",
            "suno_genre": "dark ambient",
        },
        "action": {
            "prompt": "action electronic, driving beat, fast tempo, intense, battle theme, synth and drums, energetic",
            "style": "战斗激烈",
            "suno_genre": "electronic action",
        },
        "nostalgic": {
            "prompt": "nostalgic music box or soft piano, memories, childhood, bittersweet, slow waltz, warm but sad",
            "style": "回忆怀旧",
            "suno_genre": "nostalgic music box",
        },
        "hopeful": {
            "prompt": "hopeful orchestral, rising melody, new beginning, inspirational, gentle build, warm strings, bright future",
            "style": "希望光明",
            "suno_genre": "inspirational orchestral",
        },
        "comedy": {
            "prompt": "comedic light music, playful pizzicato strings, quirky, funny, cartoonish, lighthearted, silly situations",
            "style": "搞笑轻松",
            "suno_genre": "comedy cartoon",
        },
    }
    
    # 收集所有场景的BGM需求
    bgm_needs = {}
    for scene in scenes:
        mood = scene.get("bgm_mood", "calm_piano")
        if mood not in bgm_needs:
            bgm_needs[mood] = {"scenes": [], "mood": mood}
        bgm_needs[mood]["scenes"].append(scene["scene_id"])
    
    # 生成BGM制作指南
    bgm_list = []
    for mood, info in bgm_needs.items():
        bgm_style = BGM_STYLE_MAP.get(mood, {
            "prompt": f"{mood} instrumental background music, visual novel style, loopable",
            "style": mood,
            "suno_genre": "ambient instrumental",
        })
        
        bgm_list.append({
            "mood": mood,
            "style_cn": bgm_style["style"],
            "scene_count": len(info["scenes"]),
            "scenes": info["scenes"],
            "ai_prompt": bgm_style["prompt"],
            "suno_genre": bgm_style["suno_genre"],
            "filename_template": f"bgm_{mood}.mp3",
            "recommendation": f"推荐在Suno.ai中选择 '{bgm_style['suno_genre']}' 风格生成，或搜索CC0音乐: '{mood}'",
        })
    
    return {
        "total_tracks": len(bgm_list),
        "bgm_tracks": bgm_list,
        "guide": (
            "## BGM制作指南\n\n"
            "1. **Suno.ai**: 将下面的prompt复制到Suno.ai生成，建议生成3-5个版本挑选\n"
            "2. **CC0音乐**: 搜索 'free visual novel bgm' 或访问 DOVA-SYNDROME / 甘茶の音楽工房\n"
            "3. **格式要求**: 导出为MP3或OGG，建议44.1kHz，单曲至少1分钟且可循环\n\n"
            "4. **循环处理**: 如果你需要对BGM做无缝循环，可以使用Audacity等工具裁剪\n"
        ),
    }


def generate_voice_guide(scenes: List[Dict]) -> Dict:
    """
    生成配音制作指南
    包含角色配音方案和TTS/克隆思路
    """
    # 收集所有角色
    characters = {}
    for scene in scenes:
        for char in scene.get("characters_in_scene", []):
            name = char.get("name", "未知角色")
            if name not in characters and name != "旁白":
                characters[name] = {
                    "name": name,
                    "role": char.get("role", ""),
                    "line_count": 0,
                }
        
        for line in scene.get("lines", []):
            speaker = line.get("speaker", "")
            if speaker in characters:
                characters[speaker]["line_count"] += 1
    
    character_guide = []
    for name, info in characters.items():
        character_guide.append({
            "name": name,
            "role": info["role"],
            "total_lines": info["line_count"],
            "solution_a": {
                "name": "GPT-SoVITS 声音克隆（推荐）",
                "steps": [
                    f"1. 找一个符合{name}人设的声优配音样本（3-5分钟音频）",
                    "2. 下载GPT-SoVITS: https://github.com/RVC-Boss/GPT-SoVITS",
                    "3. 使用WebUI上传音频样本，训练语音模型",
                    "4. 将台词逐句输入TTS生成配音",
                    f"5. 导出每个台词的WAV文件，命名为 {name}_line001.wav 等",
                ],
            },
            "solution_b": {
                "name": "商用TTS服务",
                "steps": [
                    "1. 访问 ElevenLabs (elevenlabs.io) 或 Fish Audio (fish.audio)",
                    "2. 选择合适的声音模板或上传样本克隆",
                    "3. 逐句生成语音并下载",
                ],
            },
            "character_traits": f"角色定位: {info['role']}，台词量: {info['line_count']}句",
        })
    
    return {
        "total_characters": len(character_guide),
        "characters": character_guide,
        "guide": (
            "## 配音制作指南\n\n"
            "### 方案一：GPT-SoVITS（免费/本地）\n"
            "1. 下载并安装 GPT-SoVITS\n"
            "2. 为每个角色准备3-5分钟的干净语音样本\n"
            "3. 训练语音模型\n"
            "4. 逐句TTS生成\n\n"
            "### 方案二：商用TTS（付费/云端）\n"
            "1. ElevenLabs: 10美元/月起，支持声音克隆\n"
            "2. Fish Audio: 国内可访问，中文支持好\n\n"
            "### 格式要求\n"
            "- 采样率: 44100Hz\n"
            "- 格式: WAV 或 OGG\n"
            "- 按角色分文件夹存放\n"
            "- 命名规范: {角色名}_{表情}_{编号}.wav"
        ),
    }


def _safe_filename(name: str) -> str:
    """将名称转换为安全的文件名"""
    import re
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', "_", name)
    return name


def generate_ui_prompts(
    scenes: List[Dict],
    style: str = "anime_default",
    game_title: str = "",
) -> Dict:
    """
    生成标题画面和UI元素的AI绘图提示词
    """
    style_cfg = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["anime_default"])
    
    # 从场景中提取游戏基调
    all_moods = [s.get("mood", "") for s in scenes]
    all_locations = [s.get("location", "") for s in scenes]
    
    # 判断游戏类型基调（启发式）
    if any("action" in m or "battle" in m for m in all_moods):
        title_theme = "cinematic action shot"
    elif any("romantic" in m or "love" in m for m in all_moods):
        title_theme = "romantic atmosphere, soft lighting"
    elif any("mysterious" in m or "dark" in m or "horror" in m for m in all_moods):
        title_theme = "mysterious dark atmosphere"
    else:
        title_theme = "nostalgic slice of life atmosphere"
    
    # 找一个标志性地点
    signature_loc = all_locations[0] if all_locations else "教室"
    first_bg = ""
    for s in scenes:
        if s.get("bg_description"):
            first_bg = s["bg_description"][:100]
            break
    
    title_bg_prompt = (
        f"{style_cfg['base_prompt']}, "
        f"visual novel title screen background, {title_theme}, "
        f"{first_bg if first_bg else 'scenic background with cinematic composition'}, "
        f"wide shot, beautiful cinematic lighting, "
        f"suitable for game title overlay, text-friendly negative space at center, "
        f"no characters or minimal silhouettes"
    )
    
    return {
        "title_screen": {
            "filename": "title_bg.png",
            "prompt": title_bg_prompt,
            "negative_prompt": f"{style_cfg['negative']}, text, logo, watermark, character",
            "notes": "标题画面背景。建议在上方留空以放置游戏标题文字，可在Ren'Py中用title screen展示。",
            "guide": (
                "## 标题画面制作\n\n"
                "1. 将生成的图片放入 `game/images/title_bg.png`\n"
                "2. 如果需要在图片上加标题文字，推荐用PS/Affinity等工具后期添加\n"
                "3. 标题画面会在游戏启动时展示，可以用Ren'Py的screen系统定制\n"
                "4. 建议另外生成一个logo/标题文字PNG，叠在背景上面"
            ),
        },
        "textbox": {
            "filename": "textbox.png",
            "prompt": (
                f"{style_cfg['base_prompt']}, "
                f"visual novel textbox, semi-transparent dark gradient panel, "
                f"clean UI element, optimized for text readability, "
                f"horizontal rectangle shape, subtle border decoration, "
                f"matching {title_theme}, 2D game asset"
            ),
            "negative_prompt": f"{style_cfg['negative']}, text, letters",
            "notes": "对话框背景。放在画面底部，半透明以便看到背景。尺寸建议1920x200px。",
            "guide": "放在 `game/images/textbox.png`，在gui.rpy中配置。",
        },
        "choice_buttons": {
            "filename": "choice_idle_background.png",
            "prompt": (
                f"{style_cfg['base_prompt']}, "
                f"visual novel choice button, colored rounded rectangle, "
                f"semi-transparent with subtle glow, clean game UI element, "
                f"{title_theme}, 2D game asset, button sprite"
            ),
            "negative_prompt": f"{style_cfg['negative']}, text, letters",
            "notes": "选择支按钮。hover状态可以用更亮的颜色版本。",
            "guide": "放在 `game/images/` 下，在screens.rpy中引用。",
        },
        "namebox": {
            "filename": "namebox.png",
            "prompt": (
                f"{style_cfg['base_prompt']}, "
                f"visual novel name tag box, small horizontal panel, "
                f"semi-transparent, clean corner decoration, "
                f"{title_theme}, 2D game asset, namebox element"
            ),
            "negative_prompt": f"{style_cfg['negative']}, text, letters",
            "notes": "角色名标签框。放在对话框上方。",
            "guide": "放在 `game/images/namebox.png`。",
        },
        "game_logo": {
            "filename": "game_logo.png",
            "prompt": (
                f"masterpiece, best quality, anime style, "
                f"game logo design, {title_theme}, "
                f"artistic text design, decorative border, "
                f"transparent background, visual novel title art, "
                f"elegant typography container, clean logo template"
            ),
            "negative_prompt": f"{style_cfg['negative']}, actual text, letters, words, readable text",
            "notes": f"游戏标题Logo。如游戏名是'{game_title}'，可用PS等工具添加文字。提示词生成的是Logo背景/框架。",
            "guide": "放在 `game/images/game_logo.png`，在title screen中叠加显示。",
        },
        "guide": (
            "## UI图片制作指南\n\n"
            "### 需要制作的UI元素\n"
            "1. **标题画面背景** (title_bg.png) — 游戏启动时的全屏背景\n"
            "2. **游戏Logo** (game_logo.png) — 标题画面的LOGO艺术字\n"
            "3. **对话框** (textbox.png) — 底部显示台词的面板\n"
            "4. **名字框** (namebox.png) — 显示说话人名字的小框\n"
            "5. **选项按钮** (choice_*.png) — 分支选择的按钮\n\n"
            "### 尺寸建议\n"
            "- 背景: 1920x1080 或 1280x720\n"
            "- 对话框: 1920x200\n"
            "- 名字框: 300x60\n"
            "- 按钮: 400x60\n\n"
            "### 风格建议\n"
            "- 所有UI元素保持风格统一\n"
            "- 使用半透明效果让背景透过来\n"
            "- Logo单独制作带透明通道的PNG"
        ),
    }


def generate_all_prompts(
    scenes: List[Dict],
    style: str = "anime_default",
) -> Dict:
    """
    生成所有类型的提示词和制作指南
    
    Returns:
        {
            "characters": [...],       # 角色立绘提示词
            "backgrounds": [...],      # 背景提示词
            "cgs": [...],              # 事件CG提示词
            "bgm": {...},             # BGM制作指南
            "voice": {...},           # 配音制作指南
            "scene_summary": {...},   # 场景摘要
            "style": str,             # 使用的画风
        }
    """
    from .scene_analyzer import generate_scene_summary

    ui_prompts = generate_ui_prompts(scenes, style)
    tool_recs = generate_tool_recommendations()

    return {
        "characters": generate_character_prompts(scenes, style),
        "backgrounds": generate_background_prompts(scenes, style),
        "cgs": generate_cg_prompts(scenes, style),
        "bgm": generate_bgm_guide(scenes),
        "voice": generate_voice_guide(scenes),
        "ui": ui_prompts,
        "tool_recommendations": tool_recs,
        "scene_summary": generate_scene_summary(scenes),
        "style": style,
        "style_name": STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["anime_default"])["name"],
    }


def generate_tool_recommendations() -> Dict:
    """
    生成AI工具推荐指南
    每个类别列出付费和免费选项，加上使用建议
    """
    return {
        "image_generation": {
            "title": "🎨 AI绘图工具推荐",
            "paid": [
                {
                    "name": "NovelAI v4",
                    "price": "$10-25/月",
                    "best_for": "二次元/动漫角色和场景，专为视觉小说优化",
                    "pros": "出图质量高、NSFW友好、无需复杂prompt",
                    "url": "novelai.net",
                },
                {
                    "name": "niji-journey (Midjourney)",
                    "price": "$10-60/月",
                    "best_for": "高质量动漫插画，电影级构图",
                    "pros": "画面细腻、角色设计一流",
                    "cons": "NSFW限制严格",
                    "url": "midjourney.com",
                },
                {
                    "name": "DALL-E 3 (ChatGPT Plus)",
                    "price": "$20/月",
                    "best_for": "快速出概念图，prompt理解力强",
                    "pros": "操作简单，中文prompt友好",
                    "cons": "NSFW完全屏蔽",
                    "url": "chat.openai.com",
                },
            ],
            "free": [
                {
                    "name": "Stable Diffusion (本地部署)",
                    "price": "完全免费",
                    "best_for": "批量出图、无内容审查、可定制模型",
                    "pros": "完全免费、无限生成、NSFW可用、模型库丰富",
                    "cons": "需要显卡（建议6GB+ VRAM）、配置稍复杂",
                    "guide": "推荐使用 Stability Matrix 一键安装包，加载动漫模型如 Anything-v5、Counterfeit",
                },
                {
                    "name": "ComfyUI (本地)",
                    "price": "完全免费",
                    "best_for": "节点式工作流、批量处理、高级控制",
                    "pros": "工作流可复用、适合量产、社区模板丰富",
                    "guide": "适合批量生成立绘差分，搭好工作流后拖入prompt即可批量出图",
                },
                {
                    "name": "通义万相 (阿里)",
                    "price": "免费额度",
                    "best_for": "中文用户、无需翻墙、快速出图",
                    "pros": "中文prompt支持好、免费额度够用",
                    "cons": "风格控制较弱、商业用途需确认",
                    "url": "tongyi.aliyun.com/wanxiang",
                },
                {
                    "name": "CivitAI (在线生图)",
                    "price": "免费（部分需付费）",
                    "best_for": "社区共享模型，浏览器在线跑SD",
                    "pros": "模型多、可在线预览效果",
                    "url": "civitai.com",
                },
            ],
            "bg_removal": [
                {
                    "name": "remove.bg",
                    "price": "免费（低分辨率）/ 付费",
                    "best_for": "一键去背景，效果极好",
                    "url": "remove.bg",
                },
                {
                    "name": "RMBG-2.0 (本地)",
                    "price": "完全免费",
                    "best_for": "批量去背景、本地运行、隐私安全",
                    "guide": "GitHub: briaai/RMBG-2.0，效果接近 remove.bg",
                },
                {
                    "name": "Photoshop / GIMP",
                    "price": "付费 / 免费",
                    "best_for": "精细手工修图",
                },
            ],
            "guide": "推荐组合: 日常图用NovelAI（快且质量高），批量用SD本地（免费无限），CG大图用niji。⚠️ 立绘生成后务必用背景去除工具处理！",
        },
        "bgm_generation": {
            "title": "🎵 BGM音乐工具推荐",
            "paid": [
                {
                    "name": "Suno.ai Pro",
                    "price": "$10-30/月",
                    "best_for": "批量生成BGM、音质好、支持歌词",
                    "pros": "音质优秀、风格多样、商用授权含Pro",
                    "url": "suno.ai",
                },
                {
                    "name": "Udio Pro",
                    "price": "$10/月",
                    "best_for": "高品质BGM、声音更自然",
                    "url": "udio.com",
                },
                {
                    "name": "Artlist / Epidemic Sound",
                    "price": "$10-15/月",
                    "best_for": "真实录音室品质音乐、商用无忧",
                    "pros": "真人演奏、法律安全",
                },
            ],
            "free": [
                {
                    "name": "Suno.ai (免费版)",
                    "price": "免费（每日额度）",
                    "best_for": "快速生成、试试效果",
                    "pros": "操作极简、生成快",
                    "cons": "商用需Pro、每日限制次数",
                },
                {
                    "name": "DOVA-SYNDROME",
                    "price": "完全免费",
                    "best_for": "日系BGM、品类齐全",
                    "pros": "数千首免费曲目、日本创作者、商用可",
                    "url": "dova-s.jp",
                },
                {
                    "name": "甘茶の音楽工房",
                    "price": "完全免费",
                    "best_for": "和风/治愈系BGM",
                    "url": "amachamusic.chagasi.com",
                },
                {
                    "name": "Freesound / Pixabay Music",
                    "price": "完全免费",
                    "best_for": "音效和氛围音乐",
                },
            ],
            "guide": "推荐: 先用Suno.ai免费版生成demo，确认方向后用Pro版本正式生成。需要特定氛围的BGM可去DOVA-SYNDROME按标签搜索。",
        },
        "voice_generation": {
            "title": "🎙️ 配音/语音工具推荐",
            "paid": [
                {
                    "name": "ElevenLabs",
                    "price": "$5-99/月",
                    "best_for": "高品质多语言TTS、声音克隆",
                    "pros": "音质顶级、30+语言、API可用",
                    "url": "elevenlabs.io",
                },
                {
                    "name": "Fish Audio",
                    "price": "按量付费",
                    "best_for": "中文配音、国内可用",
                    "pros": "中文效果好、API价格低",
                    "url": "fish.audio",
                },
            ],
            "free": [
                {
                    "name": "GPT-SoVITS (本地)",
                    "price": "完全免费",
                    "best_for": "声音克隆、完全可控",
                    "pros": "克隆效果极好、本地运行无审查、中文日文都行",
                    "cons": "需要显卡、需准备样本音频、配置稍复杂",
                    "guide": "推荐方案！用3-5分钟干净人声样本即可训练。GitHub: RVC-Boss/GPT-SoVITS",
                },
                {
                    "name": "RVC (Retrieval-based Voice Conversion)",
                    "price": "完全免费",
                    "best_for": "声音转换/翻唱风格语音合成",
                    "guide": "与GPT-SoVITS配合使用效果好。先录自己的声音念台词，再用RVC转成目标声线。",
                },
                {
                    "name": "Coqui TTS",
                    "price": "完全免费",
                    "best_for": "开源多语言TTS框架",
                    "cons": "音质一般，不如GPT-SoVITS",
                },
            ],
            "guide": "推荐: GPT-SoVITS是当前最好的免费方案。准备样本时注意：安静环境录制、语速自然、包含不同情绪。样本越长效果越好。",
        },
    }
