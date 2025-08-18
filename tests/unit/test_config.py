import unittest
import os
from unittest.mock import patch

from src.config import MindsDBConfig, KnowledgeBaseConfig, StressTestConfig, AppConfig

class TestConfig(unittest.TestCase):

    def test_mindsdb_config_defaults(self):
        """Test that MindsDBConfig has correct default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = MindsDBConfig()
            self.assertEqual(config.host, "127.0.0.1")
            self.assertEqual(config.port, 47334)
            self.assertEqual(config.user, "")
            self.assertEqual(config.password, "")
            self.assertEqual(config.database, "mindsdb")
            self.assertEqual(config.connection_url, "http://127.0.0.1:47334")
            self.assertFalse(config.is_cloud_connection)

    @patch.dict(os.environ, {
        "MINDSDB_HOST": "localhost",
        "MINDSDB_PORT": "47335",
        "MINDSDB_USER": "testuser",
        "MINDSDB_PASSWORD": "testpassword",
        "MINDSDB_DATABASE": "testdb"
    })
    def test_mindsdb_config_env_vars(self):
        """Test that MindsDBConfig loads values from environment variables."""
        config = MindsDBConfig()
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 47335)
        self.assertEqual(config.user, "testuser")
        self.assertEqual(config.password, "testpassword")
        self.assertEqual(config.database, "testdb")
        self.assertEqual(config.connection_url, "http://localhost:47335")
        self.assertTrue(config.is_cloud_connection)

    def test_kb_config_defaults(self):
        """Test that KnowledgeBaseConfig has correct default values."""
        config = KnowledgeBaseConfig()
        self.assertEqual(config.name, "codebase_kb")
        self.assertEqual(config.embedding_model, "text-embedding-3-large")
        self.assertEqual(config.reranking_model, "gpt-3.5-turbo")
        self.assertEqual(config.openai_api_key, "")
        self.assertIsNotNone(config.metadata_columns)
        self.assertIsNotNone(config.content_columns)

    @patch.dict(os.environ, {
        "KB_NAME": "my_kb",
        "EMBEDDING_MODEL": "custom-embedding",
        "RERANKING_MODEL": "custom-reranking",
        "OPENAI_API_KEY": "test-key"
    })
    def test_kb_config_env_vars(self):
        """Test that KnowledgeBaseConfig loads values from environment variables."""
        config = KnowledgeBaseConfig()
        self.assertEqual(config.name, "my_kb")
        self.assertEqual(config.embedding_model, "custom-embedding")
        self.assertEqual(config.reranking_model, "custom-reranking")
        self.assertEqual(config.openai_api_key, "test-key")

    def test_stress_test_config_defaults(self):
        """Test that StressTestConfig has correct default values."""
        config = StressTestConfig()
        self.assertEqual(config.max_concurrent_queries, 100)
        self.assertEqual(config.stress_test_duration, 300)
        self.assertEqual(config.batch_size, 500)
        self.assertEqual(config.threads, 10)

    @patch.dict(os.environ, {
        "MAX_CONCURRENT_QUERIES": "200",
        "STRESS_TEST_DURATION": "600",
        "BATCH_SIZE": "1000",
        "THREADS": "20"
    })
    def test_stress_test_config_env_vars(self):
        """Test that StressTestConfig loads values from environment variables."""
        config = StressTestConfig()
        self.assertEqual(config.max_concurrent_queries, 200)
        self.assertEqual(config.stress_test_duration, 600)
        self.assertEqual(config.batch_size, 1000)
        self.assertEqual(config.threads, 20)

    def test_app_config_validation_missing_key(self):
        """Test that AppConfig validation fails without an OpenAI API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            app_config = AppConfig()
            with self.assertRaises(ValueError):
                app_config.validate()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "a-valid-key"})
    def test_app_config_validation_with_key(self):
        """Test that AppConfig validation succeeds with an OpenAI API key."""
        app_config = AppConfig()
        self.assertTrue(app_config.validate())

if __name__ == '__main__':
    unittest.main()
