import logging
import os
import time

from django.core.management.base import BaseCommand
from django.utils import autoreload

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from stardate.models import Blog

logger = logging.getLogger(__name__)


class LocalFileEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # logger.info(event)
        path = event.src_path
        blog = Blog.objects.get(backend_file=path)

        blog.backend.pull()


class Command(BaseCommand):
    def watch(self):
        event_handler = LocalFileEventHandler()
        observer = Observer()

        for blog in Blog.objects.filter(
            backend_class='stardate.backends.local_file.LocalFileBackend'
        ):
            path = os.path.dirname(blog.backend_file)
            observer.schedule(event_handler, path, recursive=True)

        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()

        observer.join()

    def handle(self, *args, **options):
        self.run(**options)

    def run(self, **options):
        """
        Runs the server, using the autoreloader if needed
        """
        autoreload.main(self.inner_run, None, options)

    def inner_run(self, *args, **options):
        autoreload.raise_last_exception()

        self.stdout.write('watching files')

        try:
            self.watch()
        except KeyboardInterrupt:
            if shutdown_message:
                self.stdout.write(shutdown_message)
            sys.exit(0)
