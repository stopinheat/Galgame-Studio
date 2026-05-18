"""
场景分析器
利用LLM将小说文本拆解为视觉小说分镜脚本
"""

import json
import re
from typing import List, Dict, Optional
from openai import OpenAI


# LLM 系统提示词 - 将小说拆解为视觉小说分镜
SCENE_ANALYSIS_SYSTEM = """你是一个专业的Galgame/视觉小说剧本编剧。你的任务是将小说文本转换为结构化的视觉小说分镜脚本。

## 输出格式
你必须返回严格的JSON数组，每个元素代表一个场景。不要包含任何JSON之外的内容。

每个场景的结构：
{
  "scene_id": "scene_001",
  "scene_title": "场景标题（简短有力，6字以内）",
  "location": "场景地点描述",
  "time": "时间描述（如：傍晚/教室/雨后）",
  "mood": "氛围（英文标签，如 warm_library / rainy_street / tense_room）",
  "bg_description": "背景画面的详细描述，用于AI绘图（50-100字，描述光线、环境、氛围、建筑细节）",
  "characters_in_scene": [
    {
      "name": "角色名",
      "role": "主角/女主/配角",
      "appearance": "外观的详细描述，用于AI绘图做立绘（包含发型、发色、服装、体型、气质，50-80字）",
      "sprites_needed": ["default", "happy", "sad", "angry", "shy"]  // 该角色需要画的情绪差分
    }
  ],
  "cg_suggestions": [
    {
      "cg_id": "cg_001",
      "description": "CG场景描述（80-120字），用于AI绘图生成事件CG",
      "trigger_line_index": 5  // 在哪个台词时触发此CG
    }
  ],
  "lines": [
    {
      "speaker": "说话人（旁白/角色名）",
      "text": "台词内容",
      "type": "narration|dialogue|inner_thought",
      "expression": "对话时的表情（仅dialogue类型需要）"
    }
  ],
  "bgm_mood": "BGM情绪标签（如 calm_piano / tense_strings / romantic / sad / upbeat / mysterious）",
  "sfx": ["音效列表", "如：door_open", "rain", "footsteps"],
  "transition": "转场方式（fade/dissolve/none）"
}

## 分支选择（choises）
如果原文中出现明显的选择或分岔（如角色面临抉择、多个可能走向），请在场景末尾添加choices字段：
{
  "choices": [
    {
      "choice_id": "choice_001a",
      "text": "选项文本（如：追上去拦住她）",
      "target_scene": "下一个场景的scene_id，暂留空由后续程序填充"
    },
    {
      "choice_id": "choice_001b", 
      "text": "选项文本（如：默默目送她离开）"
    }
  ]
}
每个choice包含：choice_id、text（选项显示的文字）、target_scene（跳转到的场景id，先留空）
注意：不要强行编造分支，只在原文确实存在选择点时才添加choices。

## 规则
1. 根据文本的自然段落和场景切换来划分场景，通常200-800字一个场景
2. 每个场景需要有明确的地点变化或情绪转折
3. 角色名要从原文中提取，不要创造新名字
4. 旁白统一用"旁白"作为speaker
5. 心情独白用type="inner_thought"
6. bg_description要足够详细，包含构图、光线、色彩指引
7. 角色appearance要统一——同一角色在不同场景中外观描述要一致
8. CG建议用于值得画成独立插画的关键场景（如相遇、重要事件、结局）
9. BGM情绪标签要能指导AI音乐生成
10. 如果原文有多个结局或分支走向，在最后一个场景的choices中体现出来"""


