import os
import logging
import aiohttp
import aiofiles
import asyncio
import fitz  # PyMuPDF
import pikepdf
from pathlib import Path
from typing import List, Optional, Union
from tempfile import NamedTemporaryFile

class PDFDownloader:
    """Class for downloading PDFs from URLs to a specified target folder."""
    
    def __init__(self, target_folder: str):
        """Initialize the PDF downloader.
        
        Args:
            target_folder: Path to the folder where PDFs will be saved
        """
        self.target_folder = Path(target_folder)
        self._setup_target_folder()
        self._setup_logging()
    
    def _setup_target_folder(self):
        """Create the target folder if it doesn't exist."""
        self.target_folder.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler('pdf_downloads.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def _get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        return url.split('/')[-1]
    
    async def _download_pdf(self, session: aiohttp.ClientSession, url: str) -> Optional[Path]:
        """Download a single PDF file."""
        filename = self._get_filename_from_url(url)
        filepath = self.target_folder / filename
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    if content[:4] == b'%PDF':  # Basic check if it's a PDF
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)
                        logging.info(f"Successfully downloaded: {filename}")
                        return filepath
                    else:
                        logging.error(f"Downloaded content is not a PDF: {url}")
                        return None
                else:
                    logging.error(f"Failed to download {url}, status: {response.status}")
                    return None
        except Exception as e:
            logging.error(f"Error downloading {url}: {str(e)}")
            return None
    
    async def _download_all(self, urls: List[str]) -> List[Path]:
        """Download multiple PDFs concurrently."""
        async with aiohttp.ClientSession() as session:
            tasks = [self._download_pdf(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return [path for path in results if path is not None]
    
    def download_pdfs(self, urls: List[str], highlight_words: Union[str, List[str]] = None) -> List[Path]:
        """Download PDFs from the given URLs and optionally highlight words.
        
        Args:
            urls: List of URLs to PDFs to download
            highlight_words: Word or list of words to highlight in the PDFs
            
        Returns:
            List of paths to successfully downloaded files
        """
        if not urls:
            logging.warning("No URLs provided for download")
            return []
            
        logging.info(f"Starting download of {len(urls)} PDFs to {self.target_folder}")
        
        # Run the async download
        loop = asyncio.get_event_loop()
        downloaded_files = loop.run_until_complete(self._download_all(urls))
        
        # Highlight words if specified
        if highlight_words and downloaded_files:
            if isinstance(highlight_words, str):
                highlight_words = [highlight_words]
            
            highlighted_files = []
            for pdf_path in downloaded_files:
                if self._highlight_words(pdf_path, highlight_words):
                    highlighted_files.append(pdf_path)
                else:
                    logging.warning(f"Skipping highlighting for {pdf_path} due to errors")
        
        logging.info(f"Successfully downloaded {len(downloaded_files)} PDFs")
        return downloaded_files
        
    def _repair_pdf(self, pdf_path: Path) -> Optional[Path]:
        """Attempt to repair a PDF file.
        
        Args:
            pdf_path: Path to the PDF file to repair
            
        Returns:
            Path to repaired PDF if successful, None if repair failed
        """
        try:
            # Create a temporary file for the repaired PDF
            with NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                repaired_path = Path(tmp_file.name)
            
            # Try to repair the PDF
            with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
                pdf.save(repaired_path)
            
            return repaired_path
        except Exception as e:
            logging.error(f"Could not repair PDF {pdf_path}: {str(e)}")
            if 'repaired_path' in locals() and repaired_path.exists():
                repaired_path.unlink()  # Clean up temp file if it exists
            return None
    
    def _highlight_words(self, pdf_path: Path, words: List[str]) -> bool:
        """Highlight words in a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            words: List of words to highlight
            
        Returns:
            bool: True if highlighting was successful, False otherwise
        """
        try:
            # First try to open and validate the PDF
            try:
                doc = fitz.open(pdf_path)
                # Quick validation - try to access first page
                _ = doc[0]
            except Exception as e:
                logging.warning(f"Cannot open PDF {pdf_path}, attempting repair: {str(e)}")
                if 'doc' in locals() and doc:
                    doc.close()
                
                # Try to repair the PDF
                repaired_path = self._repair_pdf(pdf_path)
                if repaired_path is None:
                    return False
                
                try:
                    doc = fitz.open(repaired_path)
                    _ = doc[0]  # Validate repaired PDF
                    logging.info(f"Successfully repaired {pdf_path}")
                except Exception as e:
                    logging.error(f"Cannot open repaired PDF {pdf_path}: {str(e)}")
                    if 'doc' in locals() and doc:
                        doc.close()
                    repaired_path.unlink()  # Clean up temp file
                    return False
                
                # Use repaired PDF for highlighting
                pdf_path = repaired_path
                
            num_highlights = 0
            has_errors = False
            
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    for word in words:
                        try:
                            # Search for word on page
                            instances = page.search_for(word)
                            
                            # Add yellow highlight for each instance
                            for inst in instances:
                                try:
                                    highlight = page.add_highlight_annot(inst)
                                    highlight.set_colors(stroke=(1, 1, 0))  # Yellow highlight
                                    highlight.update()
                                    num_highlights += 1
                                except Exception as e:
                                    logging.warning(f"Could not highlight instance in {pdf_path} on page {page_num + 1}: {str(e)}")
                                    has_errors = True
                        except Exception as e:
                            logging.warning(f"Could not search for '{word}' in {pdf_path} on page {page_num + 1}: {str(e)}")
                            has_errors = True
                except Exception as e:
                    logging.warning(f"Could not process page {page_num + 1} in {pdf_path}: {str(e)}")
                    has_errors = True
                    continue
            
            if num_highlights > 0:
                try:
                    # Save with highlights
                    highlighted_path = pdf_path.parent / f"highlighted_{pdf_path.name}"
                    doc.save(highlighted_path)
                    status = "with some errors" if has_errors else "successfully"
                    logging.info(f"Added {num_highlights} highlights {status} to {highlighted_path}")
                except Exception as e:
                    logging.error(f"Could not save highlighted PDF {pdf_path}: {str(e)}")
                    return False
            else:
                logging.info(f"No instances of search terms found in {pdf_path}")
                
            doc.close()
            return True
        except Exception as e:
            logging.error(f"Error highlighting PDF {pdf_path}: {str(e)}")
            return False


if __name__ == "__main__":
    # Example usage
    downloader = PDFDownloader("downloaded_pdfs")
    urls = [
        "https://zoek.officielebekendmakingen.nl/kst-36410-VIII-2.pdf",
        "https://zoek.officielebekendmakingen.nl/blg-996338.pdf"
    ]
    # Download and highlight "onderwijs" in the PDFs
    downloaded = downloader.download_pdfs(urls, highlight_words="onderwijs")
    print(f"Downloaded files: {[str(p) for p in downloaded]}")