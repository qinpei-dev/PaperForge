# Backup and restore boundaries

Persistent production data consists of PostgreSQL plus Docker volumes `paperforge-uploads`, `paperforge-outputs`, `paperforge-template-storage`, `paperforge-task-states`, and `paperforge-templates`.

Use `scripts/backup_postgres.ps1 -EnvFile /secure/paperforge.env` before migration, then run `scripts/verify_postgres_backup.ps1 -BackupFile <dump>` to validate the custom-format archive. Keep backups outside the repository and test restore in an isolated environment. File-volume backup should be taken alongside the database backup with `scripts/backup_files.ps1 -BackupDirectory <dir>`; quiesce uploads/tasks or document the backup window to avoid inconsistent file/database references. Restore database first, then corresponding file volumes with `scripts/restore_files.ps1 ... -ConfirmDestructiveRestore`, and only then start the compatible application image.

The recovery rehearsal is: capture the PostgreSQL dump and five file-volume archives, verify the dump archive, restore into an isolated PostgreSQL/volume set, run Alembic to the image's expected revision, and execute `scripts/production_smoke_test.py` against the isolated endpoint. A production restore must not be performed against the live volume without an explicit maintenance window and a second operator checking the target names.

`task_states` preserves JSON state files, but the in-process task worker and SSE event history are not restart-resumable. A container restart can interrupt a running task; persistent files do not provide distributed queue or resume semantics.
