# UCMA | ClickHouse Report Generator Plugin

Report generator plugin, which can be used to save the result of metrics calculation to a [ClickHouse](https://clickhouse.com) column-oriented database.

**Install**

``` bash
poetry add git+https://github.com/Universal-code-metrics-analyzer/clickhouse-report-generator@v0.1.0
```

You can use [docker-compose.yml](contrib/docker-compose.yml) to run development database

**Runner configuration**

``` yaml
# config.yml

report_generator:
  plugin: clickhouse_report_generator
  config:
    ch_dsn: clickhouse+asynch://admin:admin@127.0.0.1:9000/default
```

