import csv
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field


CSV_FILE = Path(__file__).with_name("employees.csv")
CSV_FIELDS = ["employee_id", "name", "age", "salary"]

app = FastAPI(title="Employee API")


class EmployeeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    age: int = Field(ge=0)
    salary: float = Field(ge=0)


class EmployeeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1)
    age: int | None = Field(default=None, ge=0)
    salary: float | None = Field(default=None, ge=0)


def read_employees() -> list[dict[str, str]]:
    if not CSV_FILE.exists():
        return []
    with CSV_FILE.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_employees(employees: list[dict[str, str]]) -> None:
    with CSV_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(employees)


@app.post("/employees", status_code=status.HTTP_201_CREATED)
def create_employee(employee: EmployeeCreate) -> dict[str, object]:
    employees = read_employees()
    next_id = max((int(row["employee_id"]) for row in employees), default=0) + 1
    new_employee = {
        "employee_id": str(next_id),
        "name": employee.name,
        "age": str(employee.age),
        "salary": str(employee.salary),
    }
    employees.append(new_employee)
    write_employees(employees)
    return {
        "employee_id": next_id,
        "name": employee.name,
        "age": employee.age,
        "salary": employee.salary,
    }

@app.get("/test")
def get_test():
    return "testing"

@app.get("/employees")
def get_employees() -> list[dict[str, object]]:
    return [
        {
            "employee_id": int(row["employee_id"]),
            "name": row["name"],
            "age": int(row["age"]),
            "salary": float(row["salary"]),
        }
        for row in read_employees()
    ]


@app.get("/employees/{employee_id}")
def get_employee(employee_id: int) -> dict[str, object]:
    for row in read_employees():
        if int(row["employee_id"]) == employee_id:
            return {
                "employee_id": employee_id,
                "name": row["name"],
                "age": int(row["age"]),
                "salary": float(row["salary"]),
            }
    raise HTTPException(status_code=404, detail="Employee not found")


@app.patch("/employees/{employee_id}")
def update_employee(employee_id: int, changes: EmployeeUpdate) -> dict[str, object]:
    updates = changes.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")
    if any(value is None for value in updates.values()):
        raise HTTPException(status_code=422, detail="Employee fields cannot be null")

    employees = read_employees()
    for row in employees:
        if int(row["employee_id"]) == employee_id:
            row.update({key: str(value) for key, value in updates.items()})
            write_employees(employees)
            return get_employee(employee_id)
    raise HTTPException(status_code=404, detail="Employee not found")