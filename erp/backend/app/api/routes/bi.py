"""Business Intelligence Routes."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.database import MongoDB
from app.models.bi import Report, Dashboard, KPI
from apps.shared.dependencies import require_organization_access, OrganizationScoped

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reports", response_model=Report, status_code=status.HTTP_201_CREATED)
async def create_report(report_data: Report, scope: OrganizationScoped = Depends()):
    """Create a new report configuration."""
    db = MongoDB.get_database()
    report_data.organization_id = scope.org_id
    await db.reports.insert_one(report_data.model_dump())
    return report_data


@router.get("/reports", response_model=List[Report])
async def list_reports(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    report_type: Optional[str] = None,
):
    """List all reports."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filter
    if report_type:
        query["report_type"] = report_type

    cursor = db.reports.find(query).skip(skip).limit(limit).sort("created_at", -1)
    reports = await cursor.to_list(length=limit)
    return [Report(**r) for r in reports]


@router.get("/reports/{report_id}", response_model=Report)
async def get_report(
    report_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get report by ID."""
    db = MongoDB.get_database()
    report = await db.reports.find_one({"id": report_id, "organization_id": org_id})

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return Report(**report)


@router.patch("/reports/{report_id}", response_model=Report)
async def update_report(
    report_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update report."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.reports.update_one(
        {"id": report_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report = await db.reports.find_one({"id": report_id})
    return Report(**report)


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete report."""
    db = MongoDB.get_database()

    result = await db.reports.update_one(
        {"id": report_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return None


@router.post("/dashboards", response_model=Dashboard, status_code=status.HTTP_201_CREATED)
async def create_dashboard(dashboard_data: Dashboard, scope: OrganizationScoped = Depends()):
    """Create a new dashboard."""
    db = MongoDB.get_database()
    dashboard_data.organization_id = scope.org_id
    await db.dashboards.insert_one(dashboard_data.model_dump())
    return dashboard_data


@router.get("/dashboards", response_model=List[Dashboard])
async def list_dashboards(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    is_public: Optional[bool] = None,
):
    """List all dashboards."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filter
    if is_public is not None:
        query["is_public"] = is_public

    cursor = db.dashboards.find(query).skip(skip).limit(limit).sort("created_at", -1)
    dashboards = await cursor.to_list(length=limit)
    return [Dashboard(**d) for d in dashboards]


@router.get("/dashboards/{dashboard_id}", response_model=Dashboard)
async def get_dashboard(
    dashboard_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get dashboard by ID."""
    db = MongoDB.get_database()
    dashboard = await db.dashboards.find_one({"id": dashboard_id, "organization_id": org_id})

    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")

    return Dashboard(**dashboard)


@router.patch("/dashboards/{dashboard_id}", response_model=Dashboard)
async def update_dashboard(
    dashboard_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update dashboard."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.dashboards.update_one(
        {"id": dashboard_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")

    dashboard = await db.dashboards.find_one({"id": dashboard_id})
    return Dashboard(**dashboard)


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete dashboard."""
    db = MongoDB.get_database()

    result = await db.dashboards.update_one(
        {"id": dashboard_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")

    return None


@router.post("/kpis", response_model=KPI, status_code=status.HTTP_201_CREATED)
async def create_kpi(kpi_data: KPI, scope: OrganizationScoped = Depends()):
    """Create a new KPI."""
    db = MongoDB.get_database()
    kpi_data.organization_id = scope.org_id
    await db.kpis.insert_one(kpi_data.model_dump())
    return kpi_data


@router.get("/kpis", response_model=List[KPI])
async def list_kpis(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    category: Optional[str] = None,
):
    """List all KPIs."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filter
    if category:
        query["category"] = category

    cursor = db.kpis.find(query).skip(skip).limit(limit).sort("created_at", -1)
    kpis = await cursor.to_list(length=limit)
    return [KPI(**k) for k in kpis]


@router.get("/kpis/{kpi_id}", response_model=KPI)
async def get_kpi(
    kpi_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get KPI by ID."""
    db = MongoDB.get_database()
    kpi = await db.kpis.find_one({"id": kpi_id, "organization_id": org_id})

    if not kpi:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KPI not found")

    return KPI(**kpi)


@router.patch("/kpis/{kpi_id}", response_model=KPI)
async def update_kpi(
    kpi_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update KPI."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.kpis.update_one(
        {"id": kpi_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KPI not found")

    kpi = await db.kpis.find_one({"id": kpi_id})
    return KPI(**kpi)


@router.delete("/kpis/{kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kpi(
    kpi_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete KPI."""
    db = MongoDB.get_database()

    result = await db.kpis.update_one(
        {"id": kpi_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KPI not found")

    return None
