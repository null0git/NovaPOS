"""Printer management endpoints: discovery, profiles, default, test print."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response, error_response
from app.schemas.printer_schema import PrinterCreateSchema, PrinterUpdateSchema, PrinterDiscoverSchema
from app.services.printer_service import PrinterService

blp = Blueprint("printers", __name__, url_prefix="/api/v1/printers", description="Printer management")


@blp.route("")
class PrintersListResource(MethodView):
    @jwt_required()
    def get(self):
        printers = PrinterService().list_printers()
        return success_response([p.to_dict() for p in printers])

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(PrinterCreateSchema)
    def post(self, data):
        printer = PrinterService().register(current_user_id(), **data)
        return success_response(printer.to_dict(), "Printer saved", 201)


@blp.route("/discover")
class PrinterDiscoverResource(MethodView):
    @jwt_required()
    @blp.arguments(PrinterDiscoverSchema)
    def post(self, data):
        """Client-side discovery agent posts scan results here (manual refresh scan)."""
        printers = PrinterService().discover(data.get("discovered", []))
        return success_response([p.to_dict() for p in printers], "Discovery scan processed")


@blp.route("/<int:printer_id>")
class PrinterDetailResource(MethodView):
    @jwt_required()
    def get(self, printer_id):
        printer = PrinterService().get_printer(printer_id)
        return success_response(printer.to_dict())

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(PrinterUpdateSchema)
    def patch(self, data, printer_id):
        printer = PrinterService().update(current_user_id(), printer_id, **data)
        return success_response(printer.to_dict(), "Printer updated")

    @jwt_required()
    @permission_required("settings.manage")
    def delete(self, printer_id):
        PrinterService().delete(current_user_id(), printer_id)
        return success_response(None, "Printer profile deleted")


@blp.route("/<int:printer_id>/set-default")
class PrinterSetDefaultResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def post(self, printer_id):
        printer = PrinterService().set_default(current_user_id(), printer_id)
        return success_response(printer.to_dict(), "Default printer updated")


@blp.route("/<int:printer_id>/test-print")
class PrinterTestPrintResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage", "settings.manage")
    def post(self, printer_id):
        result = PrinterService().test_print(printer_id)
        return success_response(result, "Test print sent")


@blp.route("/<int:printer_id>/history")
class PrinterHistoryResource(MethodView):
    @jwt_required()
    def get(self, printer_id):
        jobs = PrinterService().get_history(printer_id)
        return success_response([j.to_dict() for j in jobs])


@blp.route("/heartbeat/<string:identifier>")
class PrinterHeartbeatResource(MethodView):
    @blp.doc(security=[])
    def post(self, identifier):
        # Unauthenticated: the printer/agent identifies itself via its unique identifier.
        paper_status = (request.get_json(silent=True) or {}).get("paper_status")
        printer = PrinterService().heartbeat(identifier, paper_status)
        return success_response(printer.to_dict(), "Heartbeat received")
