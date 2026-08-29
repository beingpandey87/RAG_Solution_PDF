import argparse
import base64
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from unstructured.partition.pdf import partition_pdf


TEXT_CATEGORIES = {
    "Title",
    "NarrativeText",
    "UncategorizedText",
    "ListItem",
    "Header",
    "Footer",
    "Address",
    "EmailAddress",
    "FigureCaption",
    "Formula",
    "CodeSnippet",
}


def metadata_to_dict(element: Any) -> dict:
    """
    Convert Unstructured element metadata to a dictionary.
    """
    if hasattr(element.metadata, "to_dict"):
        return element.metadata.to_dict()

    return dict(element.metadata.__dict__)


def save_base64_image(
    image_base64: str,
    output_path: Path,
) -> None:
    """
    Decode and save a Base64-encoded image.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image_bytes = base64.b64decode(image_base64)
    output_path.write_bytes(image_bytes)


def extract_pdf_page_wise(
    pdf_path: str,
    output_directory: str,
    languages: list[str] =["eng"],
) -> dict:
    """
    Extract text, tables, images, graphs and metadata page by page.

    Parameters
    ----------
    pdf_path:
        Input PDF path.

    output_directory:
        Directory where extracted data will be stored.

    languages:
        OCR languages, for example ["eng"] or ["eng", "hin"].

    Returns
    -------
    dict:
        Page-wise structured extraction result.
    """

    pdf_file = Path(pdf_path)

    output_root = "ExtractedContents/"+Path(pdf_path).stem

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_file}")


    images_directory = Path(output_root+"/images")
    tables_directory = Path(output_root +"/tables")
    pages_directory = Path(output_root + "/pages")

    images_directory.mkdir(parents=True,exist_ok=True)
    tables_directory.mkdir(parents=True,exist_ok=True)
    pages_directory.mkdir(parents=True,exist_ok=True)


    elements = partition_pdf(
        filename=str(pdf_file),
        strategy="hi_res",
        infer_table_structure=True,
        include_page_breaks=True,
        languages=languages,
        extract_image_block_types=["Image", "Table"],
        extract_image_block_to_payload=True,
        unique_element_ids=True,
    )

    pages = defaultdict(
        lambda: {
            "page_number": None,
            "text": [],
            "tables": [],
            "images": [],
            "graphs_and_figures": [],
            "figure_captions": [],
            "formulas": [],
            "elements": [],
        }
    )

    for element_index, element in enumerate(elements, start=1):
        
        metadata = metadata_to_dict(element)
        
        page_number = metadata.get("page_number")

        # Some elements, such as PageBreak, may not contain page numbers.
        if page_number is None:
            continue

        page_number = int(page_number)
        pages[page_number]["page_number"] = page_number

        category = getattr(
            element,
            "category",
            element.__class__.__name__,
        )

        element_text = getattr(element, "text", "") or ""
        element_id = getattr(element, "id", None)

        coordinates = metadata.get("coordinates")
        image_base64 = metadata.get("image_base64")
        image_mime_type = metadata.get(
            "image_mime_type",
            "image/jpeg",
        )
        text_as_html = metadata.get("text_as_html")

        element_record = {
            "element_index": element_index,
            "element_id": element_id,
            "category": category,
            "text": element_text,
            "page_number": page_number,
            "coordinates": coordinates,
            "metadata": {
                key: value
                for key, value in metadata.items()
                if key != "image_base64"
            },
        }

        pages[page_number]["elements"].append(element_record)

        # Text extraction
        if category in TEXT_CATEGORIES and element_text.strip():
            pages[page_number]["text"].append(
                {
                    "category": category,
                    "text": element_text,
                    "coordinates": coordinates,
                }
            )

        # Figure caption extraction
        if category == "FigureCaption":
            pages[page_number]["figure_captions"].append(
                {
                    "text": element_text,
                    "coordinates": coordinates,
                }
            )

        # Formula extraction
        if category == "Formula":
            pages[page_number]["formulas"].append(
                {
                    "text": element_text,
                    "coordinates": coordinates,
                }
            )

        # Table extraction
        if category == "Table":
            table_number = len(pages[page_number]["tables"]) + 1

            table_basename = (
                f"page_{page_number:04d}_table_{table_number:03d}"
            )

            table_html_path = None

            if text_as_html:
                table_html_path = (
                    tables_directory / f"{table_basename}.html"
                )

                table_html_path.write_text(
                    text_as_html,
                    encoding="utf-8",
                )

            table_image_path = None

            if image_base64:
                extension = (
                    ".png"
                    if "png" in image_mime_type.lower()
                    else ".jpg"
                )

                table_image_path = (
                    tables_directory
                    / f"{table_basename}{extension}"
                )

                save_base64_image(
                    image_base64,
                    table_image_path,
                )

            pages[page_number]["tables"].append(
                {
                    "table_number": table_number,
                    "text": element_text,
                    "html": text_as_html,
                    "coordinates": coordinates,
                    "html_file": (
                        str(table_html_path)
                        if table_html_path
                        else None
                    ),
                    "image_file": (
                        str(table_image_path)
                        if table_image_path
                        else None
                    ),
                }
            )

        # Image and graph extraction
        if category in {"Image", "Figure", "Picture"}:
            image_number = len(pages[page_number]["images"]) + 1

            image_basename = (
                f"page_{page_number:04d}_"
                f"image_{image_number:03d}"
            )

            image_path = None

            if image_base64:
                extension = (
                    ".png"
                    if "png" in image_mime_type.lower()
                    else ".jpg"
                )

                image_path = (
                    images_directory
                    / f"{image_basename}{extension}"
                )

                save_base64_image(
                    image_base64,
                    image_path,
                )

            image_record = {
                "image_number": image_number,
                "category": category,
                "text": element_text,
                "coordinates": coordinates,
                "image_file": (
                    str(image_path)
                    if image_path
                    else None
                ),
            }

            pages[page_number]["images"].append(image_record)

            # Unstructured commonly classifies charts and graphs as
            # Image/Figure elements. Therefore, they are also stored here.
            pages[page_number][
                "graphs_and_figures"
            ].append(image_record)

    sorted_pages = {
        str(page_number): pages[page_number]
        for page_number in sorted(pages)
    }

    final_result = {
        "source_pdf": str(pdf_file),
        "total_elements": len(elements),
        "total_pages_extracted": len(sorted_pages),
        "pages": sorted_pages,
    }

    # Save combined JSON
    combined_json_path = Path(output_root +"document.json")

    combined_json_path.write_text(
        json.dumps(
            final_result,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    # Save one text file per page
    for page_number, page_data in sorted_pages.items():
        page_number_int = int(page_number)


        page_text = "\n\n".join(
            text_element["text"]
            for text_element in page_data["text"]
            if text_element["text"].strip()
        )

        page_text_path = (
            Path(output_root)
            / f"page_{page_number_int:04d}.txt"
        )

        page_text_path.write_text(
            page_text,
            encoding="utf-8",
        )

    print("\nExtraction completed.")
    print(f"Total elements: {len(elements)}")
    print(f"Pages extracted: {len(sorted_pages)}")
    #print(f"Output directory: {output_root.resolve()}")
    print(f"Combined JSON: {combined_json_path.resolve()}")

    return final_result


def main() -> None:
    '''parser = argparse.ArgumentParser(
        description=(
            "Extract PDF text, images, graphs and tables "
            "page by page using Unstructured."
        )
    )

    parser.add_argument(
        "C:\\RAG_Practice_Advance\\SampleFiles\\sampleletterdoc.pdf",
        help="Path of the input PDF file",
    )

    parser.add_argument(
        "--output",
        default="C:\\RAG_Practice_Advance\\ExtractedContents",
        help="Output directory. Default: output",
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        default=["eng"],
        help="OCR languages. Example: eng hin",
    )

    arguments = parser.parse_args()
    '''
    extract_pdf_page_wise(
        pdf_path="C:\\RAG_Practice_Advance\\SampleFiles\\sampleletterdoc.pdf",
        output_directory="C:\\RAG_Practice_Advance\\ExtractedContents",
        languages=["eng"],
    )


if __name__ == "__main__":
    main()