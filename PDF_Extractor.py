
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
            html_filename = f"table_page_{page_num+1}_{i+1}.html"
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
                "Table Link : "+html_filepath, 
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
        
        # 2. Fetch text fragments with their structural position data
        final_output=f"\n--- Page {page_num + 1} ---\n"
        
        # 2. Extract layout structure containing text and images simultaneously
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])
        image_counter=1
        for block in blocks:
            # Check if block is a Text block (type 0)
            if block.get("type") == 0:
                for line in block.get("lines", []):
                    line_text = "".join([span.get("text", "") for span in line.get("spans", [])])
                    final_output+=(line_text + "\n")
            
            # Check if block is an Image block (type 1)
            elif block.get("type") == 1:
                image_bytes = block.get("image")
                image_ext = block.get("ext", "png") # Default extension type
                
                if image_bytes:
                    # Formulate unique path name
                    img_filename = f"page_{page_num + 1}_img_{image_counter}.{image_ext}"
                    img_filepath = os.path.join(image_dir, img_filename)
                    
                    # 3. Write raw image byte data to disk
                    try:
                        with open(img_filepath, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        # 4. Inject structural markdown file path inline 
                        final_output+=(f"\n[Image Link: {img_filepath}]\n")
                        image_counter += 1
                    except Exception as e:
                        print(f"Error saving image {img_filename}: {e}")
                        

        content_name = f"content_page_{page_num+1}.txt"
        content_path = os.path.join(content_dir, content_name)
        with open(content_path, "w",encoding="utf-8") as content_file:
            content_file.write(final_output)
        print(final_output)         
        full_extracted_content.append(final_output)   
    doc.close()
    return "".join(full_extracted_content)

# Example execution
if __name__ == "__main__":
    # Replace with the path to your source document file
    SAMPLE_PDF = "C:\\RAG_Practice_Advance\\SampleFiles\\sample20page.pdf" 
    import utils
    
    # Ensure a mockup file exists for testing or replace directly with your path
    if os.path.exists(SAMPLE_PDF):
        base_output_dir = "C:\\RAG_Practice_Advance\\ExtractedContents" 
        file_name,images_dir, tables_dir, content_dir = utils.create_directories(SAMPLE_PDF, base_output_dir)
        extracted_content = extract_pdf_data(SAMPLE_PDF, images_dir, tables_dir, content_dir)
        print("Extraction completed. Extracted content:")
        print(extracted_content)
    else:
        print(f"Please place a valid PDF file at '{SAMPLE_PDF}' to execute layout extraction.")