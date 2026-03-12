"""
Google Drive backup integration.

Handles OAuth2 authentication and file operations for syncing
inventory backups to/from Google Drive.
"""

import os
from pathlib import Path

from database.connection import get_db_path

# Google API imports — optional; features degrade gracefully if missing
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

    _HAS_GOOGLE = True
except ImportError:
    _HAS_GOOGLE = False

# Only need file-level access to the app's own folder
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DRIVE_FOLDER_NAME = "InventoryManager_Backups"
MAX_DRIVE_BACKUPS = 5


def _token_path() -> str:
    """Path to the stored OAuth token."""
    return str(Path(get_db_path()).parent / "google_token.json")


def _credentials_path() -> str:
    """Path to the bundled OAuth client credentials."""
    # Look next to the main script first, then in the app data dir
    candidates = [
        Path(__file__).resolve().parent.parent / "credentials.json",
        Path(get_db_path()).parent / "credentials.json",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return str(candidates[0])  # default even if missing — connect() will error


def _load_creds() -> "Credentials | None":
    """Load and refresh stored credentials, or return None."""
    if not _HAS_GOOGLE:
        return None
    token = _token_path()
    if not os.path.exists(token):
        return None
    creds = Credentials.from_authorized_user_file(token, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(token, "w") as f:
                f.write(creds.to_json())
        except Exception:
            # Token is truly invalid — delete it
            os.remove(token)
            return None
    if creds and creds.valid:
        return creds
    return None


def _get_service():
    """Return an authenticated Drive API service object."""
    creds = _load_creds()
    if creds is None:
        raise RuntimeError("Not connected to Google Drive.")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


# ── Public API ────────────────────────────────────────────────────────────


def is_available() -> bool:
    """Return True if the google packages are installed."""
    return _HAS_GOOGLE


def is_connected() -> bool:
    """Return True if we have a valid, non-expired token."""
    return _load_creds() is not None


def connect() -> bool:
    """
    Run the OAuth2 desktop flow (opens browser).
    Returns True on success.
    """
    if not _HAS_GOOGLE:
        raise RuntimeError(
            "Google API packages not installed.\n"
            "Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )
    creds_file = _credentials_path()
    if not os.path.exists(creds_file):
        raise FileNotFoundError(
            f"credentials.json not found.\n"
            f"Expected at: {creds_file}\n"
            "Download it from Google Cloud Console."
        )
    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(_token_path(), "w") as f:
        f.write(creds.to_json())
    return True


def disconnect():
    """Remove stored token."""
    token = _token_path()
    if os.path.exists(token):
        os.remove(token)


def get_user_email() -> str:
    """Return the email of the connected Google account."""
    service = _get_service()
    about = service.about().get(fields="user").execute()
    return about.get("user", {}).get("emailAddress", "Unknown")


def _get_or_create_folder(service) -> str:
    """Find or create the InventoryManager_Backups folder. Returns folder ID."""
    query = (
        f"name = '{DRIVE_FOLDER_NAME}' "
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    resp = service.files().list(q=query, spaces="drive", fields="files(id)").execute()
    files = resp.get("files", [])
    if files:
        return files[0]["id"]

    # Create the folder
    meta = {
        "name": DRIVE_FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def upload_backup(local_zip_path: str) -> dict:
    """
    Upload a backup zip to the Drive folder.
    Prunes to keep only the latest MAX_DRIVE_BACKUPS files.
    Returns metadata dict of the uploaded file.
    """
    service = _get_service()
    folder_id = _get_or_create_folder(service)
    file_name = os.path.basename(local_zip_path)

    media = MediaFileUpload(local_zip_path, mimetype="application/zip", resumable=True)
    meta = {"name": file_name, "parents": [folder_id]}
    uploaded = service.files().create(body=meta, media_body=media, fields="id,name,size,createdTime").execute()

    # Prune old backups on Drive
    _prune_drive_backups(service, folder_id)

    return uploaded


def _prune_drive_backups(service, folder_id: str):
    """Keep only the newest MAX_DRIVE_BACKUPS files in the Drive folder."""
    query = f"'{folder_id}' in parents and trashed = false"
    resp = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id,name,createdTime)", orderBy="createdTime desc")
        .execute()
    )
    files = resp.get("files", [])
    for old_file in files[MAX_DRIVE_BACKUPS:]:
        service.files().delete(fileId=old_file["id"]).execute()


def list_drive_backups() -> list[dict]:
    """
    List backups on Drive, sorted newest-first.
    Returns list of dicts with: name, id, date, size_mb.
    """
    service = _get_service()
    folder_id = _get_or_create_folder(service)

    query = f"'{folder_id}' in parents and trashed = false"
    resp = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id,name,size,createdTime)", orderBy="createdTime desc")
        .execute()
    )
    result = []
    for f in resp.get("files", []):
        size_bytes = int(f.get("size", 0))
        result.append({
            "name": f["name"],
            "id": f["id"],
            "date": f.get("createdTime", "")[:19].replace("T", " "),
            "size_mb": round(size_bytes / (1024 * 1024), 2),
        })
    return result


def download_backup(file_id: str, dest_path: str) -> str:
    """Download a backup zip from Drive to dest_path. Returns absolute path."""
    import io

    service = _get_service()
    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return os.path.abspath(dest_path)
