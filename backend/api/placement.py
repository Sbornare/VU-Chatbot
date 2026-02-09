from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from typing import List, Optional
import tempfile
import os
from functools import lru_cache
import time
from backend.database import get_db
from backend.models.placement import Company, JobOpening, Placement, PlacementStats
from backend.services.placement_ingestion import ingest_placement_data
from backend.auth.dependencies import get_current_user
from backend.auth.models import User

router = APIRouter()


@router.post("/upload-placement-data")
async def upload_placement_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload Excel file with placement data (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Please upload an Excel file (.xlsx or .xls)")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Process the Excel file
        results = ingest_placement_data(temp_file_path)
        
        return {
            "message": "Placement data uploaded successfully",
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(500, f"Error processing file: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@router.get("/companies")
def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get list of companies"""
    query = db.query(Company)
    
    if search:
        query = query.filter(Company.name.ilike(f"%{search}%"))
    
    total = query.count()
    companies = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "companies": companies
    }


@router.get("/placements")
def get_placements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    program: str = Query(None),
    company_name: str = Query(None),
    min_package: float = Query(None),
    graduation_year: int = Query(None),
    db: Session = Depends(get_db)
):
    """Get placement records with filters"""
    query = db.query(Placement)
    
    if program:
        query = query.filter(Placement.program.ilike(f"%{program}%"))
    
    if company_name:
        query = query.join(Company).filter(Company.name.ilike(f"%{company_name}%"))
    
    if min_package:
        query = query.filter(Placement.package >= min_package)
    
    if graduation_year:
        query = query.filter(Placement.graduation_year == graduation_year)
    
    total = query.count()
    placements = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "placements": placements
    }


@router.get("/placement-stats")
def get_placement_stats(
    program: str = Query(None),
    graduation_year: int = Query(None),
    db: Session = Depends(get_db)
):
    """Get placement statistics"""
    query = db.query(Placement)
    
    if program:
        query = query.filter(Placement.program.ilike(f"%{program}%"))
    
    if graduation_year:
        query = query.filter(Placement.graduation_year == graduation_year)
    
    placements = query.all()
    
    if not placements:
        return {
            "message": "No placement data found for the specified filters",
            "stats": {}
        }
    
    # Calculate statistics
    total_placements = len(placements)
    packages = [p.package for p in placements if p.package]
    
    # Company-wise statistics
    company_stats = {}
    for placement in placements:
        if placement.company:
            company_name = placement.company.name
            if company_name not in company_stats:
                company_stats[company_name] = {
                    'count': 0,
                    'packages': []
                }
            company_stats[company_name]['count'] += 1
            if placement.package:
                company_stats[company_name]['packages'].append(placement.package)
    
    # Top recruiters
    top_recruiters = sorted(
        company_stats.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:10]
    
    return {
        "total_placements": total_placements,
        "average_package": sum(packages) / len(packages) if packages else 0,
        "highest_package": max(packages) if packages else 0,
        "lowest_package": min(packages) if packages else 0,
        "top_recruiters": [
            {
                "company": name,
                "placements": stats['count'],
                "avg_package": sum(stats['packages']) / len(stats['packages']) if stats['packages'] else 0
            }
            for name, stats in top_recruiters
        ]
    }


@router.get("/placement-trends")
def get_placement_trends(db: Session = Depends(get_db)):
    """Get placement trends over years"""
    trends = db.query(
        Placement.graduation_year,
        func.count(Placement.id).label('total_placements'),
        func.avg(Placement.package).label('avg_package'),
        func.max(Placement.package).label('max_package')
    ).filter(
        Placement.graduation_year.isnot(None)
    ).group_by(
        Placement.graduation_year
    ).order_by(
        Placement.graduation_year
    ).all()
    
    return {
        "trends": [
            {
                "year": trend.graduation_year,
                "total_placements": trend.total_placements,
                "average_package": float(trend.avg_package) if trend.avg_package else 0,
                "highest_package": float(trend.max_package) if trend.max_package else 0
            }
            for trend in trends
        ]
    }


@router.get("/search-placements")
def search_placements(
    query: str = Query(..., min_length=2),
    db: Session = Depends(get_db)
):
    """Search placements by student name, company, or job title"""
    placements = db.query(Placement).join(Company).filter(
        (Placement.student_name.ilike(f"%{query}%")) |
        (Company.name.ilike(f"%{query}%")) |
        (Placement.job_title.ilike(f"%{query}%")) |
        (Placement.program.ilike(f"%{query}%"))
    ).limit(50).all()
    
    return {
        "results": placements,
        "count": len(placements)
    }


@router.get("/companies/{company_id}/placements")
def get_company_placements(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Get all placements for a specific company"""
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(404, "Company not found")
    
    placements = db.query(Placement).filter(Placement.company_id == company_id).all()
    
    return {
        "company": company,
        "placements": placements,
        "total_placements": len(placements)
    }