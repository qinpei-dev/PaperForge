# Backup and restore boundaries

Persistent production data consists of PostgreSQL plus Docker volumes `paperforge-uploads`, `paperforge-outputs`, `paperforge-template-storage`, `paperforge-task-states`, and `paperforge-templates`.

Use `scripts/backup_postgres.ps1 -EnvFile /secure/paperforge.env` before migration. Keep backups outside the repository and test restore in an isolated environment. File-volume backup should be taken alongside the database backup; quiesce uploads/tasks or document the backup window to avoid inconsistent file/database references. Restore database first, then corresponding file volumes, and only then start the compatible application image.

`task_states` preserves JSON state files, but the in-process task worker and SSE event history are not restart-resumable. A container restart can interrupt a running task; persistent files do not provide distributed queue or resume semantics.
