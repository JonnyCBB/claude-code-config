#!/usr/bin/env python3
"""Google Docs Operations Script — CRUD operations on Google Documents."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import google.auth
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    _HAS_GOOGLE = True
except ImportError:
    _HAS_GOOGLE = False

SKILL_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = SKILL_DIR / ".venv"
VENV_PYTHON = VENV_DIR / "bin" / "python"
REQUIRED_PACKAGES = ["google-auth", "google-auth-httplib2", "google-api-python-client"]
REQUIRED_SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
]

_SOLID_BORDER = {
    "width": {"magnitude": 1, "unit": "PT"},
    "dashStyle": "SOLID",
    "color": {"color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}},
}

_HEADING_SHIFT = {
    "HEADING_1": "TITLE",
    "HEADING_2": "HEADING_1",
    "HEADING_3": "HEADING_2",
    "HEADING_4": "HEADING_3",
    "HEADING_5": "HEADING_4",
    "HEADING_6": "HEADING_5",
}

_MONOSPACE_FONTS = frozenset({"Courier New", "Consolas", "Monaco", "Courier"})


# --- Credential & Service Helpers ---


def _get_credentials() -> Any:
    creds, _ = google.auth.default(scopes=REQUIRED_SCOPES)
    return creds


def _get_docs_service(credentials: Any | None = None) -> Any:
    return build("docs", "v1", credentials=credentials or _get_credentials())


def _get_drive_service(credentials: Any | None = None) -> Any:
    return build("drive", "v3", credentials=credentials or _get_credentials())


# --- Utility Helpers ---


def _find_end_index(content: list[dict]) -> int:
    return max((el["endIndex"] for el in content if "endIndex" in el), default=1)


def _find_tab_by_id(tabs: list[dict], target_id: str) -> dict | None:
    for tab in tabs:
        if tab.get("tabProperties", {}).get("tabId") == target_id:
            return tab.get("documentTab", {})
        if found := _find_tab_by_id(tab.get("childTabs", []), target_id):
            return found
    return None


# --- Formatting Request Builders ---


def _cleanup_named_ranges(doc: dict) -> list[dict]:
    requests: list[dict] = []
    for range_data in doc.get("namedRanges", {}).values():
        for nr in range_data.get("namedRanges", []):
            if nr_id := nr.get("namedRangeId"):
                requests.append({"deleteNamedRange": {"namedRangeId": nr_id}})
    return requests


def _build_heading_shift_requests(content: list[dict]) -> list[dict]:
    requests: list[dict] = []
    for element in content:
        if "paragraph" not in element:
            continue
        style_type = (
            element["paragraph"].get("paragraphStyle", {}).get("namedStyleType", "")
        )
        if style_type in _HEADING_SHIFT:
            requests.append(
                {
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": element["startIndex"],
                            "endIndex": element["endIndex"],
                        },
                        "paragraphStyle": {
                            "namedStyleType": _HEADING_SHIFT[style_type]
                        },
                        "fields": "namedStyleType",
                    }
                }
            )
    return requests


def _build_global_font_request(end_index: int, text_font: str) -> dict:
    return {
        "updateTextStyle": {
            "range": {"startIndex": 1, "endIndex": end_index - 1},
            "textStyle": {"weightedFontFamily": {"fontFamily": text_font}},
            "fields": "weightedFontFamily",
        }
    }


def _build_paragraph_style_requests(
    content: list[dict], text_font: str, code_font: str
) -> list[dict]:
    requests: list[dict] = []
    for element in content:
        if "paragraph" not in element:
            continue
        paragraph = element["paragraph"]
        paragraph_style = paragraph.get("paragraphStyle", {})
        is_blockquote = (
            paragraph_style.get("namedStyleType") == "NORMAL_TEXT"
            and paragraph_style.get("indentFirstLine", {}).get("magnitude", 0) > 0
        )

        for para_el in paragraph.get("elements", []):
            if "textRun" not in para_el:
                continue
            text_style = para_el["textRun"].get("textStyle", {})
            start_idx = para_el["startIndex"]
            end_idx = para_el["endIndex"]

            font_family = text_style.get("weightedFontFamily", {}).get("fontFamily")
            if font_family in _MONOSPACE_FONTS:
                requests.append(
                    {
                        "updateTextStyle": {
                            "range": {
                                "startIndex": start_idx,
                                "endIndex": end_idx,
                            },
                            "textStyle": {
                                "weightedFontFamily": {"fontFamily": code_font}
                            },
                            "fields": "weightedFontFamily",
                        }
                    }
                )
            elif is_blockquote:
                requests.append(
                    {
                        "updateTextStyle": {
                            "range": {
                                "startIndex": start_idx,
                                "endIndex": end_idx,
                            },
                            "textStyle": {"italic": True},
                            "fields": "italic",
                        }
                    }
                )
    return requests


def _build_table_style_requests(content: list[dict], text_font: str) -> list[dict]:
    requests: list[dict] = []
    for element in content:
        if "table" not in element:
            continue
        table = element["table"]
        table_start_index = element.get("startIndex")

        for row_idx, row in enumerate(table.get("tableRows", [])):
            is_header = row_idx == 0
            for col_idx, cell in enumerate(row.get("tableCells", [])):
                cell_style: dict[str, Any] = {
                    side: _SOLID_BORDER
                    for side in (
                        "borderTop",
                        "borderBottom",
                        "borderLeft",
                        "borderRight",
                    )
                }
                fields = "borderTop,borderBottom,borderLeft,borderRight"

                if is_header:
                    cell_style["backgroundColor"] = {
                        "color": {"rgbColor": {"red": 0.9, "green": 0.9, "blue": 0.9}}
                    }
                    fields += ",backgroundColor"

                requests.append(
                    {
                        "updateTableCellStyle": {
                            "tableRange": {
                                "tableCellLocation": {
                                    "tableStartLocation": {"index": table_start_index},
                                    "rowIndex": row_idx,
                                    "columnIndex": col_idx,
                                },
                                "rowSpan": 1,
                                "columnSpan": 1,
                            },
                            "tableCellStyle": cell_style,
                            "fields": fields,
                        }
                    }
                )

                for cell_content in cell.get("content", []):
                    if "paragraph" not in cell_content:
                        continue
                    for para_el in cell_content["paragraph"].get("elements", []):
                        if "textRun" not in para_el:
                            continue
                        start_idx = para_el["startIndex"]
                        end_idx = para_el["endIndex"]
                        text_style: dict[str, Any] = {
                            "weightedFontFamily": {"fontFamily": text_font},
                        }
                        style_fields = "weightedFontFamily"
                        if is_header:
                            text_style["bold"] = True
                            style_fields += ",bold"
                        requests.append(
                            {
                                "updateTextStyle": {
                                    "range": {
                                        "startIndex": start_idx,
                                        "endIndex": end_idx,
                                    },
                                    "textStyle": text_style,
                                    "fields": style_fields,
                                }
                            }
                        )
    return requests


# --- Core Operations ---


def upload_image_to_drive(image_data: bytes, filename: str, credentials: Any) -> str:
    drive_service = _get_drive_service(credentials)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        temp_file.write(image_data)
        temp_path = Path(temp_file.name)
    try:
        media = MediaFileUpload(str(temp_path), mimetype="image/png")
        drive_file = (
            drive_service.files()
            .create(body={"name": filename}, media_body=media, fields="id")
            .execute()
        )
        file_id = drive_file.get("id")
        drive_service.permissions().create(
            fileId=file_id,
            body={"type": "domain", "role": "reader", "domain": "example.com"},
        ).execute()
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    finally:
        temp_path.unlink()


def convert_markdown_to_docx(
    markdown_file: str, output_docx: str | None = None
) -> Path:
    markdown_path = Path(markdown_file)
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_file}")

    output_path = (
        Path(output_docx) if output_docx else markdown_path.with_suffix(".docx")
    )
    print(f"Converting {markdown_path.name} to .docx...")

    try:
        subprocess.run(
            [
                "pandoc",
                "-f",
                "markdown-auto_identifiers-header_attributes",
                str(markdown_path),
                "-o",
                str(output_path),
                "--standalone",
                "--columns=1000",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Created {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error running Pandoc: {e.stderr}")
        raise
    except FileNotFoundError:
        print("Error: Pandoc not found. Please install it:")
        print("  brew install pandoc")
        raise


def apply_font_formatting(
    document_id: str,
    credentials: Any,
    text_font: str = "Proxima Nova",
    code_font: str = "Consolas",
) -> None:
    docs_service = _get_docs_service(credentials)
    print(f"\nApplying font formatting ({text_font} for text, {code_font} for code)...")

    try:
        doc = docs_service.documents().get(documentId=document_id).execute()
        content = doc.get("body").get("content")
        end_index = _find_end_index(content)

        requests = [
            *_cleanup_named_ranges(doc),
            *_build_heading_shift_requests(content),
            _build_global_font_request(end_index, text_font),
            *_build_paragraph_style_requests(content, text_font, code_font),
            *_build_table_style_requests(content, text_font),
        ]

        if requests:
            docs_service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            ).execute()
            print("Applied custom font formatting")
    except HttpError as e:
        print(f"Warning: Could not apply font formatting: {e}")
        print("  The document was created successfully, but font may be default.")


def upload_to_google_drive(
    docx_file: str | Path,
    doc_name: str | None = None,
    convert_to_gdoc: bool = True,
    folder_id: str | None = None,
    apply_font: bool = True,
) -> dict:
    docx_path = Path(docx_file)
    if not docx_path.exists():
        raise FileNotFoundError(f"DOCX file not found: {docx_file}")

    if doc_name is None:
        doc_name = docx_path.stem

    print("\nUploading to Google Drive...")

    try:
        credentials = _get_credentials()
        drive_service = _get_drive_service(credentials)

        file_metadata: dict[str, Any] = {"name": doc_name}
        if folder_id:
            file_metadata["parents"] = [folder_id]
        if convert_to_gdoc:
            file_metadata["mimeType"] = "application/vnd.google-apps.document"

        media = MediaFileUpload(
            str(docx_path),
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            resumable=True,
        )

        drive_file = (
            drive_service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink, mimeType",
            )
            .execute()
        )

        print(f"Successfully uploaded: {drive_file.get('name')}")
        print(f"  Document ID: {drive_file.get('id')}")
        print(f"  Link: {drive_file.get('webViewLink')}")

        if convert_to_gdoc and apply_font:
            apply_font_formatting(drive_file.get("id"), credentials)

        return drive_file

    except google.auth.exceptions.DefaultCredentialsError:
        print("\nError: Google Cloud credentials not found!")
        print("\nPlease run:")
        print("  gcloud auth application-default login")
        print("\nThen make sure Google Drive API is enabled:")
        print("  gcloud services enable drive.googleapis.com --project=YOUR_PROJECT_ID")
        raise
    except HttpError as error:
        print(f"An error occurred: {error}")
        if error.resp.status == 403:
            print("\nThis might be because:")
            print("1. Google Drive API is not enabled. Run:")
            print(
                "   gcloud services enable drive.googleapis.com --project=YOUR_PROJECT_ID"
            )
            print("2. Your credentials don't have the necessary permissions")
        raise


def read_document(
    doc_id: str, tab_id: str | None = None, include_tabs: bool = True
) -> dict:
    docs_service = _get_docs_service()
    return (
        docs_service.documents()
        .get(documentId=doc_id, includeTabsContent=include_tabs)
        .execute()
    )


def list_document_tabs(doc_id: str) -> list[dict]:
    doc = read_document(doc_id, include_tabs=True)
    tabs: list[dict] = []

    def extract_tabs(tab_list: list[dict], level: int = 0) -> None:
        for tab in tab_list:
            props = tab.get("tabProperties", {})
            tabs.append(
                {
                    "tabId": props.get("tabId"),
                    "title": props.get("title", "Untitled"),
                    "level": level,
                }
            )
            if "childTabs" in tab:
                extract_tabs(tab["childTabs"], level + 1)

    extract_tabs(doc.get("tabs", []))
    return tabs


def create_empty_document(title: str) -> dict:
    docs_service = _get_docs_service()
    doc = docs_service.documents().create(body={"title": title}).execute()
    doc_id = doc.get("documentId")
    print(f"Created empty document: {title}")
    print(f"  Document ID: {doc_id}")
    print(f"  Link: https://docs.google.com/document/d/{doc_id}/edit")
    return doc


def replace_text_in_doc(
    doc_id: str, find_text: str, replace_text: str, tab_id: str | None = None
) -> dict:
    docs_service = _get_docs_service()
    request: dict[str, Any] = {
        "replaceAllText": {
            "containsText": {"text": find_text, "matchCase": True},
            "replaceText": replace_text,
        }
    }
    if tab_id:
        request["replaceAllText"]["tabsCriteria"] = {"tabIds": [tab_id]}

    result = (
        docs_service.documents()
        .batchUpdate(documentId=doc_id, body={"requests": [request]})
        .execute()
    )
    occurrences = (
        result.get("replies", [{}])[0]
        .get("replaceAllText", {})
        .get("occurrencesChanged", 0)
    )
    print(
        f"Replaced {occurrences} occurrence(s) of '{find_text}' with '{replace_text}'"
    )
    return result


def insert_text_in_doc(
    doc_id: str, text: str, index: int | None = None, tab_id: str | None = None
) -> dict:
    docs_service = _get_docs_service()

    if index is not None:
        location: dict[str, Any] = {"index": index}
        if tab_id:
            location["tabId"] = tab_id
        request = {"insertText": {"location": location, "text": text}}
    else:
        seg_location: dict[str, Any] = {"segmentId": ""}
        if tab_id:
            seg_location["tabId"] = tab_id
        request = {"insertText": {"endOfSegmentLocation": seg_location, "text": text}}

    result = (
        docs_service.documents()
        .batchUpdate(documentId=doc_id, body={"requests": [request]})
        .execute()
    )
    position = f"index {index}" if index else "end of document"
    print(f"Inserted text at {position}")
    return result


def apply_batch_update(doc_id: str, requests_file: str) -> dict:
    docs_service = _get_docs_service()
    body = json.loads(Path(requests_file).read_text())
    result = (
        docs_service.documents().batchUpdate(documentId=doc_id, body=body).execute()
    )
    print(f"Applied {len(body.get('requests', []))} request(s) from {requests_file}")
    return result


def get_document_end_index(doc_id: str, tab_id: str | None = None) -> int:
    doc = read_document(doc_id, include_tabs=True)

    if tab_id:
        doc_tab = _find_tab_by_id(doc.get("tabs", []), tab_id)
        if not doc_tab:
            raise ValueError(f"Tab {tab_id} not found")
        content = doc_tab.get("body", {}).get("content", [])
    else:
        tabs = doc.get("tabs", [])
        if tabs:
            content = tabs[0].get("documentTab", {}).get("body", {}).get("content", [])
        else:
            content = doc.get("body", {}).get("content", [])

    return _find_end_index(content) - 1


def append_markdown_to_doc(
    doc_id: str, markdown_file: str, tab_id: str | None = None
) -> None:
    print(f"Appending {markdown_file} to document {doc_id}...")
    content = Path(markdown_file).read_text(encoding="utf-8")
    end_index = get_document_end_index(doc_id, tab_id)
    insert_text_in_doc(doc_id, "\n\n" + content, index=end_index, tab_id=tab_id)
    print(f"Appended content from {markdown_file}")
    print(f"  Link: https://docs.google.com/document/d/{doc_id}/edit")


# --- Diagnostics ---


def check_auth() -> bool:
    try:
        credentials = _get_credentials()
        drive_service = _get_drive_service(credentials)
        drive_service.about().get(fields="user").execute()
        return True
    except google.auth.exceptions.DefaultCredentialsError:
        return False
    except HttpError as e:
        if e.resp.status == 403:
            return False
        raise


def ensure_setup() -> bool:
    ok = True
    if not shutil.which("pandoc"):
        print("ERROR: pandoc is not installed.")
        print("  Fix: brew install pandoc")
        ok = False
    if not check_auth():
        print("ERROR: Google credentials missing or wrong scopes.")
        print("  Fix: gcloud auth application-default login \\")
        print(
            "    --scopes=https://www.googleapis.com/auth/drive.file,"
            "https://www.googleapis.com/auth/documents,"
            "https://www.googleapis.com/auth/cloud-platform"
        )
        ok = False
    return ok


def doctor() -> bool:
    print("Google Docs skill — prerequisite check\n")
    all_ok = True

    pandoc = shutil.which("pandoc")
    if pandoc:
        version = subprocess.run(
            ["pandoc", "--version"], capture_output=True, text=True
        ).stdout.split("\n")[0]
        print(f"  [OK]  pandoc: {version}")
    else:
        print("  [FAIL] pandoc not found")
        print("         Fix: brew install pandoc")
        all_ok = False

    if _HAS_GOOGLE:
        from importlib.metadata import version as pkg_version

        print(f"  [OK]  google-auth: {google.auth.__version__}")
        print(
            f"  [OK]  google-api-python-client: "
            f"{pkg_version('google-api-python-client')}"
        )
    else:
        print("  [FAIL] Missing Google Python packages")
        print(f"         Fix: uv venv {VENV_DIR}")
        print(
            f"         uv pip install --python {VENV_PYTHON}"
            f" {' '.join(REQUIRED_PACKAGES)}"
        )
        print(f"         Then run: {VENV_PYTHON} {__file__} doctor")
        all_ok = False

    if _HAS_GOOGLE and check_auth():
        print("  [OK]  Google credentials (drive.file + documents scopes)")
    elif _HAS_GOOGLE:
        print("  [FAIL] Google credentials missing or wrong scopes")
        print("         Fix: gcloud auth application-default login \\")
        print(
            "           --scopes=https://www.googleapis.com/auth/drive.file,"
            "https://www.googleapis.com/auth/documents,"
            "https://www.googleapis.com/auth/cloud-platform"
        )
        all_ok = False

    if VENV_PYTHON.exists():
        print(f"  [OK]  Skill venv: {VENV_DIR}")
    else:
        print(f"  [WARN] No skill venv at {VENV_DIR}")
        print(f"         Fix: uv venv {VENV_DIR}")
        print(
            f"         uv pip install --python {VENV_PYTHON}"
            f" {' '.join(REQUIRED_PACKAGES)}"
        )

    print()
    print("All checks passed." if all_ok else "Some checks failed — see fixes above.")
    return all_ok


# --- CLI ---


def _handle_setup() -> None:
    print(f"Setting up skill venv at {VENV_DIR} ...")
    if not shutil.which("uv"):
        print("ERROR: uv is not installed.")
        print("  Fix: brew install uv")
        sys.exit(1)
    subprocess.run(["uv", "venv", str(VENV_DIR)], check=True)
    subprocess.run(
        ["uv", "pip", "install", "--python", str(VENV_PYTHON), *REQUIRED_PACKAGES],
        check=True,
    )
    print(f"\nDone! Run commands with: {VENV_PYTHON} {__file__} <command>")


def _handle_create(args: argparse.Namespace) -> None:
    if not args.convert_only and not ensure_setup():
        sys.exit(1)

    print("Converting markdown file...")
    docx_file = convert_markdown_to_docx(args.markdown_file, args.output)

    if args.convert_only:
        print(f"\nConversion complete: {docx_file}")
        return

    file_info = upload_to_google_drive(
        docx_file,
        doc_name=args.name,
        convert_to_gdoc=not args.no_convert,
        folder_id=args.folder,
    )

    if not args.keep_docx and not args.output:
        docx_file.unlink()
        print(f"\nCleaned up: {docx_file.name}")

    print(f"\nDone! Open at: {file_info.get('webViewLink')}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Google Docs operations: create, read, edit, append",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  doctor                        Check all prerequisites
  setup                         Create skill venv and install deps (uses uv)
  create <file.md>              Create new doc from markdown
  create-empty <title>          Create empty document
  read <doc_id>                 Read document content (JSON)
  list-tabs <doc_id>            List all tabs in document
  append <doc_id> <file.md>     Append markdown to existing doc
  replace <doc_id> <find> <rep> Replace all occurrences of text
  insert <doc_id> <text>        Insert text at position
  update <doc_id> <json_file>   Apply batchUpdate from JSON

Examples:
  python gdocs.py doctor
  python gdocs.py setup
  python gdocs.py create my_doc.md --name "My Document"
  python gdocs.py append 1abc...xyz section.md --tab t.appendix
  python gdocs.py replace 1abc...xyz "{{DATE}}" "2025-01-15"
  python gdocs.py list-tabs 1abc...xyz
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    subparsers.add_parser("doctor", help="Check all prerequisites")
    subparsers.add_parser("setup", help="Create skill venv and install deps (uses uv)")

    create_parser = subparsers.add_parser("create", help="Create doc from markdown")
    create_parser.add_argument("markdown_file", help="Path to markdown file")
    create_parser.add_argument("--name", help="Document name")
    create_parser.add_argument("--folder", help="Google Drive folder ID")
    create_parser.add_argument(
        "--no-convert", action="store_true", help="Keep as .docx"
    )
    create_parser.add_argument(
        "--convert-only", action="store_true", help="Only convert, no upload"
    )
    create_parser.add_argument("--output", help="Output path for .docx")
    create_parser.add_argument(
        "--keep-docx", action="store_true", help="Keep .docx after upload"
    )

    create_empty_parser = subparsers.add_parser(
        "create-empty", help="Create empty document"
    )
    create_empty_parser.add_argument("title", help="Document title")

    read_parser = subparsers.add_parser("read", help="Read document content")
    read_parser.add_argument("doc_id", help="Document ID")
    read_parser.add_argument("--tab", help="Specific tab ID")
    read_parser.add_argument("--tabs", action="store_true", help="Include all tabs")

    list_tabs_parser = subparsers.add_parser("list-tabs", help="List document tabs")
    list_tabs_parser.add_argument("doc_id", help="Document ID")

    append_parser = subparsers.add_parser("append", help="Append markdown to doc")
    append_parser.add_argument("doc_id", help="Document ID")
    append_parser.add_argument("markdown_file", help="Path to markdown file")
    append_parser.add_argument("--tab", help="Target tab ID")

    replace_parser = subparsers.add_parser("replace", help="Replace text in doc")
    replace_parser.add_argument("doc_id", help="Document ID")
    replace_parser.add_argument("find", help="Text to find")
    replace_parser.add_argument("replace_text", help="Replacement text")
    replace_parser.add_argument("--tab", help="Target tab ID")

    insert_parser = subparsers.add_parser("insert", help="Insert text in doc")
    insert_parser.add_argument("doc_id", help="Document ID")
    insert_parser.add_argument("text", help="Text to insert")
    insert_parser.add_argument("--index", type=int, help="Position index")
    insert_parser.add_argument("--tab", help="Target tab ID")

    update_parser = subparsers.add_parser("update", help="Apply batchUpdate from JSON")
    update_parser.add_argument("doc_id", help="Document ID")
    update_parser.add_argument("json_file", help="Path to JSON file with requests")

    args = parser.parse_args()

    try:
        match args.command:
            case "doctor":
                sys.exit(0 if doctor() else 1)
            case "setup":
                _handle_setup()
            case "create":
                _handle_create(args)
            case "create-empty":
                create_empty_document(args.title)
            case "read":
                doc = read_document(
                    args.doc_id, tab_id=args.tab, include_tabs=args.tabs
                )
                print(json.dumps(doc, indent=2))
            case "list-tabs":
                tabs = list_document_tabs(args.doc_id)
                print(f"{'Tab ID':<20} {'Title':<20} {'Level'}")
                print("-" * 50)
                for tab in tabs:
                    indent = "  " * tab["level"]
                    print(
                        f"{tab['tabId']:<20} {indent}{tab['title']:<20} {tab['level']}"
                    )
            case "append":
                append_markdown_to_doc(args.doc_id, args.markdown_file, tab_id=args.tab)
            case "replace":
                replace_text_in_doc(
                    args.doc_id, args.find, args.replace_text, tab_id=args.tab
                )
            case "insert":
                insert_text_in_doc(
                    args.doc_id, args.text, index=args.index, tab_id=args.tab
                )
            case "update":
                apply_batch_update(args.doc_id, args.json_file)
            case _:
                parser.print_help()
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
