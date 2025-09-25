import json
import re
from pathlib import Path

from google import genai

from config import SUMMARY_MODEL

class PaperSummarizer:
    """
    論文の要約を行う
    - 背景・目的
        - この論文ではどのような背景・課題があって、それを解決する研究なのか
    - 手法
        - どうやったかをそれなりに詳しく
    - 結果
        - どのような実験でそれを確かめたのか
    """
    def __init__(self, api_key: str):
        """
        Args:
            api_key(str): geminiのapikey
        """
        self.client = genai.Client(api_key=api_key)
        self.model = SUMMARY_MODEL # "gemini-2.5-pro" "gemini-2.5-flash"
    
    def simple_summary(self, text_path: Path, save_directory: Path, save: bool=True) -> str:
        """
        雑に全部投げて要約を作ってもらう
        Args:
            text_path(str): 要約元のテキストファイル
            save_directory(Path): 保存する場所のパス、名前はpdfと同じ
            save(bool): 保存をするのかどうか
        """
        with text_path.open("r", encoding="utf-8") as f:
            text = f.read()
        
        try:
            data = json.loads(text)
        except json.decoder.JSONDecodeError:
            text = text.replace("\\", "\\\\")
            data = json.loads(text)

        paper_content = ""
        for section in data["sections"]:
            paper_content += f"section_id: {section["id"]}, {section["title"]}\n"
            paper_content += section["content"]
            paper_content += "\n"

        prompt = """\
論文のテキストを渡すので日本語で要約を行ってください。
- キーワード
    - 英語、リスト形式で
- 背景・目的
    - この論文ではどのような背景・課題があって、それを解決する研究なのかを簡潔に
- 手法
    - どうやったかをそれなりに詳しく
- 結果
    - どのような実験でそれを確かめたのか
返す形式は
```markdown
### キーワード
- keyword1
- keyword2
...
### 背景・目的
...
### 手法
...
### 実験
...
```
としてください。この形式でキーワードとこれら3項目についてまとめてください。
"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                prompt,
                paper_content,
            ]
        )

        # textは保存しておく
        if save_directory is not None:
            save_path = save_directory / (text_path.stem + ".md")
        else:
            save_path = text_path.parent / (text_path.stem + ".md")
        with save_path.open("w", encoding="utf-8") as f:
            f.write(response.text)

        return response.text

    def overview(self) -> str:
        """
        論文のセクション構造を返す
        """
        text = ""
        for section in self.data["sections"]:
            sentences = re.split(r'(?<=[.?!])\s+', section["content"])
            text += f"section_id: {section["id"]}, {section["title"]}\n"
            text += sentences[0]
            text += "\n"
        
        return text

    def full_section(self, target_ids: list[str]) -> str:
        """
        指定セクションの本文を返す
        """
        text = ""
        for section in self.data["sections"]:
            if section["id"] in target_ids:
                text += f"section_id: {section["id"]}, {section["title"]}\n"
                text += section["content"]
                text += "\n"
        
        return text
