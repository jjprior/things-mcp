"""Tests for the efficiency changes: UUID read-back, get_orphans,
update_todos batch, search_advanced area+type fix, and brief formatting."""

import pytest
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import things_server
from things_server import get_orphans, search_advanced, add_todo, add_project
from formatters import format_todo


# --- Change 5: format_todo brief mode -------------------------------------

class TestFormatTodoBrief:
    def test_brief_truncates_long_notes(self):
        long_notes = "x" * 250
        todo = {
            'uuid': 'u1', 'title': 'T', 'type': 'to-do', 'notes': long_notes,
        }
        result = format_todo(todo, brief=True)
        assert "x" * 100 + "…" in result
        # The full 250-char run must not survive.
        assert "x" * 101 not in result

    def test_full_keeps_long_notes(self):
        long_notes = "y" * 250
        todo = {
            'uuid': 'u1', 'title': 'T', 'type': 'to-do', 'notes': long_notes,
        }
        result = format_todo(todo, brief=False)
        assert "y" * 250 in result
        assert "…" not in result

    def test_brief_omits_verbose_fields_keeps_minimum(self):
        todo = {
            'uuid': 'u1', 'title': 'My Task', 'type': 'to-do', 'status': 'open',
            'start': 'Anytime', 'modified': '2024-01-01',
            'checklist': [{'title': 'c1', 'status': 'open'}],
        }
        result = format_todo(todo, brief=True)
        # Minimum kept
        assert "Title: My Task" in result
        assert "UUID: u1" in result
        assert "List: Anytime" in result
        # Verbose fields omitted
        assert "Type:" not in result
        assert "Status:" not in result
        assert "Modified:" not in result
        assert "Checklist:" not in result

    def test_full_default_unchanged(self):
        todo = {'uuid': 'u1', 'title': 'My Task', 'type': 'to-do', 'status': 'open'}
        result = format_todo(todo)
        assert "Type: to-do" in result
        assert "Status: open" in result


# --- Change 4: search_advanced area + type collision ----------------------

class TestSearchAdvancedAreaType:
    @pytest.mark.asyncio
    @patch('things_server.things.tasks')
    async def test_area_and_type_together_no_error(self, mock_tasks):
        mock_tasks.return_value = [
            {'uuid': 't1', 'title': 'In area', 'type': 'to-do', 'area': 'area-1'}
        ]
        result = await search_advanced.fn(area='area-1', type='to-do')
        assert 'In area' in result
        # Routed through things.tasks, not things.todos
        mock_tasks.assert_called_once()
        _, kwargs = mock_tasks.call_args
        assert kwargs['area'] == 'area-1'
        assert kwargs['type'] == 'to-do'
        # Default incomplete status preserved
        assert kwargs['status'] == 'incomplete'

    @pytest.mark.asyncio
    @patch('things_server.things.todos')
    async def test_no_type_routes_to_todos(self, mock_todos):
        mock_todos.return_value = [
            {'uuid': 't2', 'title': 'No type', 'type': 'to-do'}
        ]
        result = await search_advanced.fn(area='area-1')
        assert 'No type' in result
        mock_todos.assert_called_once()


# --- Change 2: get_orphans ------------------------------------------------

