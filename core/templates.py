"""
项目模板系统
预设不同风格的视觉小说模板（校园/古风/科幻等）
"""

from typing import List, Dict


# === 项目模板定义 ===
PROJECT_TEMPLATES = {
    "campus": {
        "id": "campus",
        "name_cn": "校园恋爱",
        "name_en": "Campus Romance",
        "name_ja": "学園恋愛",
        "description_cn": "经典的校园恋爱故事模板，教室、天台、图书馆、放学路",
        "icon": "🏫",
        "default_style": "anime_default",
        "bgm_presets": {
            "calm_piano": "soft piano school bgm, warm afternoon classroom",
            "upbeat": "cheerful school life, bright morning, friends chatting",
            "romantic": "sweet romantic piano, sunset rooftop confession",
            "sad": "melancholic piano after school, empty classroom",
        },
        "bg_locations": [
            "教室 (sunlit_classroom)",
            "走廊 (school_corridor)",
            "天台 (rooftop)",
            "图书馆 (library)",
            "校门口 (school_gate)",
            "操场 (playground)",
            "放学路 (school_road)",
        ],
        "character_archetypes": [
            {"role": "主角", "desc": "普通高中生，黑发，白衬衫校服"},
            {"role": "女主", "desc": "同班同学或学妹，校服或便服"},
            {"role": "闺蜜/基友", "desc": "好友角色，活泼或冷静"},
        ],
        "scene_types": [
            "first_meeting", "classroom", "club_room", "rooftop_talk",
            "library_study", "school_festival", "confession", "graduation",
        ],
        "color_scheme": {
            "primary": "#FF6B8A",
            "secondary": "#87CEEB",
            "bg": "#FFF8F0",
            "text": "#4A3728",
            "accent": "#FFB6C1",
        },
        "ui_prompts": {
            "title_bg": (
                "masterpiece, best quality, anime style, "
                "Japanese high school background, cherry blossoms in spring, "
                "school building in distance, soft sunlight, nostalgic atmosphere, "
                "wide shot, beautiful sky, visual novel title screen background"
            ),
            "textbox": (
                "masterpiece, best quality, anime style, "
                "visual novel textbox, semi-transparent gradient, "
                "warm pink border, soft rounded corners, clean UI element, "
                "2D game asset"
            ),
            "choice_buttons": (
                "masterpiece, best quality, anime style, "
                "visual novel choice button, pastel pink gradient, "
                "soft glow, rounded rectangle, game UI element"
            ),
        },
    },
    "ancient_chinese": {
        "id": "ancient_chinese",
        "name_cn": "古风仙侠",
        "name_en": "Ancient Chinese Fantasy",
        "name_ja": "中華古風ファンタジー",
        "description_cn": "古风仙侠/宫廷/江湖题材，山水墨韵、竹林庭院、月下剑影",
        "icon": "🏯",
        "default_style": "chinese_ink",
        "bgm_presets": {
            "calm_piano": "traditional guqin solo, peaceful bamboo forest, ancient Chinese zen",
            "tense_strings": "erhu tension, battle preparation, dramatic Chinese orchestra",
            "romantic": "soft pipa and flute duet, moonlit garden, ancient love theme",
            "sad": "solo xiao flute, rainy pavilion, nostalgic ancient melody",
            "action": "fast Chinese drum, martial arts battle, dynamic guzheng",
            "mysterious": "mysterious guqin, ancient temple, spiritual atmosphere",
        },
        "bg_locations": [
            "竹林 (bamboo_forest)",
            "月下庭院 (moonlit_courtyard)",
            "山巅道观 (mountain_temple)",
            "江南水乡 (water_town)",
            "宫殿大殿 (palace_hall)",
            "桃花林 (peach_blossom_grove)",
            "悬崖边 (cliff_edge)",
            "客栈 (ancient_inn)",
        ],
        "character_archetypes": [
            {"role": "主角", "desc": "年轻剑客/书生，白衣或青衫，束发"},
            {"role": "女主", "desc": "仙子/闺秀，飘逸长裙，发簪步摇"},
            {"role": "前辈/师父", "desc": "德高望重的长者，仙风道骨"},
        ],
        "scene_types": [
            "first_meeting", "sword_practice", "tea_ceremony", "moon_gazing",
            "battle", "confession", "parting", "reunion",
        ],
        "color_scheme": {
            "primary": "#8B4513",
            "secondary": "#2F4F4F",
            "bg": "#F5F0E8",
            "text": "#3C2415",
            "accent": "#C41E3A",
        },
        "ui_prompts": {
            "title_bg": (
                "masterpiece, best quality, Chinese ink painting style, "
                "misty mountains, ancient Chinese landscape, pine trees, "
                "waterfall in distance, poetic atmosphere, elegant, "
                "traditional Chinese art, visual novel title screen, wide shot"
            ),
            "textbox": (
                "masterpiece, best quality, Chinese ink painting style, "
                "ancient scroll texture border, semi-transparent parchment, "
                "traditional Chinese pattern decoration, elegant, "
                "visual novel textbox, 2D game asset"
            ),
            "choice_buttons": (
                "masterpiece, best quality, Chinese ink painting style, "
                "ancient Chinese seal stamp design, red ink border, "
                "traditional calligraphy vibe, game UI element"
            ),
        },
    },
    "sci_fi": {
        "id": "sci_fi",
        "name_cn": "科幻未来",
        "name_en": "Sci-Fi Future",
        "name_ja": "SF未来",
        "description_cn": "赛博朋克/太空歌剧/近未来题材，霓虹都市、飞船舰桥、虚拟空间",
        "icon": "🚀",
        "default_style": "anime_realistic",
        "bgm_presets": {
            "calm_piano": "ambient synth, space station interior, calm sci-fi atmosphere",
            "tense_strings": "cyberpunk tension, dark synth, dystopian electronic",
            "romantic": "ethereal synth pad, stargazing, romantic sci-fi",
            "action": "fast electronic, mecha battle, intense synthwave",
            "mysterious": "deep space ambient, alien discovery, mysterious drone",
            "upbeat": "future pop, bright synth, utopian city life",
        },
        "bg_locations": [
            "霓虹街道 (neon_street)",
            "太空舰桥 (spaceship_bridge)",
            "实验室 (laboratory)",
            "虚拟空间 (virtual_space)",
            "废墟都市 (ruined_city)",
            "太空站观景台 (space_station_view)",
            "机甲格纳库 (mecha_hangar)",
            "未来教室 (future_classroom)",
        ],
        "character_archetypes": [
            {"role": "主角", "desc": "年轻机师/黑客，近未来服装，可能有义体"},
            {"role": "女主", "desc": "AI/改造人/研究员，科技感服装"},
            {"role": "队友/搭档", "desc": "战友或AI助手"},
        ],
        "scene_types": [
            "first_meeting", "hacker_room", "rooftop_city", "spacewalk",
            "battle", "virtual_world", "escape", "final_battle",
        ],
        "color_scheme": {
            "primary": "#00FFFF",
            "secondary": "#FF00FF",
            "bg": "#0A0A1A",
            "text": "#E0E0FF",
            "accent": "#00FF88",
        },
        "ui_prompts": {
            "title_bg": (
                "masterpiece, best quality, sci-fi anime style, "
                "futuristic city skyline at night, neon lights, holographic billboards, "
                "flying cars, cyberpunk aesthetic, rain on glass, "
                "visual novel title screen background, wide cinematic shot"
            ),
            "textbox": (
                "masterpiece, best quality, sci-fi anime style, "
                "holographic interface, semi-transparent blue glass panel, "
                "digital circuit border, neon glow, high-tech UI element, "
                "visual novel textbox, 2D game asset"
            ),
            "choice_buttons": (
                "masterpiece, best quality, sci-fi anime style, "
                "holographic button, cyan neon glow, rounded digital panel, "
                "futuristic UI design, game UI element"
            ),
        },
    },
    "mystery_horror": {
        "id": "mystery_horror",
        "name_cn": "悬疑惊悚",
        "name_en": "Mystery Horror",
        "name_ja": "ミステリーホラー",
        "description_cn": "推理/恐怖/心理惊悚，昏暗洋馆、废弃医院、迷雾小镇",
        "icon": "🔍",
        "default_style": "anime_default",
        "bgm_presets": {
            "tense_strings": "psychological horror strings, creeping dread, minimal",
            "mysterious": "dark ambient, old mansion atmosphere, subtle tension",
            "sad": "haunting piano, ghostly melody, tragic backstory",
            "action": "chase sequence, frantic strings, heart-pounding",
        },
        "bg_locations": [
            "昏暗洋馆 (dark_mansion)",
            "废弃医院 (abandoned_hospital)",
            "迷雾森林 (foggy_forest)",
            "老旧图书馆 (old_library)",
            "地下密室 (underground_room)",
            "雨夜街道 (rainy_street_mystery)",
        ],
        "character_archetypes": [
            {"role": "主角", "desc": "侦探/调查员，深色风衣或校服"},
            {"role": "女主", "desc": "神秘少女，可能有特殊能力"},
            {"role": "助手/搭档", "desc": "可靠的伙伴或亦敌亦友"},
        ],
        "scene_types": [
            "arrival", "investigation", "discovery", "chase",
            "revelation", "confrontation", "escape", "truth",
        ],
        "color_scheme": {
            "primary": "#8B0000",
            "secondary": "#2F1B41",
            "bg": "#0D0D0D",
            "text": "#D4C5B2",
            "accent": "#FF4444",
        },
        "ui_prompts": {
            "title_bg": (
                "masterpiece, best quality, anime style, dark gothic, "
                "old Victorian mansion in moonlight, fog, dead trees, "
                "mysterious atmosphere, horror visual novel title screen, "
                "wide shot, dark and moody"
            ),
            "textbox": (
                "masterpiece, best quality, anime style, "
                "dark vintage frame, ornate gothic border, "
                "semi-transparent dark panel, aged texture, "
                "visual novel textbox, horror game UI"
            ),
            "choice_buttons": (
                "masterpiece, best quality, anime style, "
                "aged paper texture, blood-red accent, vintage button, "
                "gothic horror UI element"
            ),
        },
    },
    "fantasy": {
        "id": "fantasy",
        "name_cn": "异世界奇幻",
        "name_en": "Isekai Fantasy",
        "name_ja": "異世界ファンタジー",
        "description_cn": "异世界转生/剑与魔法/冒险公会，中世纪欧洲风",
        "icon": "⚔️",
        "default_style": "light_novel",
        "bgm_presets": {
            "calm_piano": "medieval town, peaceful lute, fantasy village",
            "upbeat": "adventuring music, heroic orchestra, rpg town theme",
            "action": "epic battle orchestra, sword clash, fantasy combat",
            "romantic": "magical romance, harp and strings, moonlit castle",
            "mysterious": "ancient ruins, mystical choir, dungeon exploration",
        },
        "bg_locations": [
            "冒险者公会 (adventurer_guild)",
            "王城街道 (royal_city_street)",
            "魔法学院 (magic_academy)",
            "精灵森林 (elf_forest)",
            "地下迷宫 (dungeon)",
            "城堡大厅 (castle_hall)",
            "草原旅路 (grassland_road)",
        ],
        "character_archetypes": [
            {"role": "主角", "desc": "转生者/冒险者，轻甲或法袍"},
            {"role": "女主", "desc": "精灵/公主/魔法师，奇幻装束"},
            {"role": "队友", "desc": "战士/魔法师/盗贼等经典职业"},
        ],
        "scene_types": [
            "summoning", "guild_hall", "quest", "dungeon_crawl",
            "campfire", "festival", "final_boss", "coronation",
        ],
        "color_scheme": {
            "primary": "#4A90D9",
            "secondary": "#D4A017",
            "bg": "#1A2A1A",
            "text": "#F0E6D0",
            "accent": "#FFD700",
        },
        "ui_prompts": {
            "title_bg": (
                "masterpiece, best quality, anime fantasy style, "
                "floating castle in the sky, magical floating islands, "
                "dragon flying in distance, epic fantasy landscape, "
                "warm sunset lighting, visual novel title screen, wide shot"
            ),
            "textbox": (
                "masterpiece, best quality, anime fantasy style, "
                "ornate golden border, medieval manuscript texture, "
                "semi-transparent parchment panel, fantasy game UI, "
                "visual novel textbox, 2D game asset"
            ),
            "choice_buttons": (
                "masterpiece, best quality, anime fantasy style, "
                "golden ornate button, magical glow, medieval design, "
                "fantasy game UI element"
            ),
        },
    },
    "adult_romance": {
        "id": "adult_romance",
        "name_cn": "成人恋爱",
        "name_en": "Adult Romance",
        "name_ja": "アダルト恋愛",
        "description_cn": "成人向恋爱故事，含好感度系统、画面特效、CG画廊、H场景解锁",
        "icon": "💕",
        "default_style": "anime_realistic",
        "adult": True,
        "features": ["affection", "screen_shake", "cg_gallery", "h_scene_unlock"],
        "bgm_presets": {
            "calm_piano": "intimate solo piano, warm bedroom atmosphere, gentle",
            "romantic": "sensual r&b instrumental, soft saxophone, candlelit mood",
            "tense_strings": "erotic tension, slow bass, breathy synths",
            "sad": "melancholic piano, rainy window, heartbreak",
            "upbeat": "playful pop instrumental, flirty, cheerful date",
            "mysterious": "dark seduction, pulsing beat, mysterious encounter",
            "hopeful": "morning after, gentle acoustic guitar, new love",
        },
        "bg_locations": [
            "卧室 (bedroom)",
            "咖啡厅 (cafe)",
            "温泉旅馆 (hot_spring_inn)",
            "夜店 (night_club)",
            "海边 (beach)",
            "浴室 (bathroom)",
            "酒店房间 (hotel_room)",
            "私人影院 (private_cinema)",
        ],
        "character_archetypes": [
            {"role": "主角", "desc": "普通青年/上班族，便服或正装，可塑性强的外表"},
            {"role": "女主1", "desc": "活泼系/傲娇系/温柔系，日常+私密服装"},
            {"role": "女主2", "desc": "成熟系/御姐系，职业装+私服"},
            {"role": "女主3", "desc": "学妹系/妹妹系，可爱风格"},
        ],
        "scene_types": [
            "first_meeting", "date", "confession", "intimate_talk",
            "first_kiss", "love_scene", "morning_after", "conflict",
            "reconciliation", "proposal", "epilogue",
        ],
        "color_scheme": {
            "primary": "#FF3366",
            "secondary": "#993366",
            "bg": "#1A0A10",
            "text": "#F0D0D8",
            "accent": "#FF69B4",
        },
        "ui_prompts": {
            "title_bg": (
                "masterpiece, best quality, anime style, "
                "romantic sunset silhouette, couple embracing in distance, "
                "soft bokeh lighting, cherry blossom petals, "
                "sensual romantic atmosphere, warm color palette, "
                "visual novel adult romance title screen, cinematic"
            ),
            "textbox": (
                "masterpiece, best quality, anime style, "
                "semi-transparent dark gradient panel with subtle red glow, "
                "elegant curved corners, romantic visual novel textbox, "
                "sophisticated adult game UI, 2D game asset"
            ),
            "choice_buttons": (
                "masterpiece, best quality, anime style, "
                "heart-shaped accent button, rose gold gradient, "
                "soft glow, romantic adult game UI element"
            ),
        },
        "renpy_features": {
            "affection_system": True,
            "screen_shake": True,
            "cg_gallery": True,
            "h_scene_unlock": True,
            "affection_vars": ["affection_y1", "affection_y2", "affection_y3"],
        },
    },
}


