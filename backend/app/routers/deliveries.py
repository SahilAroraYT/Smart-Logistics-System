from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.delivery import DeliveryListResponse, DeliveryResponse, PredictionRequest, PredictionResponse, ManualDeliveryCreate
from app.services import ml_service, delivery_service, assignment_service

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


@router.post("/manual")
def create_manual_delivery(payload: ManualDeliveryCreate, db: Session = Depends(get_db)):
    delivery = assignment_service.create_manual_delivery(
        db, payload.session_id or 0,
        customer_name=payload.customer_name,
        delivery_street=payload.delivery_street,
        delivery_city=payload.delivery_city,
        delivery_pincode=payload.delivery_pincode,
        customer_lat=payload.customer_lat,
        customer_lon=payload.customer_lon,
        package_weight=payload.package_weight,
    )
    return {
        "id": delivery.id,
        "order_id": delivery.order_id,
        "customer_name": delivery.customer_name,
        "delivery_street": delivery.delivery_street,
        "delivery_city": delivery.delivery_city,
        "delivery_pincode": delivery.delivery_pincode,
        "customer_lat": delivery.customer_lat,
        "customer_lon": delivery.customer_lon,
        "risk_score": delivery.risk_score,
        "risk_category": delivery.risk_category,
        "status": delivery.status,
    }
