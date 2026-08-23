from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(tags=["Products"])


@router.post(
    "",
    response_model=APIResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Registers a new packaged commodity in the product catalog.",
)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.INSPECTOR)),
) -> APIResponse[ProductResponse]:
    """Create a new product."""
    product = await ProductService.create_product(db, payload)
    return APIResponse(
        success=True,
        data=ProductResponse.model_validate(product),
        message="Product created successfully",
    )


@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
    summary="List products",
    description="Retrieves a paginated list of products with optional text search and category filtering.",
)
async def list_products(
    query: Optional[str] = Query(default=None, description="Search term for name, barcode, or manufacturer"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[ProductResponse]:
    """List products with pagination and search."""
    products, total_items = await ProductService.list_products(
        db=db, query=query, category=category, page=page, page_size=page_size
    )
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0

    return PaginatedResponse(
        success=True,
        data=[ProductResponse.model_validate(p) for p in products],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
        message="Products retrieved successfully",
    )


@router.get(
    "/{product_id}",
    response_model=APIResponse[ProductResponse],
    summary="Get product by ID",
    description="Retrieves single product details by product ID.",
)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ProductResponse]:
    """Get single product details."""
    product = await ProductService.get_product(db, product_id)
    return APIResponse(
        success=True,
        data=ProductResponse.model_validate(product),
        message="Product retrieved successfully",
    )


@router.put(
    "/{product_id}",
    response_model=APIResponse[ProductResponse],
    summary="Update product",
    description="Updates existing product details.",
)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.INSPECTOR)),
) -> APIResponse[ProductResponse]:
    """Update product details."""
    updated = await ProductService.update_product(db, product_id, payload)
    return APIResponse(
        success=True,
        data=ProductResponse.model_validate(updated),
        message="Product updated successfully",
    )


@router.delete(
    "/{product_id}",
    response_model=APIResponse[dict],
    summary="Delete product",
    description="Removes a product from the database (Admin only).",
)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> APIResponse[dict]:
    """Delete product."""
    await ProductService.delete_product(db, product_id)
    return APIResponse(
        success=True,
        data={"product_id": product_id},
        message="Product deleted successfully",
    )
