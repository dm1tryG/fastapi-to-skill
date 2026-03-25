"""Example FastAPI app: simple task manager.

Generate CLI + SKILL.md:
    fastapi-to-skill generate examples.task_manager:app -o ./skills/task-manager/

Install and use:
    cd skills/task-manager && pip install -e .
    task-manager-api --help
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Task Manager API",
    description="Simple task manager — demo for fastapi-to-skill",
    version="1.0.0",
)

tasks: dict[int, dict] = {}
_next_id = 1


class Task(BaseModel):
    title: str
    description: Optional[str] = None
    done: bool = False


class TaskOut(Task):
    id: int


@app.get("/tasks", response_model=list[TaskOut], tags=["tasks"])
def list_tasks(done: Optional[bool] = None):
    """List all tasks, optionally filter by done status."""
    result = list(tasks.values())
    if done is not None:
        result = [t for t in result if t["done"] == done]
    return result


@app.post("/tasks", response_model=TaskOut, tags=["tasks"])
def create_task(task: Task):
    """Create a new task."""
    global _next_id
    t = {"id": _next_id, **task.model_dump()}
    tasks[_next_id] = t
    _next_id += 1
    return t


@app.get("/tasks/{task_id}", response_model=TaskOut, tags=["tasks"])
def get_task(task_id: int):
    """Get a task by ID."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]


@app.put("/tasks/{task_id}", response_model=TaskOut, tags=["tasks"])
def update_task(task_id: int, task: Task):
    """Update a task by ID."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    t = {"id": task_id, **task.model_dump()}
    tasks[task_id] = t
    return t


@app.delete("/tasks/{task_id}", tags=["tasks"])
def delete_task(task_id: int):
    """Delete a task by ID."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    return {"ok": True}
