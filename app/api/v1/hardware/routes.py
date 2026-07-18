"""Hardware device endpoints: barcode scanners, printers, cash drawers, customer displays."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response, error_response
from app.schemas.device_schema import DeviceCreateSchema, DeviceUpdateSchema
from app.services.hardware_service import HardwareService

blp = Blueprint("hardware", __name__, url_prefix="/api/v1/hardware", description="Hardware device management")


@blp.route("/devices")
class DevicesListResource(MethodView):
    @jwt_required()
    def get(self):
        device_type = request.args.get("device_type")
        devices = HardwareService().list_devices(device_type)
        return success_response([d.to_dict() for d in devices])

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(DeviceCreateSchema)
    def post(self, data):
        device = HardwareService().register_device(current_user_id(), **data)
        return success_response(device.to_dict(), "Device registered", 201)


@blp.route("/devices/<int:device_id>")
class DeviceDetailResource(MethodView):
    @jwt_required()
    def get(self, device_id):
        device = HardwareService().get_device(device_id)
        return success_response(device.to_dict())

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(DeviceUpdateSchema)
    def patch(self, data, device_id):
        device = HardwareService().update_device(current_user_id(), device_id, **data)
        return success_response(device.to_dict(), "Device updated")

    @jwt_required()
    @permission_required("settings.manage")
    def delete(self, device_id):
        HardwareService().deregister_device(current_user_id(), device_id)
        return success_response(None, "Device deregistered")


@blp.route("/devices/heartbeat/<string:identifier>")
class DeviceHeartbeatResource(MethodView):
    @blp.doc(security=[])
    def post(self, identifier):
        # Deliberately unauthenticated: physical devices ping this endpoint using
        # their unique identifier/token as the credential rather than a user JWT.
        device = HardwareService().heartbeat(identifier)
        return success_response(device.to_dict(), "Heartbeat received")


@blp.route("/devices/<int:device_id>/open-drawer")
class OpenCashDrawerResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    def post(self, device_id):
        result = HardwareService().open_cash_drawer(device_id)
        return success_response(result, "Open command sent")
