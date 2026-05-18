"""
小说文本解析器
负责读取小说文件，按章节/段落拆分，预处理文本
"""

import re
import os
from typing import List, Dict, Optional


def parse_novel(filepath: str) -> Dict:
    """
    读取小说文件，返回结构化文本数据
    
    Returns:
        {
            "title": str,
            "full_text": str,
            "word_count": int,
            "chapters": [{"title": str, "content": str, "word_count": int}, ...],
            "raw_paragraphs": [str, ...]
        }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    title = os.path.splitext(os.path.basename(filepath))[0]
    word_count = len(text.replace(" ", "").replace("\n", ""))

    # 尝试自动检测章节分割
    chapters = _split_chapters(text)
    raw_paragraphs = _split_paragraphs(text)

    return {
        "title": title,
        "full_text": text,
        "word_count": word_count,
        "chapters": chapters,
        "raw_paragraphs": raw_paragraphs,
        "filename": os.path.basename(filepath),
    }


def _split_chapters(text: str) -> List[Dict]:
    """尝试按章节标题分割文本"""
    # 常见的章节标识模式
    chapter_patterns = [
        r"(?:第[零一二三四五六七八九十百千万\d]+章[\s\S]*?(?=第[零一二三四五六七八九十百千万\d]+章|$))",
        r"(?:Chapter\s*\d+[\s\S]*?(?=Chapter\s*\d+|$))",
        r"(?:CHAPTER\s*\d+[\s\S]*?(?=CHAPTER\s*\d+|$))",
    ]

    for pattern in chapter_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if len(matches) > 1:
            chapters = []
            for i, match in enumerate(matches):
                match = match.strip()
                if not match:
                    continue
                # 提取章节标题（第一行）
                lines = match.split("\n", 1)
                chapter_title = lines[0].strip()
                content = lines[1].strip() if len(lines) > 1 else ""
                chapters.append({
                    "index": i + 1,
                    "title": chapter_title,
                    "content": content or match,
                    "word_count": len(content.replace(" ", "").replace("\n", ""))
                })
            return chapters

    # 如果没检测到章节，整体作为一个章节
    return [{
        "index": 1,
        "title": "全文",
        "content": text,
        "word_count": len(text.replace(" ", "").replace("\n", ""))
    }]


def _split_paragraphs(text: str) -> List[str]:
    """按段落分割，过滤空行"""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paras


def extract_characters(text: str) -> List[str]:
    """从文本中提取可能的角色名称（启发式）"""
    speakers = set()
    
    # 匹配常见的日语式对话格式: 」大家好」小明说
    # 使用 Unicode: \u300d = 」 (右书名号)
    name_pattern = re.compile(
        r"[\u300d\u201d'](.{1,4})"
        r"(?:说|問|道|喊|叫|嘆|笑|哭|怒|骂|轻|低|大|小|冷|热|淡|急|缓|慢|快|高|回|答|应|话|言|语)"
    )
    
    # 冒号对话格式: 小明：\u300c你好\u300d
    colon_pattern = re.compile(r"^(.{1,6})[\uff1a:]\s*[\u300c\u201c]")
    
    for line in text.split('\n'):
        match = colon_pattern.match(line.strip())
        if match:
            name = match.group(1).strip()
            if name and len(name) <= 6 and name not in ['我', '你', '他', '她']:
                speakers.add(name)

    matches = name_pattern.findall(text)
    for m in matches:
        if m and m not in ['我', '你', '他', '她']:
            speakers.add(m)
    
    return list(speakers)[:20]  # 最多返回20个角色名
