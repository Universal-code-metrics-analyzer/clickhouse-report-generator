from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, NamedTuple, cast

from asynch import connect
from asynch.connection import Connection
from asynch.cursors import DictCursor
from pydantic import ClickHouseDsn


class CommitDataRow(NamedTuple):
    sha: str
    author_email: str
    committer_email: str
    authored_date: datetime
    committed_date: datetime
    message: str


class MetricsDataRow(NamedTuple):
    sha: str
    name: str
    path: str
    metric_name: str
    result_scope: str
    subject_path: str
    value: float
    description: str | None


class ClickHouseClient:
    conn: Connection | None

    def __init__(
        self, dsn: ClickHouseDsn, database: str, metrics_table: str, commits_table: str
    ) -> None:
        self.conn = None
        self.dsn = dsn
        self.database = database
        self.metrics_table = metrics_table
        self.commits_table = commits_table

    async def init(self):
        self.conn = await connect(
            host=self.dsn.host,
            port=self.dsn.port,
            database=self.dsn.path,
            user=self.dsn.username,
            password=self.dsn.password,
        )

    async def deinit(self):
        if not self.conn:
            raise Exception('ClickHouseClient not initialized')

        await self.conn.close()

    @asynccontextmanager
    async def cursor_context(self) -> AsyncGenerator[DictCursor, None]:
        if not self.conn:
            raise Exception('ClickHouseClient not initialized')

        async with self.conn.cursor(cursor=DictCursor) as cursor:
            yield cast(DictCursor, cursor)

    async def init_database(self):
        async with self.cursor_context() as cursor:
            await cursor.execute(f'create database if not exists {self.database}')

            await cursor.execute(
                (
                    f"create table if not exists {self.database}.{self.commits_table} ("
                    + "sha String,"
                    + "author_email String,"
                    + "committer_email String,"
                    + "authored_date DateTime('Europe/Moscow'),"
                    + "committed_date DateTime('Europe/Moscow'),"
                    + "message String"
                    + ") ENGINE MergeTree order by committed_date"
                )
            )

            await cursor.execute(
                (
                    f"create table if not exists {self.database}.{self.metrics_table} ("
                    + "sha String,"
                    + "name String,"
                    + "path String,"
                    + "metric_name String,"
                    + "result_scope String,"
                    + "subject_path String,"
                    + "value Float64,"
                    + "description Nullable(String)"
                    + ") ENGINE MergeTree order by path"
                )
            )

    async def insert_commits(self, rows: list[CommitDataRow]):
        async with self.cursor_context() as cursor:
            await cursor.execute(f'insert into {self.database}.{self.commits_table} values', rows)

    async def insert_metrics(self, rows: list[MetricsDataRow]):
        async with self.cursor_context() as cursor:
            await cursor.execute(f'insert into {self.database}.{self.metrics_table} values', rows)
