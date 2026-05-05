from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.delivery import DeliveryListResponse, DeliveryResponse, PredictionRequest, PredictionResponse
from app.services import ml_service, delivery_service

router = APIRouter()


@router.get("/", response_model=DeliveryListResponse)
def list_deliveries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    status: str | None = None,
    risk_category: str | None = None,
    db: Session = Depends(get_db),
):
    deliveries, total = delivery_service.get_deliveries(db, page, page_size, status, risk_category)
    return DeliveryListResponse(
        deliveries=[DeliveryResponse.model_validate(d) for d in deliveries],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{delivery_id}", response_model=DeliveryResponse)
def get_delivery(delivery_id: int, db: Session = Depends(get_db)):
    delivery = delivery_service.get_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return DeliveryResponse.model_validate(delivery)


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest):
    data = payload.model_dump()
    result = ml_service.predict(data)
    return PredictionResponse(order_id=payload.order_id, **result)
