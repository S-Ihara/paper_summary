import re
import json
from pathlib import Path

from loguru import logger
from google import genai

from config import EXTRACT_MODEL

class PDFExtractor:
    """paperのpdfから構造化されたテキストを抽出する"""
    def __init__(self, api_key: str):
        """
        Args:
            api_key(str): geminiのapikey
        """
        self.client = genai.Client(api_key=api_key)
        self.model = EXTRACT_MODEL

    def extract(self, pdf_path: Path, save_directory: Path|None = None, save: bool=True) -> str:
        """
        args:
            pdf_path(Path): paper pdfのパス
            save_directory(Path): 保存する場所のパス、名前はpdfと同じ
            save(bool): 保存をするのかどうか
        """
        file = self._file_upload(pdf_path)
        prompt = """\
Analyze the following academic paper text and extract its sections into a JSON format.

# Extraction Rules
1.  **Section Identification**: Identify all major sections of the paper, such as "Abstract," "Introduction," "Method," "Results," and "Conclusion."
2.  **Exclusions**: Exclude noise data such as author names, affiliations, and the entire "References" section. Do not include any text that follows the "References" or "Bibliography" heading.
3.  **JSON Format**: The output must be a single JSON object with a key named `sections`. The value of this key should be an array of section objects.
    * Each section object must have three keys: `id`, `title`, and `content`.
    * The `id` key should be a string representing the section number (e.g., "1", "2.1"). For sections without a number, like "Abstract," assign a logical ID (e.g., "0" for "Abstract" and "1" for "Introduction").
    * The `title` key should contain the section title as a string (e.g., "Abstract," "Introduction").
    * The `content` key should contain the plain text body of the section. Do not use Markdown or any other formatting within this text.
4.  **Important Note**: The content for `id` "0" should be the "Abstract"."
5.  **Quotation Mark Escaping**: When generating the JSON output, ensure all quotation marks inside the content value are escaped strictly according to JSON syntax.
    * Use a backslash followed by a half-width double quote (\").
    * Do not use full-width smart quotes (“, ”) or any other non-standard quotation marks.
    * Apply escaping consistently for all quotation marks in the content.
    * The final output must be valid JSON without syntax errors.

# output format
{
  "sections": [
    {
      "id": "0",
      "title": "Abstract",
      "content": "..."
    },
    {
      "id": "1",
      "title": "Introduction",
      "content": "..."
    },
    ...
  ]
}
"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                {"file_data": {"file_uri": file.uri, "mime_type": file.mime_type}},
                prompt,
            ]
        )

        json_text = self._parse_jsontext(response.text)

        # textは保存しておく
        if save_directory is not None:
            save_path = save_directory / (pdf_path.stem + ".txt")
        else:
            save_path = pdf_path.parent / (pdf_path.stem + ".txt")
        with save_path.open("w", encoding="utf-8") as f:
            f.write(json_text)

        return json_text

    def _file_upload(self, pdf_path: Path) -> object:
        """
        args:
            pdf_path(Path): ローカルのpaper pdfのパス
        returns:
            file(google.genai.types.File)
        """
        file = self.client.files.upload(file=pdf_path)
        logger.info(f"Uploaded: {file.uri}")

        return file

    def _parse_jsontext(self, response: str) -> str:
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            json_text = match.group(0)
            try:
                json.loads(json_text)
            except json.decoder.JSONDecodeError:
                logger.error("jsonテキストがパースできない形式です")

        return json_text

if __name__ == "__main__":
    pdf_extractor = PDFExtractor()
    pdf_path = Path("pdfs/cvpr1.pdf")
    pdf_extractor.extract(pdf_path)