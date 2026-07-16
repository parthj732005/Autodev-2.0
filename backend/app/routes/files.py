from fastapi import APIRouter
from app.db.session import SessionLocal
from app.db.models import GeneratedFile

router = APIRouter(prefix="/files")


@router.get("/{project_name}")
def list_files(project_name: str):
    db = SessionLocal()
    files = (
        db.query(GeneratedFile)
        .filter(GeneratedFile.project_name == project_name)
        .all()
    )

    tree = {}

    for f in files:
        tree.setdefault(f.file_path, {
            "id": f.id,
            "language": f.language
        })

    db.close()
    return tree


@router.get("/content/{file_id}")
def read_file(file_id: int):
    db = SessionLocal()
    file = db.query(GeneratedFile).get(file_id)
    db.close()

    return {
        "path": file.file_path,
        "content": file.content
    }
