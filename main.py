from pathlib import Path

from loguru import logger

from paper_tools.pdf_extractor import PDFExtractor
from paper_tools.paper_summary import PaperSummarizer
from config import API_KEY

def main():
    target_directory = Path("./papers")
    pdf_directory = target_directory / "pdf"
    text_directory = target_directory / "text"
    md_directory = target_directory / "markdown"

    if not target_directory.exists():
        target_directory.mkdir()
        if not pdf_directory.exists():
            pdf_directory.mkdir()
        if not text_directory.exists():
            text_directory.mkdir()
        if not md_directory.exists():
            md_directory.mkdir()

    pdf_extractor = PDFExtractor(api_key=API_KEY)
    paper_summarizer = PaperSummarizer(api_key=API_KEY)

    for pdf_path in pdf_directory.glob("*.pdf"):
        logger.info(f"{pdf_path.stem}の要約を作ります")
        # textの抽出
        if not (text_directory / (pdf_path.stem + ".txt")).exists():
            pdf_extractor.extract(pdf_path, save_directory=text_directory, save=True)
            logger.info(f"{text_directory}に{pdf_path.stem}のtextを保存しました")

        # 要約の作成
        text_path = text_directory / (pdf_path.stem + ".txt")
        if not (md_directory / (pdf_path.stem + ".md")).exists():
            paper_summarizer.simple_summary(text_path, save_directory=md_directory, save=True)
            logger.info(f"{md_directory}に{pdf_path.stem}の要約を保存しました")
    
    logger.info("完了")

if __name__ == "__main__":
    main()