from langchain_text_splitters import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import pandas as pd
import utils


def text_content_chunking(text, chunk_size, chunk_overlap):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
        )
    chunks = text_splitter.split_text(text)
    chunk_ids=list(range(1, len(chunks) + 1))
    return chunks,chunk_ids

'''
[HTML File] ➔ [DOM Parser] ➔ Group by Section (H1-H6) ➔ Prepend Context ➔ Text Chunks
'''
def html_content_semantic_chunking(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract headers
    headers = [th.get_text(strip=True) for th in soup.find_all('th')]
    if not headers:
        # Fallback if no <th> elements exist
        first_row = soup.find('tr')
        headers = [td.get_text(strip=True) for td in first_row.find_all('td')] if first_row else []
    
    chunks = []
    # Loop over individual rows
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if not cells:
            continue  # Skip header rows
            
        cell_values = [cell.get_text(strip=True) for cell in cells]
        
        # Build a highly semantic sentence representation for embeddings
        row_segments = [f"{headers[i]}: {cell_values[i]}" for i in range(min(len(headers), len(cell_values)))]
        semantic_chunk = ", ".join(row_segments)
        
        chunks.append(semantic_chunk)
    return chunks

# Converting HTML table to markdown format for better chunking
def html_table_to_markdown(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract headers
    headers = [th.get_text(strip=True) for th in soup.find_all('th')]
    if not headers:
        # Fallback if no <th> elements exist
        first_row = soup.find('tr')
        headers = [td.get_text(strip=True) for td in first_row.find_all('td')] if first_row else []
    
    combined_content = ""
    # Loop over individual rows
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if not cells:
            continue  # Skip header rows
            
        cell_values = [cell.get_text(strip=True) for cell in cells]
        
        # Build a highly semantic sentence representation for embeddings
        row_segments = [f"{headers[i]}: {cell_values[i]}" for i in range(min(len(headers), len(cell_values)))]
        semantic_chunk = ", ".join(row_segments)
        
        combined_content+=semantic_chunk+"\n"
    return combined_content

# Chunking markdown content with RecursiveCharacterTextSplitter
def html_content_recursive_chunking_with_markdown(html_content,chunk_size, chunk_overlap):
    # 1. Convert HTML table to markdown
    markdown_table = html_table_to_markdown(html_content)

    # 2. Configure the RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n|", "\n", " ", ""]
    )
    chunk_ids=list(range(1, len(markdown_table) + 1))
    return splitter.split_text(markdown_table),chunk_ids

if __name__ == "__main__":
    # Example usage
    html_file="ExtractedContents\\sample20page\\tables\\table_page9_1.html"
    with open(html_file, 'r') as f:
        html_data = f.read()

    '''
    table_chunks = html_content_semantic_chunking(html_data)
    count=1
    for chunk in table_chunks:
        print(f"Chunk count: {count}")
        print(chunk)
        count += 1
    '''
    # Example usage of markdown chunking
    markdown_chunks = html_content_recursive_chunking_with_markdown(html_data, chunk_size=400, chunk_overlap=50)
    count = 1
    for chunk in markdown_chunks:
        print(f"Markdown Chunk count: {count}")
        print(chunk)
        count += 1