def analyze_novel_to_scenes(
    novel_data: Dict,
    api_key: str = None,
    api_base: str = "https://api.openai.com/v1",
    model: str = "gpt-4o",
    max_chars_per_chunk: int = 4000,
    progress_callback=None,
) -> List[Dict]:
    """
    将小说分析为场景列表
    
    Args:
        novel_data: parse_novel() 的返回值
        api_key: OpenAI兼容API的key
        api_base: API地址
        model: 模型名
        max_chars_per_chunk: 每次送入LLM的最大字符数
        progress_callback: 进度回调 fn(stage, progress, message)
    
    Returns:
        场景列表 (list of scene dicts)
    """
    if not api_key:
        raise ValueError("需要提供API Key才能进行场景分析")

    client = OpenAI(api_key=api_key, base_url=api_base)
    all_scenes = []
    
    chapters = novel_data.get("chapters", [])
    total_chapters = len(chapters)
    
    for chapter in chapters:
        if progress_callback:
            progress_callback(
                "analyzing",
                chapter["index"] / total_chapters * 100,
                f"正在分析: {chapter['title']}"
            )
        
        content = chapter["content"]
        
        # 如果章节太长，分段处理
        chunks = _chunk_text(content, max_chars_per_chunk)
        
        for i, chunk in enumerate(chunks):
            if progress_callback and len(chunks) > 1:
                progress_callback(
                    "analyzing",
                    (chapter["index"] - 1 + i / len(chunks)) / total_chapters * 100,
                    f"分析 {chapter['title']} ({i+1}/{len(chunks)})"
                )
            
            scene_chunk = _analyze_chunk(client, chunk, model, chapter["index"])
            all_scenes.extend(scene_chunk)
    
    # 重新编号场景
    for i, scene in enumerate(all_scenes):
        scene["scene_id"] = f"scene_{i+1:03d}"
    
    # 统一角色外观描述
    all_scenes = _normalize_characters(all_scenes)
    
    return all_scenes


def _chunk_text(text: str, max_chars: int) -> List[str]:
    """将文本按段落分块，每块不超过max_chars"""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current = ""
    
    for p in paragraphs:
        if len(current) + len(p) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = p
        else:
            if current:
                current += "\n\n" + p
            else:
                current = p
    
    if current.strip():
        chunks.append(current.strip())
    
    return chunks


def _analyze_chunk(client: OpenAI, text: str, model: str, chapter_index: int) -> List[Dict]:
    """调用LLM分析一段文本"""
    user_prompt = f"""请分析以下小说文本（第{chapter_index}章节），将其转换为视觉小说分镜脚本。

注意：
- 这是第{chapter_index}章
- 角色名只从原文中提取
- 背景描述要包含构图和光线指引
- 角色外观描述要详细且能够在所有场景中保持一致

小说文本：
---
{text}
---

请直接返回JSON数组，不要包含任何其他内容。"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SCENE_ANALYSIS_SYSTEM},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=16384,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 清理可能的markdown包裹
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # 尝试解析
        parsed = json.loads(result_text)
        
        # LLM可能返回 {"scenes": [...]} 或直接是数组
        if isinstance(parsed, dict):
            for key in ["scenes", "data", "result"]:
                if key in parsed:
                    parsed = parsed[key]
                    break
        
        if isinstance(parsed, list):
            return parsed
        else:
            return []
            
    except json.JSONDecodeError as e:
        # 如果JSON解析失败，尝试用正则修复
        print(f"[WARN] JSON解析失败: {e}")
        print(f"[DEBUG] 原始返回前500字: {result_text[:500]}")
        return []
    except Exception as e:
        print(f"[ERROR] LLM调用失败: {e}")
        raise


def _normalize_characters(scenes: List[Dict]) -> List[Dict]:
    """统一所有场景中的角色外观描述"""
    # 收集所有角色及其外观
    char_appearances = {}
    for scene in scenes:
        for char in scene.get("characters_in_scene", []):
            name = char.get("name", "").strip()
            appearance = char.get("appearance", "").strip()
            if name and appearance and name not in char_appearances:
                char_appearances[name] = appearance
    
    # 统一应用
    for scene in scenes:
        for char in scene.get("characters_in_scene", []):
            name = char.get("name", "").strip()
            if name in char_appearances:
                char["appearance"] = char_appearances[name]
    
    return scenes


def generate_scene_summary(scenes: List[Dict]) -> Dict:
    """生成场景统计摘要"""
    characters = set()
    locations = set()
    moods = set()
    total_lines = 0
    total_dialogues = 0
    
    for scene in scenes:
        for char in scene.get("characters_in_scene", []):
            characters.add(char.get("name", ""))
        locations.add(scene.get("location", ""))
        moods.add(scene.get("mood", ""))
        for line in scene.get("lines", []):
            total_lines += 1
            if line.get("type") == "dialogue":
                total_dialogues += 1
    
    return {
        "total_scenes": len(scenes),
        "total_lines": total_lines,
        "total_dialogues": total_dialogues,
        "character_count": len(characters),
        "characters": sorted(characters),
        "locations": sorted(locations),
        "moods": sorted(moods),
    }
