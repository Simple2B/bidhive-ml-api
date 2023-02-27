from invoke import task


# Invoke doesn't suppport underscores in tasks, so clean_db - invalid.
# That's why here i use camelCase
@task
def cleanDb(_):
    from app.database import get_db
    from app.model import UploadedFile

    db_iter = get_db()
    db = next(db_iter)

    db.query(UploadedFile).delete()
    db.commit()
