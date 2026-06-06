from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseResponse, WarehouseCreate, WarehouseUpdate
from app.services import audit_service

router = APIRouter()


@router.get("/", response_model=list[WarehouseResponse])
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).order_by(Warehouse.name).all()


@router.post("/", response_model=WarehouseResponse, status_code=201)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wh = Warehouse(**payload.model_dump())
    db.add(wh)
    db.commit()
    db.refresh(wh)
    audit_service.log_action(
        db, action_type="create_warehouse", user_id=current_user.id,
        entity_type="warehouse", entity_id=wh.id,
        extra_data={"name": wh.name, "city": wh.city},
    )
    return wh


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return wh


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(wh, key, val)
    db.commit()
    db.refresh(wh)
    audit_service.log_action(
        db, action_type="update_warehouse", user_id=current_user.id,
        entity_type="warehouse", entity_id=warehouse_id,
        extra_data={"name": wh.name, "city": wh.city},
    )
    return wh


@router.delete("/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    name, city = wh.name, wh.city
    db.delete(wh)
    db.commit()
    audit_service.log_action(
        db, action_type="delete_warehouse", user_id=current_user.id,
        entity_type="warehouse", entity_id=warehouse_id,
        extra_data={"name": name, "city": city},
    )
    return {"detail": "Warehouse deleted"}