class TestGetOrphans:
    @pytest.mark.asyncio
    @patch('things_server.things.get')
    @patch('things_server.things.tasks')
    async def test_returns_only_orphans(self, mock_tasks, mock_get):
        mock_tasks.return_value = [
            {'uuid': 'o1', 'title': 'Orphan', 'type': 'to-do', 'project': None, 'area': 'area-1'},
            {'uuid': 'p1', 'title': 'In project', 'type': 'to-do', 'project': 'proj-1', 'area': 'area-1'},
            {'uuid': 'n1', 'title': 'No area', 'type': 'to-do', 'project': None, 'area': None},
        ]
        mock_get.return_value = {'uuid': 'area-1', 'title': 'Area One'}
        result = await get_orphans.fn()
        assert 'Orphan' in result
        assert 'In project' not in result
        assert 'No area' not in result
        assert 'Area: Area One' in result

    @pytest.mark.asyncio
    @patch('things_server.things.get')
    @patch('things_server.things.tasks')
    async def test_respects_area_filter(self, mock_tasks, mock_get):
        mock_tasks.return_value = [
            {'uuid': 'o1', 'title': 'In A', 'type': 'to-do', 'project': None, 'area': 'area-1'},
            {'uuid': 'o2', 'title': 'In B', 'type': 'to-do', 'project': None, 'area': 'area-2'},
        ]
        mock_get.return_value = {'uuid': 'area-1', 'title': 'Area One'}
        result = await get_orphans.fn(area='area-1')
        assert 'In A' in result
        assert 'In B' not in result

    @pytest.mark.asyncio
    @patch('things_server.things.get')
    @patch('things_server.things.tasks')
    async def test_excludes_own_start_someday_by_default(self, mock_tasks, mock_get):
        mock_tasks.return_value = [
            {'uuid': 'o1', 'title': 'Active', 'type': 'to-do', 'project': None, 'area': 'area-1', 'start': 'Anytime'},
            {'uuid': 'o2', 'title': 'Someday orphan', 'type': 'to-do', 'project': None, 'area': 'area-1', 'start': 'Someday'},
        ]
        mock_get.return_value = {'uuid': 'area-1', 'title': 'Area One'}
        result = await get_orphans.fn()
        assert 'Active' in result
        assert 'Someday orphan' not in result

    @pytest.mark.asyncio
    @patch('things_server.things.get')
    @patch('things_server.things.tasks')
    async def test_includes_someday_when_flagged(self, mock_tasks, mock_get):
        mock_tasks.return_value = [
            {'uuid': 'o2', 'title': 'Someday orphan', 'type': 'to-do', 'project': None, 'area': 'area-1', 'start': 'Someday'},
        ]
        mock_get.return_value = {'uuid': 'area-1', 'title': 'Area One'}
        result = await get_orphans.fn(include_someday=True)
        assert 'Someday orphan' in result

    @pytest.mark.asyncio
    @patch('things_server.things.tasks')
    async def test_no_orphans(self, mock_tasks):
        mock_tasks.return_value = []
        result = await get_orphans.fn()
        assert result == "No orphans found"


# --- Change 1: UUID read-back ---------------------------------------------

class TestUuidReadback:
    @pytest.mark.asyncio
    @patch('things_server.url_scheme.execute_url')
    @patch('things_server.things.tasks')
    async def test_add_todo_resolves_uuid(self, mock_tasks, mock_exec):
        mock_tasks.return_value = [
            {'uuid': 'new-uuid', 'title': 'Fresh Todo', 'created': '2024-01-02'},
            {'uuid': 'old-uuid', 'title': 'Fresh Todo', 'created': '2024-01-01'},
        ]
        result = await add_todo.fn(title='Fresh Todo')
        assert 'new-uuid' in result
        assert 'Fresh Todo' in result

    @pytest.mark.asyncio
    @patch('things_server.url_scheme.execute_url')
    @patch('things_server.things.projects')
    async def test_add_project_resolves_uuid(self, mock_projects, mock_exec):
        mock_projects.return_value = [
            {'uuid': 'proj-uuid', 'title': 'Fresh Project', 'created': '2024-01-02'},
        ]
        result = await add_project.fn(title='Fresh Project')
        assert 'proj-uuid' in result

    @pytest.mark.asyncio
    @patch('things_server.time.sleep', return_value=None)
    @patch('things_server.url_scheme.execute_url')
    @patch('things_server.things.tasks')
    async def test_add_todo_not_resolved(self, mock_tasks, mock_exec, mock_sleep):
        # No matching title -> graceful not-resolved path
        mock_tasks.return_value = [
            {'uuid': 'other', 'title': 'Something Else', 'created': '2024-01-01'},
        ]
        result = await add_todo.fn(title='Missing Todo')
        assert 'not resolved' in result
