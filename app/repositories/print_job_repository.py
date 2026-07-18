from app.models.print_job import PrintJob
from app.repositories.base_repository import BaseRepository


class PrintJobRepository(BaseRepository):
    model = PrintJob

    def get_for_printer(self, printer_id):
        return PrintJob.query.filter_by(printer_id=printer_id).order_by(PrintJob.created_at.desc())
