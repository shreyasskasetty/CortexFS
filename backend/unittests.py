import unittest
from unittest.mock import MagicMock, patch, call, AsyncMock
import os
import asyncio
from src.watchdog import FileEventProducer, WatchdogHandler
from src.organizer import DirectoryOrganizer
from src.summarizer import FileSummarizer
from fastapi.testclient import TestClient
from server import create_app
import json
import aio_pika

class TestFileEventProducer(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.logger = MagicMock()
        self.organizer = MagicMock()
        self.summarizer = MagicMock()
        self.rabbitmq_url = "amqp://localhost"
        self.queue_name = "test-queue"
        self.producer = FileEventProducer(
            rabbitmq_url=self.rabbitmq_url,
            queue_name=self.queue_name,
            organizer=self.organizer,
            summarizer=self.summarizer,
            logger=self.logger,
        )

    @patch("os.path.exists")
    def test_start_monitoring_valid_directory(self, mock_exists):
        mock_exists.return_value = True
        self.producer.start_monitoring("/Users/shreyasskasetty/Documents/cortexFSTest/Downloads", "/Users/shreyasskasetty/Documents/cortexFSTest/Documents") # watch_directory, target_directory
        self.assertEqual(self.producer.directory_to_watch, "/Users/shreyasskasetty/Documents/cortexFSTest/Downloads")
        self.assertEqual(self.producer.target_directory, "/Users/shreyasskasetty/Documents/cortexFSTest/Documents")
        self.logger.info.assert_called_with(f"Started monitoring directory: {self.producer.directory_to_watch}")
        self.producer.stop_monitoring()

    @patch("os.path.exists")
    def test_start_monitoring_invalid_directory(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.producer.start_monitoring("/invalid/path", "/path/to/target")

    @patch("os.path.exists")
    def test_stop_monitoring(self, mock_exists):
        # Mock the directory existence check
        mock_exists.return_value = True

        # Start monitoring to initialize the observer
        self.producer.start_monitoring(
            "/Users/shreyasskasetty/Documents/cortexFSTest/Downloads",
            "/Users/shreyasskasetty/Documents/cortexFSTest/Documents"
        )

        # Stop monitoring and verify the observer's methods were called
        self.producer.stop_monitoring()

        self.logger.info.assert_called_with("Stopped monitoring directory.")

    @patch("os.path.getsize")
    @patch("time.localtime")
    @patch("time.strftime")
    @patch("os.path.getctime")
    def test_get_suggestions(self, mock_getctime, mock_strftime, mock_localtime, mock_getsize):
        mock_getsize.return_value = 1024
        mock_getctime.return_value = 123456789
        mock_strftime.return_value = "2024-12-01 12:00:00"

        self.summarizer.get_file_category.return_value = "text"
        self.summarizer.process_file.return_value = "Content of the file"
        self.summarizer.summarize_document = AsyncMock(return_value={"summary": "Test summary"})
        self.organizer.get_path_suggestions.return_value = {"suggestions": ["path1", "path2", "path3"]}

        with patch("os.path.join", return_value="/path/to/file.txt"):
            suggestion = asyncio.run(self.producer.get_suggestions("file.txt"))

        self.assertEqual(suggestion["fileName"], "file.txt")
        self.assertEqual(suggestion["size"], 1024)
        self.assertEqual(suggestion["downloadDate"], "2024-12-01 12:00:00")
        self.summarizer.summarize_document.assert_called_once()

class TestWatchdogHandler(unittest.TestCase):
    def setUp(self):
        self.producer = MagicMock()
        self.handler = WatchdogHandler(producer=self.producer)

    def test_on_created(self):
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/path/to/file.txt"

        self.handler.on_created(event)
        self.producer.on_created.assert_called_once_with(event)
        
class TestFastAPIEndpoints(unittest.TestCase):
    def setUp(self):
        # Create a test client for the FastAPI app
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_health_check(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_batch_organize_path_not_found(self):
        response = self.client.post("/batch-organize", json={"path": "/invalid/path"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Path not found"})

    def test_batch_organize_valid(self):
        # Mock or use a valid path for the test
        with unittest.mock.patch("os.path.exists", return_value=True):
            response = self.client.post("/batch-organize", json={"path": "/Users/shreyasskasetty/Desktop/github_projects/CortexFS/files"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("status", response.json())
            self.assertIn("treeStructure", response.json())

    def test_commit(self):
        response = self.client.post("/commit", json={
            "base_path": "/Users/shreyasskasetty/Desktop/github_projects/CortexFS/files",
            "src_path": "Docker.dmg",
            "dst_path": "data/"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Commit successful"})

    def test_commit_suggestion_source_not_found(self):
        response = self.client.post("/commit-suggestion", json={
            "src_path": "/invalid/src",
            "dst_path": "/valid/dst"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Source path does not exist in filesystem'})

    def test_commit_suggestion_valid(self):
        # Mock the filesystem
        with unittest.mock.patch("os.path.exists", side_effect=lambda path: path in ["/Users/shreyasskasetty/Desktop/github_projects/CortexFS/backend/file.txt", "/Users/shreyasskasetty/Desktop/github_projects/CortexFS/files"]):
            response = self.client.post("/commit-suggestion", json={
                "src_path": "/Users/shreyasskasetty/Desktop/github_projects/CortexFS/backend/file.txt",
                "dst_path": "/Users/shreyasskasetty/Desktop/github_projects/CortexFS/files"
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"message": "Commit successful"})

    def test_start_producer(self):
        response = self.client.post("/start-producer", json={
            "watch_directory": "/Users/shreyasskasetty/Desktop/github_projects/CortexFS/backend",
            "target_directory": "/Users/shreyasskasetty/Desktop/github_projects/CortexFS/files"
        })
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())
        self.assertEqual(response.json()["status"], "Producer started")

    def test_start_producer_invalid_directory(self):
        response = self.client.post("/start-producer", json={
            "watch_directory": "/invalid/watch",
            "target_directory": "/valid/target"
        })
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    def test_stop_producer(self):
        response = self.client.post("/start-producer", json={
            "watch_directory": "/Users/shreyasskasetty/Desktop/github_projects/CortexFS/backend",
            "target_directory": "/Users/shreyasskasetty/Desktop/github_projects/CortexFS/files"
        })
        response = self.client.post("/stop-producer")
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "Producer stopped"})

if __name__ == "__main__":
    unittest.main()
