from typing import List
import logging
import time
import things
from fastmcp import FastMCP
from formatters import format_todo, format_project, format_area, format_tag
import url_scheme

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Things")


# Helper function to filter out tasks from Someday projects
def filter_someday_project_tasks(todos):
    """Filter out tasks that belong to Someday projects.

    This matches Things UI behavior where tasks from Someday projects
    don't appear in Today, Upcoming, or Anytime views.

    Args:
        todos: List of todo dictionaries

    Returns:
        Filtered list excluding tasks from Someday projects
    """
    # Single query to get all Someday project UUIDs
    try:
        someday_project_ids = {p['uuid'] for p in (things.projects(start='Someday') or [])}
    except Exception:
        return todos
    if not someday_project_ids:
        return todos
    return [todo for todo in todos if todo.get('project') not in someday_project_ids]


def filter_someday(todos, include_someday: bool = False, apply_project_filter: bool = True):
    """Exclude effectively-Someday tasks unless include_someday=True (flag-in).

    A task is effectively Someday if EITHER its own start list is 'Someday', OR
    (when apply_project_filter) its parent project is a Someday project.

    apply_project_filter is set False for explicit single-project drill-downs,
    where the caller named the project and wants its contents regardless.
    """
    if include_someday:
        return todos
    result = [t for t in todos if t.get('start') != 'Someday']
    if apply_project_filter:
        result = filter_someday_project_tasks(result)
    return result


def _find_recent_by_title(title: str, kind: str):
    """Find the most-recently-created item matching `title` exactly.

    The Things URL scheme is fire-and-forget and returns no data, so after a
    create we read back through things.py to resolve the new UUID.

    Args:
        title: Exact title to match
        kind: "to-do" or "project"

    Returns:
        The matching item dict with the max `created` timestamp, or None.
    """
    try:
        if kind == 'project':
            items = things.projects() or []
        else:
            items = things.tasks(type='to-do', status='incomplete') or []
    except Exception:
        return None
    matches = [i for i in items if i.get('title') == title]
    if not matches:
        return None
    return max(matches, key=lambda i: i.get('created') or '')


def _poll_for_uuid(title: str, kind: str, timeout: float = 1.5, interval: float = 0.1):
    """Poll things.py for a just-created item, returning its UUID once found.

    Covers the async write race after firing a Things URL: retries roughly
    every `interval` seconds for up to `timeout` seconds, returning as soon as
    a match appears. Returns None if not found within the window.
    """
    deadline = time.monotonic() + timeout
    while True:
        item = _find_recent_by_title(title, kind)
        if item:
            return item.get('uuid')
        if time.monotonic() >= deadline:
            return None
        time.sleep(interval)


