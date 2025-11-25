"""Integration tests for MCP server functions with Someday filtering."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import things_server


class TestMCPServerFiltering:
    """Test that MCP server functions properly filter Someday project tasks."""

    @pytest.mark.asyncio
    @patch('things_server.things.anytime')
    @patch('things_server.things.get')
    async def test_get_anytime_filters_someday_tasks(self, mock_things_get, mock_anytime):
        """Test that get_anytime filters out tasks from Someday projects."""
        # Mock the anytime() call to return tasks
        mock_anytime.return_value = [
            {'uuid': 'task-1', 'title': 'Someday task', 'project': 'someday-proj', 'type': 'to-do'},
            {'uuid': 'task-2', 'title': 'Active task', 'project': 'active-proj', 'type': 'to-do'},
            {'uuid': 'task-3', 'title': 'No project', 'type': 'to-do'},
        ]
        
        # Mock project lookups
        def get_project(uuid):
            if uuid == 'someday-proj':
                return {'uuid': uuid, 'status': 'someday', 'title': 'Someday Project'}
            elif uuid == 'active-proj':
                return {'uuid': uuid, 'status': 'active', 'title': 'Active Project'}
            return None
        
        mock_things_get.side_effect = get_project
        
        # Access the wrapped function
        result = await things_server.get_anytime.fn()
        
        # Should only include task-2 and task-3
        assert 'task-1' not in result
        assert 'Active task' in result
        assert 'No project' in result

    @pytest.mark.asyncio
    @patch('things_server.things.today')
    @patch('things_server.things.get')
    async def test_get_today_filters_someday_tasks(self, mock_things_get, mock_today):
        """Test that get_today filters out tasks from Someday projects."""
        mock_today.return_value = [
            {'uuid': 'task-4', 'title': 'Today someday task', 'project': 'someday-proj', 'type': 'to-do'},
            {'uuid': 'task-5', 'title': 'Today active task', 'type': 'to-do'},
        ]
        
        mock_things_get.return_value = {'uuid': 'someday-proj', 'status': 'someday'}
        
        result = await things_server.get_today.fn()
        
        # Should only include task-5
        assert 'Today someday task' not in result
        assert 'Today active task' in result

    @pytest.mark.asyncio
    @patch('things_server.things.upcoming')
    @patch('things_server.things.get')
    async def test_get_upcoming_filters_someday_tasks(self, mock_things_get, mock_upcoming):
        """Test that get_upcoming filters out tasks from Someday projects."""
        mock_upcoming.return_value = [
            {'uuid': 'task-6', 'title': 'Upcoming someday', 'project': 'someday-proj', 'type': 'to-do'},
            {'uuid': 'task-7', 'title': 'Upcoming active', 'project': 'active-proj', 'type': 'to-do'},
        ]
        
        def get_project(uuid):
            if uuid == 'someday-proj':
                return {'uuid': uuid, 'status': 'someday'}
            else:
                return {'uuid': uuid, 'status': 'active'}
        
        mock_things_get.side_effect = get_project
        
        result = await things_server.get_upcoming.fn()
        
        # Should only include task-7
        assert 'Upcoming someday' not in result
        assert 'Upcoming active' in result

    @pytest.mark.asyncio
    @patch('things_server.things.anytime')
    async def test_get_anytime_handles_empty_list(self, mock_anytime):
        """Test that get_anytime handles empty results gracefully."""
        mock_anytime.return_value = []
        
        result = await things_server.get_anytime.fn()
        
        assert result == "No items found"

    @pytest.mark.asyncio
    @patch('things_server.things.anytime')
    @patch('things_server.things.get')
    async def test_get_anytime_all_filtered_returns_empty(self, mock_things_get, mock_anytime):
        """Test that get_anytime returns 'No items found' when all tasks are filtered."""
        mock_anytime.return_value = [
            {'uuid': 'task-1', 'title': 'Someday 1', 'project': 'someday-proj', 'type': 'to-do'},
            {'uuid': 'task-2', 'title': 'Someday 2', 'project': 'someday-proj', 'type': 'to-do'},
        ]
        
        mock_things_get.return_value = {'uuid': 'someday-proj', 'status': 'someday'}
        
        result = await things_server.get_anytime.fn()
        
        assert result == "No items found"

