from langchain_text_splitters import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup

def text_content_chunking(text, chunk_size, chunk_overlap):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
        )
    chunks = text_splitter.split_text(text)
    return chunks

'''
[HTML File] ➔ [DOM Parser] ➔ Group by Section (H1-H6) ➔ Prepend Context ➔ Text Chunks
'''
def html_content_chunking(html_content):
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

if __name__ == "__main__":
    # Example usage
    html_file="ExtractedContents\\sample20page\\tables\\table_page1_1.html"
    with open(html_file, 'r') as f:
        html_data = f.read()

    table_chunks = html_content_chunking(html_data)
    for chunk in table_chunks:
        print(chunk)