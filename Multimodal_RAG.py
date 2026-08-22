
'''
To create a muli modal rag system for PDF
The documents can have content in the form of pdfs, html tables or base64 images.
We need to design that can extract these subcontent and can convert it into embeddings.
The following diagram illustrates the process of creating a vector database for a multi modal rag system.   

                       ┌──► [Text Chunks] ──► Generate Embeddings ───────┐
                       │                                                 ▼
[PDF] ──► Unstructured ├──► [HTML Tables] ──► VLM Summarize ──► Embed ──► [Vector DB (Chroma)]
(Partitioning)         │                                                 ▲
                       └──► [Base64 Images] ─► VLM Summarize ──► Embed ──┘
                       
'''

import os
import fitz  # PyMuPDF
import os
from pathlib import Path

def create_directories(file_path: str,base_path: str):
    """
    Creates the necessary output directories for extracted assets.
    """
    Filename = Path(file_path).stem
    print(f"File Name : {Filename}")
    images_output_dir = Path(base_path) / Filename / "images"
    tables_output_dir = Path(base_path) / Filename / "tables"
    content_output_dir = Path(base_path) / Filename / "contents"

    images_output_dir.mkdir(parents=True, exist_ok=True)
    tables_output_dir.mkdir(parents=True, exist_ok=True)
    content_output_dir.mkdir(parents=True, exist_ok=True)

    return images_output_dir, tables_output_dir, content_output_dir

def extract_pdf_data(pdf_path, image_dir,table_dir,content_dir):
    # Create the folder to save images if it doesn't exist
        
    doc = fitz.open(pdf_path)
    full_extracted_content = []
    

    # Loop through each page in the PDF document
    for page_num in range(len(doc)):
        page = doc[page_num]
        tabs = page.find_tables()
        
        # Extract all tabular data in HTML format and save it in a different location
        for i, table in enumerate(tabs):
            # 1. Extract table data as HTML
            #html_content = table.to_markdown()  
            # Or generate custom HTML from table.extract()
            # Alternately, PyMuPDF allows direct HTML export structural extraction:
            html_table = "border='1'>\n"
            for row in table.extract():
                html_table += "  <tr>\n"
                for cell in row:
                    html_table += f"    <td>{cell if cell else ''}</td>\n"
                html_table += "  </tr>\n"
            html_table += "</table>"
            
            # Full HTML boilerplate
            full_html = f"<html><body>\n{html_table}\n</body></html>"
            
            # 2. Save HTML to a different location
            html_filename = f"table_page{page_num+1}_{i+1}.html"
            html_filepath = os.path.join(table_dir, html_filename)
            with open(html_filepath, "w", encoding="utf-8") as f:
                f.write(full_html)
            
            # 3. Get table boundary box (Bbox)
            bbox = table.bbox  # (x0, y0, x1, y1)
            
            # 4. Redact/Cover the original table content
            page.add_redact_annot(bbox, fill=(1, 1, 1))  # White rectangle box
            page.apply_redactions()
            
            # 5. Insert the link in place of the table
            link_rect = fitz.Rect(bbox[0], bbox[1], bbox[0] + 150, bbox[1] + 20) 
            
            # Add visible text for the link
            page.insert_text(
                link_rect.tl, 
                "[View Extracted Table]", 
                color=(0, 0, 1), 
                fontsize=11
            )
            
            # Insert the actual hyperlink pointing to the local HTML file
            # Note: For web deployment, replace this with a web URL
            link_data = {
                "kind": fitz.LINK_URI,
                "from": link_rect,
                "uri": f"file:///{os.path.abspath(html_filepath)}"
            }
            page.insert_link(link_data)
        
        # 2. Fetch text fragments with their structural position data
        # "blocks" format returns tuples: (x0, y0, x1, y1, "text/image_flag", block_no, block_type)
        # block_type 0 = Text, block_type 1 = Image
        text_blocks = page.get_text("blocks")
        
        # 2. Sort structural elements from top to bottom, then left to right
        text_blocks.sort(key=lambda b: (b[1], b[0]))
        
                        
        elements = []
        
        # 2. Extract regular text blocks
        text_blocks = page.get_text("blocks")
        for b in text_blocks:
            elements.append({
                "type": "text",
                "sorting_key": (b[1], b[0]),  # Sort by Y-top, then X-left coordinate
                "content": b[4]               # The actual text string
            })
            
        # 3. Extract and save embedded images
        image_info_list = page.get_images(full=True)
        for img_idx, img_meta in enumerate(image_info_list):
            # FIX: Extract the integer xref ID which is always the FIRST item in the metadata tuple
            xref = img_meta[0] 
            
            try:
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue
                    
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Build unique file name and save the file
                img_name = f"page_{i+1}_img_{img_idx+1}_{xref}.{image_ext}"
                img_path = os.path.join(image_dir, img_name)
                
                # Write the raw bytes to your disk
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
                    
                # Find where this image is physically drawn on the page
                rects = page.get_image_rects(xref)
                if rects:
                    target_rect = rects[0] # Grab its layout box position
                    elements.append({
                        "type": "image",
                        "sorting_key": (target_rect.y0, target_rect.x0), # Sort via screen position
                        "content": f"\n[Image Link: {img_path}]\n"    # Injected file path text
                    })
            except Exception as e:
                # Catches encrypted or corrupted image streams gracefully
                print(f"Skipping image xref {xref} due to error: {e}")
                continue

        # 4. Sort everything combined by its actual vertical layout flow
        elements.sort(key=lambda x: x["sorting_key"])
        
        # 5. Append structural content safely to final payload
        '''for el in elements:
            full_output.append(el["content"])'''
        
        page_content = f"--- Page {page_num + 1} ---\n"
        for block in text_blocks:
            # Check if block is a text block
            if block[6] == 0: 
                text_content = block[4].strip()
                if text_content:
                    page_content += text_content + "\n"

        content_name = f"content_page{page_num+1}.txt"
        content_path = os.path.join(content_dir, content_name)
        with open(content_path, "w",encoding="utf-8") as content_file:
            content_file.write(page_content)
        print(page_content)         
        full_extracted_content.append(page_content)   
    doc.close()
    return "".join(full_extracted_content)

# Example execution
if __name__ == "__main__":
    # Replace with the path to your source document file
    SAMPLE_PDF = "E:\\ML Live AI ML Projects\\Document RAG\\Sample_Files\\sampleimagedoc.pdf" 
    
    
    # Ensure a mockup file exists for testing or replace directly with your path
    if os.path.exists(SAMPLE_PDF):
        base_output_dir = "E:\\ML Live AI ML Projects\\Document RAG\\ExtractedContents" 
        images_dir, tables_dir, content_dir = create_directories(SAMPLE_PDF, base_output_dir)
        extracted_content = extract_pdf_data(SAMPLE_PDF, images_dir, tables_dir, content_dir)
        print("Extraction completed. Extracted content:")
        print(extracted_content)
    else:
        print(f"Please place a valid PDF file at '{SAMPLE_PDF}' to execute layout extraction.")