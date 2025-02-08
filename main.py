import pytesseract
from pdf2image import convert_from_path
import json
import os
from typing import List, Dict, Any
import logging
from datetime import datetime

class PDFOCRExtractor:
    def __init__(self, tesseract_path: str = None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def convert_pdf_to_images(self, pdf_path: str) -> List[Any]:
        """
        Convert PDF pages to images.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of PIL Image objects
        """
        try:
            self.logger.info(f"Converting PDF to images: {pdf_path}")
            return convert_from_path(pdf_path)
        except Exception as e:
            self.logger.error(f"Error converting PDF to images: {str(e)}")
            raise

    def extract_text_from_image(self, image: Any) -> Dict[str, Any]:
        try:
            # Extract text using pytesseract
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Process the OCR data
            extracted_data = {
                "text": [],
                "confidence_scores": [],
                "word_boxes": []
            }
            
            for i, text in enumerate(ocr_data['text']):
                if text.strip():  # Only process non-empty text
                    extracted_data["text"].append(text)
                    extracted_data["confidence_scores"].append(ocr_data['conf'][i])
                    extracted_data["word_boxes"].append({
                        "left": ocr_data['left'][i],
                        "top": ocr_data['top'][i],
                        "width": ocr_data['width'][i],
                        "height": ocr_data['height'][i]
                    })
            
            return extracted_data
        except Exception as e:
            self.logger.error(f"Error extracting text from image: {str(e)}")
            raise

    def process_pdf(self, pdf_path: str, output_path: str = None) -> Dict[str, Any]:
       
        try:
            # Convert PDF to images
            images = self.convert_pdf_to_images(pdf_path)
            
            # Process each page
            result = {
                "filename": os.path.basename(pdf_path),
                "processed_date": datetime.now().isoformat(),
                "total_pages": len(images),
                "pages": []
            }
            
            for i, image in enumerate(images):
                self.logger.info(f"Processing page {i+1}/{len(images)}")
                page_data = self.extract_text_from_image(image)
                result["pages"].append({
                    "page_number": i + 1,
                    "extracted_data": page_data
                })
            
            # Save to JSON file if output path is provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Results saved to: {output_path}")
            
            return result

    def batch_process_pdfs(self, input_dir: str, output_dir: str) -> List[Dict[str, Any]]:
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for filename in os.listdir(input_dir):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.json")
                
                try:
                    result = self.process_pdf(pdf_path, output_path)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing {filename}: {str(e)}")
                    continue
        
        return results



def main():
    """
    Main function to process a specific PDF file.
    """
    # Input and output file paths
    input_file = "input.pdf"
    output_file = "output.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        return
    
    try:
        # Initialize the extractor
        extractor = PDFOCRExtractor()
        
        # Process the PDF and save results
        print(f"Processing {input_file}...")
        result = extractor.process_pdf(input_file, output_file)
        
        # Print summary
        print("\nProcessing complete!")
        print(f"Total pages processed: {result['total_pages']}")
        print(f"Output saved to: {output_file}")
        
        # Print sample of extracted text from first page
        if result['pages']:
            first_page_text = ' '.join(result['pages'][0]['extracted_data']['text'])
            print("\nSample text from first page:")
            print(first_page_text[:200] + "..." if len(first_page_text) > 200 else first_page_text)
            
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")


if __name__ == "__main__":
    main()
