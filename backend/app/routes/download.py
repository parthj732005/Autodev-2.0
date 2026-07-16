import io
import zipfile
from fastapi import APIRouter, Response
from app.db.session import SessionLocal
from app.db.models import GeneratedFile

router = APIRouter(prefix="/download")


@router.get("/{project_name}")
def download_project(project_name: str):
    db = SessionLocal()
    files = db.query(GeneratedFile)\
        .filter(GeneratedFile.project_name == project_name)\
        .all()

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for f in files:
            zipf.writestr(f.file_path, f.content)

    db.close()

    return Response(
        zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={project_name}.zip"
        }
    )
