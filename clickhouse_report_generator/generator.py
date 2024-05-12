from pathlib import Path

from core.report_generator import ReportGenerator, ReportGenratorConfigShape


class ClickHouseReportGenratorConfigShape(ReportGenratorConfigShape):
    output_dir: Path


class ClickHouseReportGenerator(
    ReportGenerator[ClickHouseReportGenratorConfigShape],
    config_shape=ClickHouseReportGenratorConfigShape,
):
    async def generate(self) -> None:
        pass
