from core.metrics_calculator import BlobMetrics, TreeMetrics
from core.report_generator import ReportGenerator, ReportGenratorConfigShape
from pydantic import ClickHouseDsn

from .database import ClickHouseClient, CommitDataRow, MetricsDataRow


class ClickHouseReportGenratorConfigShape(ReportGenratorConfigShape):
    ch_dsn: ClickHouseDsn
    database: str = 'ucma'
    metrics_table: str = 'metrics'
    commits_table: str = 'commits'


class ClickHouseReportGenerator(
    ReportGenerator[ClickHouseReportGenratorConfigShape],
    config_shape=ClickHouseReportGenratorConfigShape,
):
    def process_blob(self, blob: BlobMetrics) -> list[MetricsDataRow]:
        return [
            MetricsDataRow(
                sha=self.sha,
                name=blob.name,
                path=blob.path,
                metric_name=result.metric_name,
                result_scope=result.result_scope,
                subject_path=result.subject_path,
                value=result.value,
                description=result.description,
                level=result.level,
            )
            for result in blob.metric_results
        ]

    def process_tree(self, tree: TreeMetrics) -> list[MetricsDataRow]:
        rows: list[MetricsDataRow] = []

        for result in tree.metric_results:
            rows.append(
                MetricsDataRow(**result.model_dump(), sha=self.sha, name=tree.name, path=tree.path)
            )

        for blob in tree.blobs:
            rows += self.process_blob(blob)

        for subtree in tree.trees:
            rows += self.process_tree(subtree)

        return rows

    async def generate(self) -> None:
        ch_client = ClickHouseClient(
            dsn=self.config.ch_dsn,
            database=self.config.database,
            commits_table=self.config.commits_table,
            metrics_table=self.config.metrics_table,
        )

        await ch_client.init()
        await ch_client.init_database()

        await ch_client.insert_commits(
            [
                CommitDataRow(
                    self.sha,
                    self.commit_meta.author_email,
                    self.commit_meta.committer_email,
                    self.commit_meta.authored_date,
                    self.commit_meta.committed_date,
                    self.commit_meta.message,
                )
            ]
        )

        await ch_client.insert_metrics(self.process_tree(self.tree_metrics))

        await ch_client.deinit()
