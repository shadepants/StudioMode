
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure .core modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../.core')))

# Robust Mocking
if 'httpx' not in sys.modules:
    sys.modules['httpx'] = MagicMock()

from services import critic_service

@pytest.fixture
def mock_subprocess():
    with patch('services.critic_service.subprocess.run') as mock:
        yield mock

@pytest.fixture
def mock_exists():
    with patch('services.critic_service.os.path.exists') as mock:
        mock.return_value = True
        yield mock

def test_review_task_success(mock_subprocess, mock_exists):
    # Setup mocks
    # returncode=0 means success
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "Success"
    mock_subprocess.return_value.stderr = ""
    
    service = critic_service.CriticService("test_repo")
    result = service.review_task({'id': '1', 'type': 'REVIEW', 'metadata': {'repo_path': '.'}})
    
    assert result['status'] == 'pass'
    assert result['lint_score'] == 10.0

def test_review_task_issues_found(mock_subprocess, mock_exists):
    # Setup mock: Linter fails (1), Tests pass (0)
    mock_subprocess.side_effect = [
        MagicMock(returncode=1, stdout="Linting errors", stderr="Error details"),
        MagicMock(returncode=0, stdout="Tests passed", stderr="")
    ]
    
    service = critic_service.CriticService("test_repo")
    result = service.review_task({'id': '1', 'type': 'REVIEW', 'metadata': {'repo_path': '.'}})
    
    assert result['status'] == 'issues_found'
    assert len(result['errors']) > 0

def test_path_not_found():
    service = critic_service.CriticService("test_repo")
    # Provide a non-existent path
    result = service.review_task({'id': '1', 'type': 'REVIEW', 'metadata': {'repo_path': 'non_existent_path_12345'}})
    
    assert 'error' in result
    assert 'Path not found' in result['error']