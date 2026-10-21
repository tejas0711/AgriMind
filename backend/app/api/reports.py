from __future__ import annotations

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, SavedReport
from app.api.deps import get_current_user
from app.models.auth import ReportSaveRequest, ReportResponse, ReportSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def save_report(
    req: ReportSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """Saves an analyzed soil report and recommendations associated with the authenticated user."""
    report = SavedReport(
        user_id=current_user.id,
        title=req.title or "Soil Health Analysis",
        farm_name=req.farm_name,
        location_name=req.location_name,
        latitude=req.latitude,
        longitude=req.longitude,
        selected_crop=req.selected_crop,
        soil_data=req.soil_data,
        deficiencies=req.deficiencies,
        crop_scores=req.crop_scores,
        fertilizer_options=req.fertilizer_options,
        application_window=req.application_window,
        evidence=req.evidence,
        explanation=req.explanation,
        llm_provider=req.llm_provider,
        llm_model=req.llm_model,
        is_llm_fallback=req.is_llm_fallback,
        notes=req.notes,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    logger.info("Saved soil report ID %s for user ID %s", report.id, current_user.id)
    return ReportResponse.model_validate(report)


@router.get("", response_model=List[ReportSummary])
def list_saved_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ReportSummary]:
    """Lists saved reports belonging strictly to the authenticated user."""
    reports = (
        db.query(SavedReport)
        .filter(SavedReport.user_id == current_user.id)
        .order_by(SavedReport.created_at.desc())
        .all()
    )
    return [ReportSummary.model_validate(r) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_saved_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """Retrieves full details of a saved report, strictly enforcing user ownership."""
    report = db.query(SavedReport).filter(SavedReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil report #{report_id} was not found.",
        )

    # Authorization Check: User can only access their own reports
    if report.user_id != current_user.id:
        logger.warning(
            "Unauthorized access attempt: User %s tried to access report %s belonging to user %s",
            current_user.id,
            report_id,
            report.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this report.",
        )

    return ReportResponse.model_validate(report)


@router.delete("/{report_id}")
def delete_saved_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a saved report, strictly enforcing user ownership."""
    report = db.query(SavedReport).filter(SavedReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil report #{report_id} was not found.",
        )

    # Authorization Check: User can only delete their own reports
    if report.user_id != current_user.id:
        logger.warning(
            "Unauthorized delete attempt: User %s tried to delete report %s belonging to user %s",
            current_user.id,
            report_id,
            report.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this report.",
        )

    db.delete(report)
    db.commit()
    logger.info("Deleted report ID %s by user ID %s", report_id, current_user.id)
    return {"status": "deleted", "id": report_id}
