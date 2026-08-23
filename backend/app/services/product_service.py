from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    @staticmethod
    async def create_product(db: AsyncSession, payload: ProductCreate) -> Product:
        """Create a new product record."""
        if payload.barcode:
            existing = await db.execute(
                select(Product).where(Product.barcode == payload.barcode.strip())
            )
            if existing.scalar_one_or_none():
                raise ValidationError(f"Product with barcode '{payload.barcode}' already exists")

        product = Product(
            product_name=payload.product_name.strip(),
            barcode=payload.barcode.strip() if payload.barcode else None,
            category=payload.category.strip() if payload.category else None,
            manufacturer=payload.manufacturer.strip() if payload.manufacturer else None,
        )
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def get_product(db: AsyncSession, product_id: int) -> Product:
        """Retrieve a product by its ID."""
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise NotFoundError(f"Product with ID {product_id} not found")
        return product

    @staticmethod
    async def get_by_barcode(db: AsyncSession, barcode: str) -> Optional[Product]:
        """Look up product by barcode."""
        result = await db.execute(select(Product).where(Product.barcode == barcode.strip()))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_products(
        db: AsyncSession,
        query: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Product], int]:
        """List products with search and pagination."""
        stmt = select(Product)
        count_stmt = select(func.count(Product.id))

        filters = []
        if query:
            search = f"%{query.strip()}%"
            filters.append(
                or_(
                    Product.product_name.ilike(search),
                    Product.barcode.ilike(search),
                    Product.manufacturer.ilike(search),
                )
            )

        if category:
            filters.append(Product.category.ilike(f"%{category.strip()}%"))

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        # Get total count
        total_result = await db.execute(count_stmt)
        total_items = total_result.scalar_one() or 0

        # Pagination & sorting
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Product.id.desc()).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        products = list(result.scalars().all())

        return products, total_items

    @staticmethod
    async def update_product(
        db: AsyncSession, product_id: int, payload: ProductUpdate
    ) -> Product:
        """Update product details."""
        product = await ProductService.get_product(db, product_id)

        update_data = payload.model_dump(exclude_unset=True)
        if "barcode" in update_data and update_data["barcode"]:
            existing = await db.execute(
                select(Product).where(
                    Product.barcode == update_data["barcode"].strip(),
                    Product.id != product_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ValidationError(f"Barcode '{update_data['barcode']}' is already in use by another product")

        for key, value in update_data.items():
            if value is not None:
                setattr(product, key, value.strip() if isinstance(value, str) else value)

        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def delete_product(db: AsyncSession, product_id: int) -> bool:
        """Delete a product."""
        product = await ProductService.get_product(db, product_id)
        await db.delete(product)
        await db.commit()
        return True
