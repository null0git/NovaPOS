"""Unified global search across products, categories, customers, users, sales/receipts, barcodes, variants."""
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.category import Category
from app.models.customer import Customer
from app.models.user import User
from app.models.sale import Sale

RESULT_LIMIT_PER_TYPE = 8


class SearchService:
    def global_search(self, query, limit=RESULT_LIMIT_PER_TYPE):
        like = f"%{query}%"
        results = {
            "products": [
                {"id": p.id, "name": p.name, "sku": p.sku, "barcode": p.barcode, "price": float(p.price)}
                for p in Product.query.filter(
                    (Product.name.ilike(like)) | (Product.sku.ilike(like)) | (Product.barcode.ilike(like))
                ).limit(limit).all()
            ],
            "variants": [
                {"id": v.id, "name": v.name, "sku": v.sku, "barcode": v.barcode,
                 "product_id": v.product_id, "product_name": v.product.name if v.product else None}
                for v in ProductVariant.query.filter(
                    (ProductVariant.name.ilike(like)) | (ProductVariant.sku.ilike(like)) |
                    (ProductVariant.barcode.ilike(like))
                ).limit(limit).all()
            ],
            "categories": [
                {"id": c.id, "name": c.name}
                for c in Category.query.filter(Category.name.ilike(like)).limit(limit).all()
            ],
            "customers": [
                {"id": c.id, "name": c.name, "email": c.email, "phone": c.phone}
                for c in Customer.query.filter(
                    (Customer.name.ilike(like)) | (Customer.email.ilike(like)) | (Customer.phone.ilike(like))
                ).limit(limit).all()
            ],
            "users": [
                {"id": u.id, "username": u.username, "full_name": u.full_name}
                for u in User.query.filter(
                    (User.username.ilike(like)) | (User.full_name.ilike(like))
                ).limit(limit).all()
            ],
            "sales": [
                {"id": s.id, "receipt_number": s.receipt_number, "total_amount": float(s.total_amount),
                 "status": s.status}
                for s in Sale.query.filter(Sale.receipt_number.ilike(like)).limit(limit).all()
            ],
        }
        results["total_count"] = sum(len(v) for v in results.values())
        return results
