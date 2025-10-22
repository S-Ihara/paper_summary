import sys
from pathlib import Path
import time

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

    MAX_SUMMARY_PAPERS = 10

    summary_count = 0
    for pdf_path in pdf_directory.glob("*.pdf"):
        logger.debug(f"{pdf_path.stem}の要約を作ります")
        # textの抽出
        if not (text_directory / (pdf_path.stem + ".txt")).exists():
            while True:
                try:
                    pdf_extractor.extract(pdf_path, save_directory=text_directory, save=True)
                    logger.info(f"{text_directory}に{pdf_path.stem}のtextを保存しました")
                    break
                except Exception as e:
                    logger.error(f"エラーが発生しました: {e}")
                    if e.response.status_code == 400:
                        logger.error("invalud argumentらしいですが、よくわかっていないです。再開させてもうまくいかないのでスキップします。")
                        break
                    logger.error("その他のエラーです。5秒後に再試行します")
                    time.sleep(5)
                    continue

        # 要約の作成
        text_path = text_directory / (pdf_path.stem + ".txt")
        if not (md_directory / (pdf_path.stem + ".md")).exists():
            while True:
                try:
                    paper_summarizer.simple_summary(text_path, save_directory=md_directory, save=True)
                    logger.info(f"{md_directory}に{pdf_path.stem}の要約を保存しました")
                    break
                except FileNotFoundError:
                    logger.warning("ファイルが見つかりませんでした。ここでテキスト抽出をとりあえず飛ばしている可能性が高いので一旦スキップさせます。")
                    break
                except Exception as e:
                    logger.error(f"エラーが発生しました: {e}、5秒後に再試行します")
                    time.sleep(5)
                    continue
            summary_count += 1
        else:
            logger.debug("すでに要約があるみたいです")

        if summary_count >= MAX_SUMMARY_PAPERS:
            logger.info("最大要約数に達したので終了します")
            break

    logger.info("終了しました")

if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    main()