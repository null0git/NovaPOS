from marshmallow import Schema, fields, validate


class ReportPeriodSchema(Schema):
    period = fields.String(
        required=False, load_default="today",
        validate=validate.OneOf(["today", "week", "month", "year", "custom"])
    )
    start_date = fields.DateTime(required=False, allow_none=True)
    end_date = fields.DateTime(required=False, allow_none=True)


class SalesReportResponseSchema(Schema):
    period = fields.String()
    total_sales_count = fields.Integer()
    total_revenue = fields.Float()
    total_tax = fields.Float()
    total_discount = fields.Float()
    average_sale_value = fields.Float()


class ProfitReportResponseSchema(Schema):
    period = fields.String()
    total_revenue = fields.Float()
    total_cost = fields.Float()
    gross_profit = fields.Float()
    margin_percent = fields.Float()


class TopProductSchema(Schema):
    product_id = fields.Integer()
    product_name = fields.String()
    quantity_sold = fields.Integer()
    revenue = fields.Float()
