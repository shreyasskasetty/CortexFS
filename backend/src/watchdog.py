import os
import json
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from langchain_core.documents import Document
import pika
import asyncio

class WatchdogHandler(FileSystemEventHandler):
    def __init__(self, producer):
        self.producer = producer

    def on_created(self, event):
        self.producer.on_created(event)

class FileEventProducer:
    def __init__(self, rabbitmq_url, queue_name, organizer, summarizer):
        self.organizer = organizer
        self.summarizer = summarizer
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        self.observer = None
        self.directory_to_watch = None
        self.target_directory = None

    def send_event(self, suggestion):
        """Send suggestions to the notification queue"""
        print(f"Sending the following suggestions to the queue: {suggestion}")
        message = suggestion
        try:
            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),  # Make message persistent
            )
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
        print(f"notification sent!")

    async def get_suggestions(self, rel_file_path):
        """Find the destination path for the file."""
        full_file_path = os.path.join(self.directory_to_watch, rel_file_path)
        category = self.summarizer.get_file_category(full_file_path)
        if category:
            content = self.summarizer.process_file(full_file_path, category)
            document = Document(
                page_content=content,
                metadata={"file_name": rel_file_path, "source": self.directory_to_watch, "category": category},
            )
            print("summarizing document")
            summary = await self.summarizer.summarize_document(document)
            print("getting path suggestions")
            response = self.organizer.get_path_suggestions(self.target_directory, summary)
            response["summary"] = summary.get("summary")
            return response
        return None
    
    def on_created(self, event):
        """Callback for file creation."""
        if not event.is_directory:
            file_path = os.path.relpath(event.src_path, self.directory_to_watch)
            print(f"File created: {file_path}")
            asyncio.run(self.process_file_async(file_path))

    async def process_file_async(self, file_path):
        """Process the file asynchronously and send suggestions."""
        suggestion = await self.get_suggestions(file_path)
        if suggestion:
            self.send_event(suggestion)
        else:
            print(f"No suggestions found for file: {file_path}")

    def start_monitoring(self, directory_to_watch, target_directory):
        """Start monitoring the directory."""
        if not os.path.exists(directory_to_watch):
            raise FileNotFoundError(f"Directory not found: {directory_to_watch}")

        self.directory_to_watch = directory_to_watch
        self.target_directory = target_directory
        handler = WatchdogHandler(self)
        self.observer = Observer()
        self.observer.schedule(handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        print(f"Started monitoring directory: {self.directory_to_watch}")

    def stop_monitoring(self):
        """Stop monitoring the directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            print("Stopped monitoring directory.")



