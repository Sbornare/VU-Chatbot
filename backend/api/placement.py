from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import Optional
import tempfile
import os
import re
from backend.database import get_db
from backend.services.placement_ingestion import ingest_placement_data
from backend.auth.dependencies import get_current_user

router = APIRouter()


def _clean_docs(items: list[dict]) -> list[dict]:
    cleaned = []
    for item in items:
        data = dict(item)
        data.pop("_id", None)
        cleaned.append(data)
    return cleaned


@router.post("/upload-placement-data")
async def upload_placement_data(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """Upload Excel file with placement data (Admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Please upload an Excel file (.xlsx or .xls)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        results = ingest_placement_data(temp_file_path)
        return {
            "message": "Placement data uploaded successfully",
            "results": results,
        }
    except Exception as e:
        raise HTTPException(500, f"Error processing file: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@router.get("/companies")
def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db=Depends(get_db),
):
    """Get list of companies."""
    filter_query = {}
    if search:
        filter_query["name"] = {"$regex": re.escape(search), "$options": "i"}

    total = db.companies.count_documents(filter_query)
    companies = list(db.companies.find(filter_query, {"_id": 0}).skip(skip).limit(limit))

    return {
        "total": total,
        "companies": companies,
    }


@router.get("/placements")
def get_placements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    program: Optional[str] = Query(None),
    company_name: Optional[str] = Query(None),
    min_package: Optional[float] = Query(None),
    graduation_year: Optional[int] = Query(None),
    db=Depends(get_db),
):
    """Get placement records with filters."""
    filter_query = {}

    if program:
        filter_query["program"] = {"$regex": re.escape(program), "$options": "i"}

    if min_package is not None:
        filter_query["package"] = {"$gte": min_package}

    if graduation_year is not None:
        filter_query["graduation_year"] = graduation_year

    if company_name:
        company_ids = [
            company["id"]
            for company in db.companies.find(
                {"name": {"$regex": re.escape(company_name), "$options": "i"}},
                {"_id": 0, "id": 1},
            )
        ]
        if not company_ids:
            return {"total": 0, "placements": []}
        filter_query["company_id"] = {"$in": company_ids}

    total = db.placements.count_documents(filter_query)
    placements = list(db.placements.find(filter_query, {"_id": 0}).skip(skip).limit(limit))

    company_map = {
        company["id"]: company
        for company in db.companies.find(
            {"id": {"$in": [p.get("company_id") for p in placements if p.get("company_id") is not None]}},
            {"_id": 0},
        )
    }
    for placement in placements:
        cid = placement.get("company_id")
        if cid in company_map:
            placement["company"] = company_map[cid]

    return {
        "total": total,
        "placements": placements,
    }


@router.get("/placement-stats")
def get_placement_stats(
    program: Optional[str] = Query(None),
    graduation_year: Optional[int] = Query(None),
    db=Depends(get_db),
):
    """Get placement statistics."""
    filter_query = {}
    if program:
        filter_query["program"] = {"$regex": re.escape(program), "$options": "i"}
    if graduation_year is not None:
        filter_query["graduation_year"] = graduation_year

    placements = list(db.placements.find(filter_query, {"_id": 0}))

    if not placements:
        return {
            "message": "No placement data found for the specified filters",
            "stats": {},
        }

    company_map = {
        c["id"]: c
        for c in db.companies.find(
            {"id": {"$in": [p.get("company_id") for p in placements if p.get("company_id") is not None]}},
            {"_id": 0, "id": 1, "name": 1},
        )
    }

    packages = [p.get("package") for p in placements if p.get("package") is not None]
    company_stats = {}

    for placement in placements:
        company = company_map.get(placement.get("company_id"))
        if not company:
            continue

        company_name = company.get("name", "Unknown")
        if company_name not in company_stats:
            company_stats[company_name] = {"count": 0, "packages": []}

        company_stats[company_name]["count"] += 1
        if placement.get("package") is not None:
            company_stats[company_name]["packages"].append(placement["package"])

    top_recruiters = sorted(
        company_stats.items(),
        key=lambda x: x[1]["count"],
        reverse=True,
    )[:10]

    return {
        "total_placements": len(placements),
        "average_package": sum(packages) / len(packages) if packages else 0,
        "highest_package": max(packages) if packages else 0,
        "lowest_package": min(packages) if packages else 0,
        "top_recruiters": [
            {
                "company": name,
                "placements": stats["count"],
                "avg_package": (sum(stats["packages"]) / len(stats["packages"])) if stats["packages"] else 0,
            }
            for name, stats in top_recruiters
        ],
    }


@router.get("/placement-trends")
def get_placement_trends(db=Depends(get_db)):
    """Get placement trends over years."""
    pipeline = [
        {"$match": {"graduation_year": {"$ne": None}}},
        {
            "$group": {
                "_id": "$graduation_year",
                "total_placements": {"$sum": 1},
                "avg_package": {"$avg": "$package"},
                "max_package": {"$max": "$package"},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    trends = list(db.placements.aggregate(pipeline))
    return {
        "trends": [
            {
                "year": trend.get("_id"),
                "total_placements": trend.get("total_placements", 0),
                "average_package": float(trend.get("avg_package") or 0),
                "highest_package": float(trend.get("max_package") or 0),
            }
            for trend in trends
        ]
    }


@router.get("/search-placements")
def search_placements(
    query: str = Query(..., min_length=2),
    db=Depends(get_db),
):
    """Search placements by student name, company, or job title."""
    company_ids = [
        company["id"]
        for company in db.companies.find(
            {"name": {"$regex": re.escape(query), "$options": "i"}},
            {"_id": 0, "id": 1},
        )
    ]

    search_filter = {
        "$or": [
            {"student_name": {"$regex": re.escape(query), "$options": "i"}},
            {"job_title": {"$regex": re.escape(query), "$options": "i"}},
            {"program": {"$regex": re.escape(query), "$options": "i"}},
            {"company_id": {"$in": company_ids}} if company_ids else {"company_id": -1},
        ]
    }

    placements = list(db.placements.find(search_filter, {"_id": 0}).limit(50))
    return {
        "results": placements,
        "count": len(placements),
    }


@router.get("/companies/{company_id}/placements")
def get_company_placements(
    company_id: int,
    db=Depends(get_db),
):
    """Get all placements for a specific company."""
    company = db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(404, "Company not found")

    placements = list(db.placements.find({"company_id": company_id}, {"_id": 0}))

    return {
        "company": company,
        "placements": placements,
        "total_placements": len(placements),
    }
