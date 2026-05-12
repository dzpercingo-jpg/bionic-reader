"""Legacy `.doc` (Word 97–2003 binary) in-place bionic transformation.

The binary `.doc` format predates Office Open XML and is not editable in-place
the way DOCX is — there's no run-level XML to surgically patch. The robust
approach is therefore a two-step conversion:

1. Convert `.doc` → `.docx` using LibreOffice in headless mode. LibreOffice
   has the best fidelity to legacy binary formats of any open-source tool;
   embedded images, tables, headers/footers, styles, and most formatting are
   preserved through the conversion.
2. Apply `docx_inplace.export_inplace` on the resulting `.docx` bytes. From
   that point on, the in-place fidelity guarantees of DOCX apply (images and
   tables byte-identical, run properties cloned, etc.).

The output is a `.bionic.docx` file (not `.doc`) — modern Word, LibreOffice,
Pages, and Google Docs all open it without complaint, and trying to round-trip
back to the legacy `.doc` format would lose information that the docx layer
preserves.

LibreOffice must be installed on the host (`apt install libreoffice-core
libreoffice-writer`). If `soffice` is not on `PATH`, this exporter raises a
`RuntimeError` with an actionable message — the API handler converts that to
HTTP 500 with the exception text so the user understands the host is missing
the dependency.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..models import BionicSettings
from .docx_inplace import export_inplace as docx_export_inplace


def _soffice_bin() -> str:
    for name in ("libreoffice", "soffice"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError(
        "LibreOffice is required to process legacy .doc files but `libreoffice`/`soffice` "
        "was not found on PATH. Install it via `apt install libreoffice-core libreoffice-writer` "
        "(or the equivalent for your platform)."
    )


def convert_doc_to_docx(data: bytes, timeout: float = 60.0) -> bytes:
    """Convert legacy .doc bytes to .docx bytes via LibreOffice headless.

    Uses a fresh per-call user profile so concurrent calls don't fight over
    the same LibreOffice config dir. Both input and output stay in a temp
    directory that is removed when the function returns.
    """
    bin_path = _soffice_bin()
    with tempfile.TemporaryDirectory(prefix="bionic-doc-") as td_str:
        td = Path(td_str)
        src = td / "input.doc"
        src.write_bytes(data)
        profile = td / "lo-profile"
        profile.mkdir()
        cmd = [
            bin_path,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--norestore",
            f"-env:UserInstallation=file://{profile}",
            "--convert-to",
            "docx",
            "--outdir",
            str(td),
            str(src),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"LibreOffice timed out after {timeout}s converting the .doc file."
            ) from exc
        if result.returncode != 0:
            stderr = (result.stderr or b"").decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"LibreOffice failed to convert .doc → .docx (exit {result.returncode}). {stderr}"
            )
        out = td / "input.docx"
        if not out.exists():
            raise RuntimeError(
                "LibreOffice converter ran but produced no .docx output. "
                "The source .doc file may be corrupt or password-protected."
            )
        return out.read_bytes()


def export_inplace(
    data: bytes,
    settings: BionicSettings,
    filename: str = "document.doc",
) -> tuple[bytes, str, str]:
    """Convert legacy .doc → .docx with LibreOffice, then bionic-style in-place."""
    docx_bytes = convert_doc_to_docx(data)
    stem = Path(filename).stem or "document"
    # Reuse the DOCX in-place pipeline (same fidelity guarantees from here on).
    body, media_type, _ = docx_export_inplace(docx_bytes, settings, filename=f"{stem}.docx")
    return body, media_type, f"{stem}.bionic.docx"
