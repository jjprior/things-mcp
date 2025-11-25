"""Tests for filtering tasks from Someday projects."""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path to import things_server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from things_server import filter_someday_project_tasks


class TestSomedayFiltering:
    """Test suite for filtering tasks from Someday projects."""

    @patch('things_server.things.get')
    def test_filter_removes_someday_project_tasks(self, mock_things_get):
        """Test that tasks from Someday projects are filtered out."""
        # Mock project lookup
        mock_things_get.return_value = {
            'uuid': 'project-123',
            'title': 'Someday Project',
            'status': 'someday'
        }
        
        todos = [
            {
                'uuid': 'task-1',
                'title': 'Task in Someday project',
                'project': 'project-123',
                'status': 'incomplete'
            }
        ]
        
        result = filter_someday_project_tasks(todos)
        
        assert len(result) == 0
        mock_things_get.assert_called_once_with('project-123')

    @patch('things_server.things.get')
    def test_filter_keeps_active_project_tasks(self, mock_things_get):
        """Test that tasks from active projects are kept."""
        # Mock project lookup - active project
        mock_things_get.return_value = {
            'uuid': 'project-456',
            'title': 'Active Project',
            'status': 'active'
        }
        
        todos = [
            {
                'uuid': 'task-2',
                'title': 'Task in active project',
                'project': 'project-456',
                'status': 'incomplete'
            }
        ]
        
        result = filter_someday_project_tasks(todos)
        
        assert len(result) == 1
        assert result[0]['uuid'] == 'task-2'
        mock_things_get.assert_called_once_with('project-456')

    def test_filter_keeps_tasks_without_project(self):
        """Test that tasks without a project are kept."""
        todos = [
            {
                'uuid': 'task-3',
                'title': 'Standalone task',
                'status': 'incomplete'
            }
        ]
        
        result = filter_someday_project_tasks(todos)
        
        assert len(result) == 1
        assert result[0]['uuid'] == 'task-3'

    @patch('things_server.things.get')
    def test_filter_mixed_tasks(self, mock_things_get):
        """Test filtering with a mix of task types."""
        # Mock project lookups
        def get_project(uuid):
            if uuid == 'someday-proj':
                return {'uuid': uuid, 'status': 'someday'}
            elif uuid == 'active-proj':
                return {'uuid': uuid, 'status': 'active'}
            return None
        
        mock_things_get.side_effect = get_project
        
        todos = [
            {'uuid': 'task-1', 'title': 'Someday task', 'project': 'someday-proj'},
            {'uuid': 'task-2', 'title': 'Active task', 'project': 'active-proj'},
            {'uuid': 'task-3', 'title': 'No project task'},
            {'uuid': 'task-4', 'title': 'Another someday', 'project': 'someday-proj'},
        ]
        
        result = filter_someday_project_tasks(todos)
        
        assert len(result) == 2
        assert result[0]['uuid'] == 'task-2'
        assert result[1]['uuid'] == 'task-3'

    @patch('things_server.things.get')
    def test_filter_handles_missing_project(self, mock_things_get):
        """Test that tasks with missing projects are kept (graceful handling)."""
        # Mock returns None (project not found)
        mock_things_get.return_value = None
        
        todos = [
            {
                'uuid': 'task-orphan',
                'title': 'Task with missing project',
                'project': 'nonexistent-project'
            }
        ]
        
        result = filter_someday_project_tasks(todos)
        
        # Should keep the task if project can't be found
        assert len(result) == 1
        assert result[0]['uuid'] == 'task-orphan'

    @patch('things_server.things.get')
    def test_filter_handles_exception(self, mock_things_get):
        """Test that exceptions during project lookup don't crash the filter."""
        # Mock throws exception
        mock_things_get.side_effect = Exception("Database error")
        
        todos = [
            {
                'uuid': 'task-error',
                'title': 'Task that causes error',
                'project': 'error-project'
            }
        ]
        
        result = filter_someday_project_tasks(todos)
        
        # Should keep the task despite exception
        assert len(result) == 1
        assert result[0]['uuid'] == 'task-error'

    def test_filter_empty_list(self):
        """Test filtering an empty list."""
        result = filter_someday_project_tasks([])
        assert result == []

    @patch('things_server.things.get')
    def test_filter_preserves_task_data(self, mock_things_get):
        """Test that filtering preserves all task fields."""
        mock_things_get.return_value = {
            'uuid': 'active-proj',
            'status': 'active'
        }
        
        todos = [
            {
                'uuid': 'task-full',
                'title': 'Full task',
                'project': 'active-proj',
                'notes': 'Some notes',
                'tags': ['tag1', 'tag2'],
                'deadline': '2025-12-31',
                'status': 'incomplete'
            }
        ]
        
        result = filter_someday_project_tasks(todos)
        
        assert len(result) == 1
        # Verify all fields are preserved
        assert result[0]['uuid'] == 'task-full'
        assert result[0]['title'] == 'Full task'
        assert result[0]['notes'] == 'Some notes'
        assert result[0]['tags'] == ['tag1', 'tag2']
        assert result[0]['deadline'] == '2025-12-31'
