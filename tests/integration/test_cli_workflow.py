import unittest
import os
import subprocess
import time
import tempfile
import shutil
from pathlib import Path
import git
from click.testing import CliRunner

from src.cli import cli

# This is a full integration test that requires Docker and a valid OpenAI API key.
# It will start a MindsDB container, run the full CLI workflow, and then shut it down.
# NOTE: This test will fail if the provided OpenAI API key does not have credits.
class TestCLIWorkflow(unittest.TestCase):
    _mindsdb_up = False

    @classmethod
    def setUpClass(cls):
        """Set up the integration test environment by starting MindsDB."""
        print("Starting MindsDB container for integration test...")
        try:
            # Use docker-compose to start MindsDB in detached mode
            subprocess.run(
                "docker-compose up -d", 
                shell=True, 
                check=True, 
                capture_output=True
            )
            cls._mindsdb_up = True
            # Wait for the container to initialize and be ready
            print("Waiting for MindsDB to become available (this may take a minute)...")
            time.sleep(45) # Give MindsDB ample time to start
        except subprocess.CalledProcessError as e:
            print("ERROR: Failed to start MindsDB container. Is Docker running?")
            print(e.stdout.decode())
            print(e.stderr.decode())
            # We don't raise an exception so we can skip the test gracefully
        except FileNotFoundError:
            print("ERROR: `docker-compose` command not found. Is Docker installed?")


    @classmethod
    def tearDownClass(cls):
        """Tear down the integration test environment."""
        if cls._mindsdb_up:
            print("Stopping MindsDB container...")
            subprocess.run("docker-compose down", shell=True, check=True)

    def setUp(self):
        """Set up for each test case."""
        if not self._mindsdb_up:
            self.skipTest("MindsDB container is not running, skipping integration test.")
            
        # Skip the test if the API key is not available as an environment variable
        self.api_key = os.getenv("TEST_OPENAI_API_KEY")
        if not self.api_key:
            self.skipTest("TEST_OPENAI_API_KEY environment variable not set.")

        self.runner = CliRunner()
        self.repo_dir = tempfile.mkdtemp(prefix="test_repo_")
        self.repo = git.Repo.init(self.repo_dir)

        # Create a dummy Python file in the test repository
        (Path(self.repo_dir) / "app.py").write_text(
            "def sample_function():\n    return 'This is a test function.'"
        )
        self.repo.index.add(["app.py"])
        self.repo.index.commit("Initial commit")
        
        # Environment for the test run
        self.env = {
            "OPENAI_API_KEY": self.api_key,
            "CI": "true"  # Ensure plain text output from `rich`
        }

    def tearDown(self):
        """Clean up after each test case."""
        shutil.rmtree(self.repo_dir)

    def test_full_cli_workflow(self):
        """
        Tests the complete user workflow:
        1. Initialize the Knowledge Base.
        2. Ingest a local Git repository.
        3. Query the ingested code.
        4. Reset the Knowledge Base.
        """
        with self.runner.isolated_filesystem():
            # The CliRunner's context manager sets the environment
            result = self.runner.invoke(cli, ["kb:init", "--force"], env=self.env)
            self.assertEqual(result.exit_code, 0, f"kb:init failed:\n{result.output}")
            self.assertIn("Knowledge base 'codebase_kb' is ready for ingestion", result.output)

            # 2. Ingest the test repository
            repo_url = f"file://{self.repo_dir}"
            result = self.runner.invoke(cli, ["kb:ingest", repo_url], env=self.env)
            self.assertEqual(result.exit_code, 0, f"kb:ingest failed:\n{result.output}")
            self.assertIn("Repository ingestion completed successfully", result.output)

            # 3. Query the ingested code
            result = self.runner.invoke(cli, ["kb:query", "test function"], env=self.env)
            self.assertEqual(result.exit_code, 0, f"kb:query failed:\n{result.output}")
            self.assertIn("sample_function", result.output) # Check if our function was found

            # 4. Reset the Knowledge Base
            result = self.runner.invoke(cli, ["kb:reset", "--force"], env=self.env)
            self.assertEqual(result.exit_code, 0, f"kb:reset failed:\n{result.output}")
            self.assertIn("Knowledge base reset completed successfully", result.output)

if __name__ == '__main__':
    unittest.main()