# List view tools
@mcp.tool
async def get_inbox() -> str:
    """Get todos from Inbox"""
    todos = things.inbox(include_items=True)
    if not todos:
        return "No items found"
    formatted_todos = [format_todo(todo) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

@mcp.tool
async def get_today(include_someday: bool = False, brief: bool = False) -> str:
    """Get todos due today

    Args:
        include_someday: Include effectively-Someday items (default False = excluded)
        brief: Lean output for reviews — truncated notes, verbose fields omitted (default False)
    """
    todos = things.today(include_items=True)
    if not todos:
        return "No items found"
    # Exclude Someday by default (flag-in via include_someday)
    todos = filter_someday(todos, include_someday)
    if not todos:
        return "No items found"
    formatted_todos = [format_todo(todo, brief=brief) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

@mcp.tool
async def get_upcoming(include_someday: bool = False, brief: bool = False) -> str:
    """Get upcoming todos

    Args:
        include_someday: Include effectively-Someday items (default False = excluded)
        brief: Lean output for reviews — truncated notes, verbose fields omitted (default False)
    """
    todos = things.upcoming(include_items=True)
    if not todos:
        return "No items found"
    # Exclude Someday by default (flag-in via include_someday)
    todos = filter_someday(todos, include_someday)
    if not todos:
        return "No items found"
    formatted_todos = [format_todo(todo, brief=brief) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

@mcp.tool
async def get_anytime(include_someday: bool = False, brief: bool = False) -> str:
    """Get todos from Anytime list

    Args:
        include_someday: Include effectively-Someday items (default False = excluded)
        brief: Lean output for reviews — truncated notes, verbose fields omitted (default False)
    """
    todos = things.anytime(include_items=True)
    if not todos:
        return "No items found"
    # Exclude Someday by default (flag-in via include_someday)
    todos = filter_someday(todos, include_someday)
    if not todos:
        return "No items found"
    formatted_todos = [format_todo(todo, brief=brief) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

@mcp.tool
async def get_someday(brief: bool = False) -> str:
    """Get todos from Someday list

    Args:
        brief: Lean output for reviews — truncated notes, verbose fields omitted (default False)
    """
    todos = things.someday(include_items=True)
    if not todos:
        return "No items found"
    formatted_todos = [format_todo(todo, brief=brief) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

@mcp.tool
async def get_orphans(area: str = None, include_someday: bool = False, brief: bool = False) -> str:
    """Get orphan to-dos — tasks sitting directly in an area with no parent project.

    Orphans act as a second inbox: they live in an area but were never filed
    under a project. Results are grouped under a header per area.

    Args:
        area: Optional area UUID to restrict to a single area
        include_someday: Include own-start Someday items (default False = excluded).
            The parent-project Someday filter is moot here — orphans have no project.
        brief: Lean output for reviews — truncated notes, verbose fields omitted (default False)
    """
    todos = things.tasks(type='to-do', status='incomplete')
    if not todos:
        return "No orphans found"

    # An orphan has no parent project but does belong to an area.
    orphans = [t for t in todos if t.get('project') is None and t.get('area') is not None]
    if area:
        orphans = [t for t in orphans if t.get('area') == area]

    # Only the own-start Someday filter applies (orphans have no project).
    orphans = filter_someday(orphans, include_someday, apply_project_filter=False)
    if not orphans:
        return "No orphans found"

    # Group by area, preserving first-seen order.
    groups = {}
    for t in orphans:
        groups.setdefault(t.get('area'), []).append(t)

    sections = []
    for area_uuid, items in groups.items():
        area_title = area_uuid
        try:
            a = things.get(area_uuid)
            if a:
                area_title = a.get('title', area_uuid)
        except Exception:
            pass
        body = "\n\n---\n\n".join(format_todo(t, brief=brief) for t in items)
        sections.append(f"# Area: {area_title}\n\n{body}")
    return "\n\n===\n\n".join(sections)

@mcp.tool
async def get_logbook(period: str = "7d", limit: int = 50) -> str:
    """Get completed todos from Logbook, defaults to last 7 days
    
    Args:
        period: Time period to look back (e.g., '3d', '1w', '2m', '1y'). Defaults to '7d'
        limit: Maximum number of entries to return. Defaults to 50
    """
    todos = things.last(period, status='completed', include_items=True)
    if todos and len(todos) > limit:
        todos = todos[:limit]
    if not todos:
        return "No items found"
    formatted_todos = [format_todo(todo) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

@mcp.tool
async def get_trash() -> str:
    """Get trashed todos"""
    todos = things.trash(include_items=True)
    if not todos:
        return "No items found"
    formatted_todos = [format_todo(todo) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

# Basic operations
@mcp.tool
async def get_todos(project_uuid: str = None, include_items: bool = True, include_someday: bool = False, brief: bool = False) -> str:
    """Get todos from Things, optionally filtered by project

    Args:
        project_uuid: Optional UUID of a specific project to get todos from
        include_items: Include checklist items
        include_someday: Include effectively-Someday items (default False = excluded)
        brief: Lean output for reviews — truncated notes, verbose fields omitted (default False)
    """
    if project_uuid:
        project = things.get(project_uuid)
        if not project or project.get('type') != 'project':
            return f"Error: Invalid project UUID '{project_uuid}'"

    todos = things.todos(project=project_uuid, start=None, include_items=include_items)
    if not todos:
        return "No todos found"

    # Drop items individually parked in Someday (flag-in via include_someday).
    # Parent-project filter skipped: an explicit project query should show its contents.
    todos = filter_someday(todos, include_someday, apply_project_filter=False)
    if not todos:
        return "No todos found"

    formatted_todos = [format_todo(todo, brief=brief) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

@mcp.tool
async def get_projects(include_items: bool = False) -> str:
    """Get all projects from Things
    
    Args:
        include_items: Include tasks within projects
    """
    projects = things.projects()
    if not projects:
        return "No projects found"
    
    formatted_projects = [format_project(project, include_items) for project in projects]
    return "\n\n---\n\n".join(formatted_projects)

@mcp.tool
async def get_areas(include_items: bool = False) -> str:
    """Get all areas from Things
    
    Args:
        include_items: Include projects and tasks within areas
    """
    areas = things.areas()
    if not areas:
        return "No areas found"
    
    formatted_areas = [format_area(area, include_items) for area in areas]
    return "\n\n---\n\n".join(formatted_areas)

# Tag operations
@mcp.tool
async def get_tags(include_items: bool = False) -> str:
    """Get all tags
    
    Args:
        include_items: Include items tagged with each tag
    """
    tags = things.tags()
    if not tags:
        return "No tags found"
    
    formatted_tags = [format_tag(tag, include_items) for tag in tags]
    return "\n\n---\n\n".join(formatted_tags)

@mcp.tool
async def get_tagged_items(tag: str) -> str:
    """Get items with a specific tag
    
    Args:
        tag: Tag title to filter by
    """
    todos = things.todos(tag=tag, include_items=True)
    if not todos:
        return f"No items found with tag '{tag}'"
    
    formatted_todos = [format_todo(todo) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

@mcp.tool
async def get_headings(project_uuid: str = None) -> str:
    """Get headings from Things
    
    Args:
        project_uuid: Optional UUID of a specific project to get headings from
    """
    if project_uuid:
        project = things.get(project_uuid)
        if not project or project.get('type') != 'project':
            return f"Error: Invalid project UUID '{project_uuid}'"
        headings = things.tasks(type='heading', project=project_uuid)
    else:
        headings = things.tasks(type='heading')
    
    if not headings:
        return "No headings found"
    
    from formatters import format_heading
    formatted_headings = [format_heading(heading) for heading in headings]
    return "\n\n---\n\n".join(formatted_headings)

# Search operations
@mcp.tool
async def search_todos(query: str) -> str:
    """Search todos by title or notes
    
    Args:
        query: Search term to look for in todo titles and notes
    """
    todos = things.search(query, include_items=True)
    if not todos:
        return f"No todos found matching '{query}'"
    
    formatted_todos = [format_todo(todo) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

@mcp.tool
async def search_advanced(
    status: str = None,
    start_date: str = None,
    deadline: str = None,
    tag: str = None,
    area: str = None,
    type: str = None,
    include_someday: bool = False,
    brief: bool = False
) -> str:
    """Advanced todo search with multiple filters

    Args:
        status: Filter by todo status (incomplete, completed, canceled)
        start_date: Filter by start date (YYYY-MM-DD)
        deadline: Filter by deadline (YYYY-MM-DD)
        tag: Filter by tag
        area: Filter by area UUID
        type: Filter by item type (to-do, project, heading)
        include_someday: Include effectively-Someday items (default False = excluded)
        brief: Lean output for reviews — truncated notes, verbose fields omitted (default False)
    """
    search_params = {}
    if status:
        search_params["status"] = status
    if start_date:
        search_params["start_date"] = start_date
    if deadline:
        search_params["deadline"] = deadline
    if tag:
        search_params["tag"] = tag
    if area:
        search_params["area"] = area
    if type:
        search_params["type"] = type

    # things.todos() injects type='to-do' internally, so passing `type` to it
    # raises "multiple values for keyword argument 'type'". When the caller
    # supplies a type, route through things.tasks() instead (defaulting to
    # incomplete status to preserve things.todos()'s default behavior).
    if type:
        task_params = dict(search_params)
        task_params.setdefault("status", "incomplete")
        todos = things.tasks(include_items=True, **task_params)
    else:
        todos = things.todos(include_items=True, **search_params)
    if not todos:
        return "No matching todos found"

    # Exclude Someday by default (flag-in via include_someday)
    todos = filter_someday(todos, include_someday)
    if not todos:
        return "No matching todos found"

    formatted_todos = [format_todo(todo, brief=brief) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

# Recent items
@mcp.tool
async def get_recent(period: str) -> str:
    """Get recently created items
    
    Args:
        period: Time period (e.g., '3d', '1w', '2m', '1y')
    """
    todos = things.last(period, include_items=True)
    if not todos:
        return f"No items found in the last {period}"
    
    formatted_todos = [format_todo(todo) for todo in todos]
    return "\n\n---\n\n".join(formatted_todos)

# Things URL Scheme tools
@mcp.tool
async def add_todo(
    title: str,
    notes: str = None,
    when: str = None,
    deadline: str = None,
    tags: List[str] = None,
    checklist_items: List[str] = None,
    list_id: str = None,
    list_title: str = None,
    heading: str = None,
    heading_id: str = None
) -> str:
    """Create a new todo in Things
    
    Args:
        title: Title of the todo
        notes: Notes for the todo
        when: When to schedule the todo (today, tomorrow, evening, anytime, someday, or YYYY-MM-DD)
        deadline: Deadline for the todo (YYYY-MM-DD)
        tags: Tags to apply to the todo
        checklist_items: Checklist items to add
        list_id: ID of project/area to add to
        list_title: Title of project/area to add to
        heading: Heading title to add under
        heading_id: Heading ID to add under (takes precedence over heading)
    """
    url = url_scheme.add_todo(
        title=title,
        notes=notes,
        when=when,
        deadline=deadline,
        tags=tags,
        checklist_items=checklist_items,
        list_id=list_id,
        list_title=list_title,
        heading=heading,
        heading_id=heading_id
    )
    url_scheme.execute_url(url)
    # The URL scheme returns nothing; read back through things.py to resolve the UUID.
    uuid = _poll_for_uuid(title, "to-do")
    if uuid:
        return f"Created new todo: {title} (uuid: {uuid})"
    return f"Created new todo: {title} (uuid: not resolved — verify in Things)"

@mcp.tool
async def add_project(
    title: str,
    notes: str = None,
    when: str = None,
    deadline: str = None,
    tags: List[str] = None,
    area_id: str = None,
    area_title: str = None,
    todos: List[str] = None
) -> str:
    """Create a new project in Things
    
    Args:
        title: Title of the project
        notes: Notes for the project
        when: When to schedule the project
        deadline: Deadline for the project
        tags: Tags to apply to the project
        area_id: ID of area to add to
        area_title: Title of area to add to
        todos: Initial todos to create in the project
    """
    url = url_scheme.add_project(
        title=title,
        notes=notes,
        when=when,
        deadline=deadline,
        tags=tags,
        area_id=area_id,
        area_title=area_title,
        todos=todos
    )
    url_scheme.execute_url(url)
    # The URL scheme returns nothing; read back through things.py to resolve the UUID.
    uuid = _poll_for_uuid(title, "project")
    if uuid:
        return f"Created new project: {title} (uuid: {uuid})"
    return f"Created new project: {title} (uuid: not resolved — verify in Things)"

@mcp.tool
async def update_todo(
    id: str,
    title: str = None,
    notes: str = None,
    when: str = None,
    deadline: str = None,
    tags: List[str] = None,
    completed: bool = None,
    canceled: bool = None,
    list: str = None,
    list_id: str = None,
    heading: str = None,
    heading_id: str = None
) -> str:
    """Update an existing todo in Things
    
    Args:
        id: ID of the todo to update
        title: New title
        notes: New notes
        when: New schedule
        deadline: New deadline
        tags: New tags
        completed: Mark as completed
        canceled: Mark as canceled
        list: The title of a project or area to move the to-do into
        list_id: The ID of a project or area to move the to-do into (takes precedence over list)
        heading: The heading title to move the to-do under
        heading_id: The heading ID to move the to-do under (takes precedence over heading)
    """
    url = url_scheme.update_todo(
        id=id,
        title=title,
        notes=notes,
        when=when,
        deadline=deadline,
        tags=tags,
        completed=completed,
        canceled=canceled,
        list=list,
        list_id=list_id,
        heading=heading,
        heading_id=heading_id
    )
    url_scheme.execute_url(url)
    return f"Updated todo with ID: {id}"

@mcp.tool
async def update_todos(
    ids: List[str],
    notes: str = None,
    when: str = None,
    deadline: str = None,
    tags: List[str] = None,
    completed: bool = None,
    canceled: bool = None,
    list: str = None,
    list_id: str = None,
    heading: str = None,
    heading_id: str = None,
    title: str = None
) -> str:
    """Apply the same update to multiple todos in Things (batch).

    Mirrors update_todo but takes a list of ids and applies the identical
    mutation to every one. Each id is fired independently; failures are
    reported per-id rather than aborting the batch.

    Args:
        ids: List of todo IDs to update
        notes: New notes
        when: New schedule
        deadline: New deadline
        tags: New tags
        completed: Mark as completed
        canceled: Mark as canceled
        list: The title of a project or area to move the to-dos into
        list_id: The ID of a project or area to move the to-dos into (takes precedence over list)
        heading: The heading title to move the to-dos under
        heading_id: The heading ID to move the to-dos under (takes precedence over heading)
        title: New title — rarely useful in batch (would set the same title on every id)
    """
    results = []
    for todo_id in ids:
        try:
            url = url_scheme.update_todo(
                id=todo_id,
                title=title,
                notes=notes,
                when=when,
                deadline=deadline,
                tags=tags,
                completed=completed,
                canceled=canceled,
                list=list,
                list_id=list_id,
                heading=heading,
                heading_id=heading_id
            )
            url_scheme.execute_url(url)
            results.append(f"✓ {todo_id}")
        except Exception as e:
            results.append(f"✗ {todo_id}: {e}")
        # Tiny gap so Things doesn't drop rapid successive `open location` events.
        time.sleep(0.05)
    return "\n".join(results)

@mcp.tool
async def update_project(
    id: str,
    title: str = None,
    notes: str = None,
    when: str = None,
    deadline: str = None,
    tags: List[str] = None,
    completed: bool = None,
    canceled: bool = None
) -> str:
    """Update an existing project in Things
    
    Args:
        id: ID of the project to update
        title: New title
        notes: New notes
        when: New schedule
        deadline: New deadline
        tags: New tags
        completed: Mark as completed
        canceled: Mark as canceled
    """
    url = url_scheme.update_project(
        id=id,
        title=title,
        notes=notes,
        when=when,
        deadline=deadline,
        tags=tags,
        completed=completed,
        canceled=canceled
    )
    url_scheme.execute_url(url)
    return f"Updated project with ID: {id}"

@mcp.tool
async def show_item(
    id: str,
    query: str = None,
    filter_tags: List[str] = None
) -> str:
    """Show a specific item or list in Things
    
    Args:
        id: ID of item to show, or one of: inbox, today, upcoming, anytime, someday, logbook
        query: Optional query to filter by
        filter_tags: Optional tags to filter by
    """
    url = url_scheme.show(
        id=id,
        query=query,
        filter_tags=filter_tags
    )
    url_scheme.execute_url(url)
    return f"Showing item: {id}"

@mcp.tool
async def search_items(query: str) -> str:
    """Search for items in Things
    
    Args:
        query: Search query
    """
    url = url_scheme.search(query)
    url_scheme.execute_url(url)
    return f"Searching for '{query}'"

if __name__ == "__main__":
    mcp.run()