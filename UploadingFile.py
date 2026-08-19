import os
from pathlib import Path

#from PIL import Image
from unstructured.partition.pdf import partition_pdf
#import json



outdirectory = Path("./ExtractedContents")
def extract_pdf_resources_for_rag(pdf_path: str):
    """
    Parses text chunks, markdown tables, and exports images/graphs 
    from a complex PDF file for multi-modal or standard RAG pipelines.
    """
    # 1. Create the output directories for extracted assets
    Filename = Path(pdf_path).stem
    print(f"File Name : {Filename}")

    images_output_dir = Path(outdirectory) / Filename / "images"
    tables_output_dir = Path(outdirectory) / Filename / "tables"
    content_output_dir = Path(outdirectory) / Filename / "content"

    images_output_dir.mkdir(parents=True, exist_ok=True)
    tables_output_dir.mkdir(parents=True, exist_ok=True)
    content_output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Parse the PDF with Layout Detection
    elements_by_page = partition_pdf(
        filename=pdf_path,
        strategy="hi_res",
        extract_images_in_pdf=True,
        infer_table_structure=True,
        chunking_strategy="by_page"
    )
    # 3. Group elements by their page numbers for sequential rendering

    texts = []
    metadata = []

    for page_num, page_elements in enumerate(elements_by_page, start=1):
        page_texts = []
        for el in page_elements:
            # Narrative text
            if el.category in ["NarrativeText", "Title"] and hasattr(el, "text"):
                page_texts.append(el.text.strip())

            # Tables → save as HTML
            if el.category == "Table" and hasattr(el, "text"):
                table_html_path = str(tables_output_dir / f"page_{page_num}_table.html")
                with open(table_html_path, "w", encoding="utf-8") as f:
                    f.write(el.text)  # unstructured returns HTML-like table text

            # Images → save to location
            if el.category == "Image" and hasattr(el, "metadata"):
                # image bytes are in el.metadata["image_base64"] if available
                import base64
                img_data = el.metadata.get("image_base64")
                if img_data:
                    img_bytes = base64.b64decode(img_data)
                    img_path = str(images_output_dir / f"page_{page_num}_image.png")
                    with open(img_path, "wb") as f:
                        f.write(img_bytes)

        # Save text per page
        if page_texts:
            text_path = str(content_output_dir / f"page_{page_num}.txt")
            with open(text_path, "w", encoding="utf-8") as f:
                f.write("\n".join(page_texts))

            # Add to embeddings pipeline
            for t in page_texts:
                texts.append(t)
                metadata.append({"category": "Text", "page_number": page_num})


# Example execution
if __name__ == "__main__":
    # Replace with the path to your source document file
    SAMPLE_PDF = "E:\\ML Live AI ML Projects\\Advance Document RAG\\Sample_Files\\sampleletterdoc.pdf" 
    
    
    # Ensure a mockup file exists for testing or replace directly with your path
    if os.path.exists(SAMPLE_PDF):
        parsed_rag_payload = extract_pdf_resources_for_rag(SAMPLE_PDF)
        
        # Display sample chunk payload structure for verification
        print("\n--- Sample RAG Ingestion Chunk ---")
        if parsed_rag_payload:
            print(parsed_rag_payload[:3])
    else:
        print(f"Please place a valid PDF file at '{SAMPLE_PDF}' to execute layout extraction.")
