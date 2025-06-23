from fastapi import HTTPException
from sqlmodel import Session, SQLModel


def get_item_or_404(session: Session, model: SQLModel, item_id: int):
    """Generic function to get an item by ID or raise 404"""
    item = session.get(model, item_id)
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"{model.__name__} with id {item_id} not found"
        )
    return item
