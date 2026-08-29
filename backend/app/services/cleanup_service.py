"""
Cleanup service for automatic deletion of old uploaded PDF files.
Runs as a background thread to periodically clean up files older than the configured threshold.
"""
import threading
import time
from datetime import datetime

from app.core.config import UPLOAD_DIR, AUTO_DELETE_AFTER_SECONDS, AUTO_DELETE_CHECK_INTERVAL
from app.core.logger import logger


class CleanupService:
    """Background service that periodically cleans up old uploaded files."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self):
        """Start the cleanup background thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("CLEANUP | service already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="CleanupService")
        self._thread.start()
        logger.info(
            "CLEANUP | service started | delete_after=%ds | check_interval=%ds",
            AUTO_DELETE_AFTER_SECONDS,
            AUTO_DELETE_CHECK_INTERVAL
        )

    def stop(self):
        """Stop the cleanup background thread."""
        if self._thread is None:
            return

        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None
        logger.info("CLEANUP | service stopped")

    def _run(self):
        """Main cleanup loop."""
        # Run initial cleanup after a short delay to let the server start
        time.sleep(10)
        self._cleanup()

        while not self._stop_event.is_set():
            # Wait for the check interval or stop signal
            self._stop_event.wait(AUTO_DELETE_CHECK_INTERVAL)
            if self._stop_event.is_set():
                break

            self._cleanup()

    def _cleanup(self):
        """Perform the actual cleanup of old files."""
        if not UPLOAD_DIR.exists():
            logger.debug("CLEANUP | upload directory does not exist, skipping | path=%s", UPLOAD_DIR)
            return

        cutoff_time = time.time() - AUTO_DELETE_AFTER_SECONDS
        cutoff_datetime = datetime.fromtimestamp(cutoff_time)
        deleted_count = 0
        error_count = 0

        try:
            for filepath in UPLOAD_DIR.iterdir():
                if not filepath.is_file():
                    continue

                # Skip non-PDF files for safety
                if not filepath.name.lower().endswith('.pdf'):
                    continue

                try:
                    file_mtime = filepath.stat().st_mtime

                    if file_mtime < cutoff_time:
                        filepath.unlink()
                        deleted_count += 1
                        logger.info(
                            "CLEANUP | deleted old file | path=%s | age_hours=%.1f",
                            filepath,
                            (time.time() - file_mtime) / 3600
                        )
                except OSError as e:
                    error_count += 1
                    logger.warning("CLEANUP | failed to process file | path=%s | error=%s", filepath, e)

            if deleted_count > 0 or error_count > 0:
                logger.info(
                    "CLEANUP | run complete | deleted=%d | errors=%d | cutoff=%s",
                    deleted_count,
                    error_count,
                    cutoff_datetime.isoformat()
                )
            else:
                logger.debug("CLEANUP | no files to delete | cutoff=%s", cutoff_datetime.isoformat())

        except Exception as e:
            logger.exception("CLEANUP | cleanup run failed | error=%s", e)

    def run_now(self):
        """Manually trigger an immediate cleanup (for testing/admin purposes)."""
        with self._lock:
            self._cleanup()


# Singleton instance
cleanup_service = CleanupService()
