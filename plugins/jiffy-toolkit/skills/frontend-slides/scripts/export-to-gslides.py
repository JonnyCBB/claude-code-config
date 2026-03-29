#!/usr/bin/env python3
"""Export frontend-slides HTML presentations to Google Slides and/or PDF."""

import argparse
import glob
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Google API imports (only needed for gslides format)
# Imported lazily to allow --format pdf without google libs installed


def find_free_port() -> int:
    """Find an available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def start_server(presentation_dir: str, port: int) -> subprocess.Popen:
    """Start serve.py on the given port. Returns the Popen process."""
    # We can't modify serve.py's hardcoded port, so use Python's http.server directly
    proc = subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(port)],
        cwd=presentation_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait for server to be ready
    for _ in range(20):
        try:
            with socket.create_connection(('localhost', port), timeout=0.5):
                break
        except (ConnectionRefusedError, OSError):
            time.sleep(0.25)
    return proc


def run_decktape(url: str, output_dir: str, pause: int = 2000) -> tuple[str, list[str]]:
    """
    Run Decktape to capture screenshots and PDF.

    Returns:
        tuple of (pdf_path, sorted list of screenshot PNG paths)
    """
    pdf_path = os.path.join(output_dir, 'presentation.pdf')
    screenshots_dir = os.path.join(output_dir, 'screenshots')
    os.makedirs(screenshots_dir, exist_ok=True)

    # Decktape constructs screenshot paths as <screenshots-dir>/<pdf-basename>_N_WxH.png
    # relative to CWD. Run from output_dir with relative paths so files land correctly.
    cmd = [
        'decktape', 'generic',
        '--size', '1920x1080',
        '--screenshots',
        '--screenshots-directory', screenshots_dir,
        '--screenshots-format', 'png',
        '--pause', str(pause),
        url,
        'presentation.pdf',
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
    if result.returncode != 0:
        print(f"Decktape stdout:\n{result.stdout}", file=sys.stderr)
        print(f"Decktape stderr:\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(f"Decktape failed with exit code {result.returncode}")

    # Collect screenshot PNGs, sorted numerically
    pngs = sorted(
        glob.glob(os.path.join(screenshots_dir, '*.png')),
        key=lambda p: int(re.search(r'(\d+)', os.path.basename(p)).group(1))
    )

    if not pngs:
        raise RuntimeError("Decktape produced no screenshots")

    return pdf_path, pngs


def extract_slide_text(presentation_dir: str) -> list[dict]:
    """
    Extract text content and links from slides/*.html for speaker notes.

    Returns a list of dicts per slide HTML file (in order), each with:
        - 'text': plain text string
        - 'links': list of {'start': int, 'end': int, 'url': str} for hyperlinks
    Fragment steps within a slide share the same data.
    """
    from bs4 import BeautifulSoup

    slides_dir = os.path.join(presentation_dir, 'slides')
    if not os.path.isdir(slides_dir):
        return []

    slide_files = sorted(glob.glob(os.path.join(slides_dir, '*.html')))
    results = []

    for slide_file in slide_files:
        with open(slide_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        # Remove <style> and <script> tags
        for tag in soup.find_all(['style', 'script']):
            tag.decompose()

        # Extract text with link positions
        lines_seen = set()
        text_parts = []  # plain text accumulator
        links = []  # {start, end, url}
        offset = 0

        for el in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'span', 'td', 'th']):
            line_text = el.get_text(strip=True)
            if not line_text or line_text in lines_seen:
                continue
            lines_seen.add(line_text)

            if text_parts:
                text_parts.append('\n')
                offset += 1

            # Walk children to find <a> tags and their positions
            line_offset = offset
            _extract_element_text(el, text_parts, links, line_offset)
            offset = sum(len(p) for p in text_parts)

        results.append({
            'text': ''.join(text_parts),
            'links': links,
        })

    return results


def _extract_element_text(
    element, text_parts: list, links: list, base_offset: int
) -> int:
    """Recursively extract text from an element, tracking <a> link positions.

    Returns the current offset after processing.
    """
    from bs4 import NavigableString

    offset = base_offset
    for child in element.children:
        if isinstance(child, NavigableString):
            text = str(child)
            if not text:
                continue
            # Collapse internal whitespace runs, but preserve a leading/trailing
            # space if present (avoids "wordword" joins across element boundaries)
            inner = ' '.join(text.split())
            if not inner:
                # Pure whitespace node — emit a single space if we have content
                if text_parts:
                    text_parts.append(' ')
                    offset += 1
                continue
            result = ''
            if text[0].isspace():
                result = ' '
            result += inner
            if text[-1].isspace() and len(text) > 1:
                result += ' '
            text_parts.append(result)
            offset += len(result)
        elif child.name == 'a' and child.get('href'):
            link_text = child.get_text()
            collapsed = ' '.join(link_text.split())
            if collapsed:
                start = offset
                text_parts.append(collapsed)
                offset += len(collapsed)
                links.append({
                    'start': start,
                    'end': offset,
                    'url': child['href'],
                })
        elif child.name in ('style', 'script'):
            continue
        else:
            # Recurse into nested elements (but not <a> — handled above)
            offset = _extract_element_text(child, text_parts, links, offset)
    return offset


def map_screenshots_to_notes(
    screenshot_paths: list[str], slide_data: list[dict]
) -> list[dict]:
    """
    Map screenshot captures to speaker notes data (text + links).

    Decktape produces multiple screenshots per slide (one per fragment step).
    We map all fragment-step screenshots from the same slide to the same notes.

    Since we can't know exactly which screenshots map to which slide without
    parsing Decktape output, we distribute proportionally.
    """
    empty = {'text': '', 'links': []}

    if not slide_data:
        return [empty] * len(screenshot_paths)

    num_screenshots = len(screenshot_paths)
    num_slides = len(slide_data)

    if num_screenshots <= num_slides:
        return slide_data[:num_screenshots]

    # More screenshots than slides — distribute evenly
    notes = []
    for i, data in enumerate(slide_data):
        start = round(i * num_screenshots / num_slides)
        end = round((i + 1) * num_screenshots / num_slides)
        count = max(1, end - start)
        notes.extend([data] * count)

    return (notes + [empty] * num_screenshots)[:num_screenshots]


def create_google_slides(
    title: str,
    screenshot_paths: list[str],
    notes: list[dict],
    domain: str,
) -> str:
    """
    Create a Google Slides presentation with full-bleed screenshot backgrounds.

    Returns the presentation URL.
    """
    import google.auth
    from googleapiclient.discovery import build

    # Authenticate — use ADC without restricting scopes.
    # Scopes were set during `gcloud auth application-default login`.
    credentials, _ = google.auth.default()

    slides_service = build('slides', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    # Step 1: Create empty presentation
    presentation = slides_service.presentations().create(
        body={'title': title}
    ).execute()
    presentation_id = presentation['presentationId']

    # The new presentation has one blank slide — we'll delete it after adding ours
    default_slide_id = presentation['slides'][0]['objectId']

    # Step 2: Upload images to Drive and build slide requests
    BATCH_SIZE = 50

    # Step 3: Create slides and set backgrounds
    slide_requests = []
    for i, (png_path, note_text) in enumerate(zip(screenshot_paths, notes)):
        slide_id = f'slide_{i:04d}'
        image_url = _upload_image(drive_service, png_path, f'slide_{i:04d}.png', domain)

        slide_requests.append({
            'createSlide': {
                'objectId': slide_id,
                'insertionIndex': i,
                'slideLayoutReference': {'predefinedLayout': 'BLANK'},
            }
        })
        slide_requests.append({
            'updatePageProperties': {
                'objectId': slide_id,
                'pageProperties': {
                    'pageBackgroundFill': {
                        'stretchedPictureFill': {
                            'contentUrl': image_url,
                        }
                    }
                },
                'fields': 'pageBackgroundFill',
            }
        })

    # Delete default blank slide
    slide_requests.append({'deleteObject': {'objectId': default_slide_id}})

    # Send in batches
    for batch_start in range(0, len(slide_requests), BATCH_SIZE):
        batch = slide_requests[batch_start:batch_start + BATCH_SIZE]
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': batch},
        ).execute()

    # Step 4: Read back presentation to get speaker notes object IDs
    presentation = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()

    notes_requests = []
    for slide, note_data in zip(presentation['slides'], notes):
        note_text = note_data['text']
        note_links = note_data['links']
        if not note_text.strip():
            continue
        notes_id = (
            slide.get('slideProperties', {})
            .get('notesPage', {})
            .get('notesProperties', {})
            .get('speakerNotesObjectId')
        )
        if not notes_id:
            continue

        # Insert the plain text first
        notes_requests.append({
            'insertText': {
                'objectId': notes_id,
                'text': note_text,
                'insertionIndex': 0,
            }
        })

        # Apply hyperlinks to link spans
        for link in note_links:
            notes_requests.append({
                'updateTextStyle': {
                    'objectId': notes_id,
                    'textRange': {
                        'type': 'FIXED_RANGE',
                        'startIndex': link['start'],
                        'endIndex': link['end'],
                    },
                    'style': {
                        'link': {'url': link['url']},
                    },
                    'fields': 'link',
                }
            })

    if notes_requests:
        for batch_start in range(0, len(notes_requests), BATCH_SIZE):
            batch = notes_requests[batch_start:batch_start + BATCH_SIZE]
            slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': batch},
            ).execute()

    # Step 5: Set domain-restricted sharing
    drive_service.permissions().create(
        fileId=presentation_id,
        body={
            'type': 'domain',
            'role': 'reader',
            'domain': domain,
        },
    ).execute()

    return f'https://docs.google.com/presentation/d/{presentation_id}/edit'


def _upload_image(drive_service, image_path: str, filename: str, domain: str) -> str:
    """Upload a PNG to Google Drive. Returns viewable URL.

    Images need 'anyone' read permission so the Slides API server can fetch
    them when setting slide backgrounds. The presentation itself is
    domain-restricted separately.
    """
    from googleapiclient.http import MediaFileUpload

    file_metadata = {'name': filename}
    media = MediaFileUpload(image_path, mimetype='image/png')

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
    ).execute()

    file_id = file['id']

    # Images must be accessible to the Slides API server, so use 'anyone' reader.
    # The presentation itself is domain-restricted.
    drive_service.permissions().create(
        fileId=file_id,
        body={
            'type': 'anyone',
            'role': 'reader',
        },
    ).execute()

    return f'https://drive.google.com/uc?export=view&id={file_id}'


def main():
    parser = argparse.ArgumentParser(
        description='Export frontend-slides HTML presentations to Google Slides and/or PDF.'
    )
    parser.add_argument('presentation_dir', help='Path to the presentation directory')
    parser.add_argument('--title', help='Presentation title (defaults to directory name)')
    parser.add_argument('--domain', default='', help='Domain for sharing restriction (e.g. example.com)')
    parser.add_argument('--format', choices=['gslides', 'pdf'], default='gslides',
                        dest='output_format', help='Output format (default: gslides)')
    parser.add_argument('--pause', type=int, default=2000,
                        help='Decktape pause between captures in ms (default: 2000)')

    args = parser.parse_args()

    presentation_dir = os.path.expanduser(args.presentation_dir)
    if not os.path.isdir(presentation_dir):
        print(f"Error: {presentation_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    title = args.title or Path(presentation_dir).name.replace('-', ' ').title()

    # Create temp directory for Decktape output
    with tempfile.TemporaryDirectory(prefix='slides-export-') as tmp_dir:
        # Start local server
        port = find_free_port()
        server_proc = start_server(presentation_dir, port)

        try:
            url = f'http://localhost:{port}'
            print(f"Server started on {url}")

            # Run Decktape
            print("Capturing slides with Decktape...")
            pdf_path, screenshot_paths = run_decktape(url, tmp_dir, args.pause)
            print(f"Captured {len(screenshot_paths)} screenshots + PDF")

            # Copy PDF to presentation directory
            import shutil
            final_pdf = os.path.join(presentation_dir, f'{Path(presentation_dir).name}.pdf')
            shutil.copy2(pdf_path, final_pdf)
            print(f"PDF saved: {final_pdf}")

            if args.output_format == 'gslides':
                # Extract text for speaker notes
                print("Extracting slide text for speaker notes...")
                slide_texts = extract_slide_text(presentation_dir)
                notes = map_screenshots_to_notes(screenshot_paths, slide_texts)

                # Create Google Slides
                print("Creating Google Slides presentation...")
                slides_url = create_google_slides(title, screenshot_paths, notes, args.domain)
                print(f"\nGoogle Slides: {slides_url}")
                print(f"PDF: {final_pdf}")
            else:
                print(f"\nPDF: {final_pdf}")

        finally:
            # Kill server
            server_proc.terminate()
            server_proc.wait(timeout=5)

    return 0


if __name__ == '__main__':
    sys.exit(main())