def get_template(template_id: str) -> Dict:
    """获取模板数据"""
    if template_id in PROJECT_TEMPLATES:
        return PROJECT_TEMPLATES[template_id]
    return PROJECT_TEMPLATES["campus"]


def get_all_templates() -> List[Dict]:
    """获取所有模板摘要（不含完整数据）"""
    return [
        {
            "id": t["id"],
            "name_cn": t["name_cn"],
            "name_en": t["name_en"],
            "name_ja": t["name_ja"],
            "description_cn": t["description_cn"],
            "icon": t["icon"],
            "default_style": t["default_style"],
        }
        for t in PROJECT_TEMPLATES.values()
    ]


def apply_template(scenes: List[Dict], template_id: str) -> Dict:
    """
    将模板应用到场景数据
    
    覆盖默认的风格、BGM、UI提示词等
    """
    template = get_template(template_id)
    
    return {
        "scenes": scenes,
        "template": {
            "id": template["id"],
            "name_cn": template["name_cn"],
            "color_scheme": template["color_scheme"],
            "bgm_presets": template["bgm_presets"],
            "scene_types": template["scene_types"],
            "character_archetypes": template["character_archetypes"],
            "ui_prompts": template["ui_prompts"],
        },
        "suggested_style": template["default_style"],
    }
