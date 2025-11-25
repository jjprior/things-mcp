# Someday Project Filtering Implementation Summary

## Problem
The Things MCP server was returning ALL tasks with `status='incomplete'` in views like `get_anytime`, `get_today`, and `get_upcoming`, including tasks that belonged to Someday projects. In the Things UI, these tasks correctly appear under their Someday parent projects and don't clutter the active task views. This created a misleading API view with potentially hundreds of extra items.

## Solution
Implemented intelligent filtering to match the Things UI behavior by:

1. **Created a helper function** `filter_someday_project_tasks()` that:
   - Checks each task's parent project (if it has one)
   - Queries the project's status using `things.get()`
   - Filters out tasks whose parent project has `status='someday'`
   - Gracefully handles edge cases (missing projects, lookup errors)

2. **Applied filtering to relevant views**:
   - `get_today()` - Tasks scheduled for today
   - `get_upcoming()` - Tasks scheduled in the future
   - `get_anytime()` - Tasks in the Anytime list
   
3. **Preserved correct behavior** for:
   - `get_inbox()` - Shows all inbox tasks regardless of project
   - `get_someday()` - Shows Someday tasks and projects as expected
   - `get_todos()` - General query function remains unfiltered

## Code Changes

### things_server.py
- Added `filter_someday_project_tasks()` helper function (lines 15-40)
- Updated `get_today()` to apply the filter
- Updated `get_upcoming()` to apply the filter  
- Updated `get_anytime()` to apply the filter

### Tests Added
- **test_someday_filtering.py** - 8 unit tests for the filter function:
  - Removes Someday project tasks
  - Keeps active project tasks
  - Keeps tasks without projects
  - Handles mixed task types
  - Handles missing projects gracefully
  - Handles exceptions without crashing
  - Preserves all task data fields

- **test_mcp_server_filtering.py** - 5 integration tests:
  - Verifies filtering works in get_anytime()
  - Verifies filtering works in get_today()
  - Verifies filtering works in get_upcoming()
  - Handles empty lists correctly
  - Returns "No items found" when all tasks are filtered

### Documentation Updates
- **CHANGELOG.md** - Added entry for Someday project filtering
- **README.md** - Added feature description
- **CLAUDE.md** - Updated architecture and implementation details

## Benefits

1. **Matches Things UI behavior** - API responses now align with what users see in the app
2. **Reduces clutter** - Dramatically reduces the number of tasks returned in active views
3. **Better task focus** - Users see only actionable items in Today/Upcoming/Anytime
4. **Robust implementation** - Comprehensive error handling and test coverage
5. **No breaking changes** - Filtering is transparent to existing integrations

## Testing

All 13 new tests pass successfully:
```bash
cd /mnt/project && uv run pytest tests/ -v
# 13 passed in 1.40s
```

The implementation is production-ready with:
- Unit tests for the core filtering logic
- Integration tests for the MCP server functions
- Edge case handling (missing projects, exceptions)
- Backward compatibility maintained
