"""网络 KPI 查询 Tool（Mock 实现，Phase 3 对接真实 API）."""

from __future__ import annotations

import json
import random
from typing import Any

from pydantic import BaseModel, Field

from openharness.tools.base import BaseTool, ToolExecutionContext, ToolResult


class KpiQueryInput(BaseModel):
    """Input for kpi_query tool."""

    user_id: str = Field(description="用户标识")
    metric_type: str = Field(
        default="all",
        description="指标类型: cei / bandwidth / latency / packet_loss / jitter / all",
    )
    time_range: str = Field(
        default="1h",
        description="时间范围: 1h / 6h / 24h / 7d",
    )


# Mock KPI data
MOCK_KPI: dict[str, dict[str, Any]] = {
    "USER_001": {
        "cei": {"current": 72, "avg_24h": 75, "min_24h": 58, "max_24h": 92, "trend": "declining"},
        "bandwidth": {"downlink_mbps": 95.2, "uplink_mbps": 28.5, "subscribed_downlink": 100, "subscribed_uplink": 30},
        "latency": {"rtt_ms": 12.5, "avg_24h": 15.3, "p95_24h": 28.0},
        "packet_loss": {"current_pct": 0.02, "avg_24h": 0.05, "max_24h": 0.8},
        "jitter": {"current_ms": 3.2, "avg_24h": 4.5, "max_24h": 15.0},
    },
    "USER_002": {
        "cei": {"current": 85, "avg_24h": 88, "min_24h": 75, "max_24h": 95, "trend": "stable"},
        "bandwidth": {"downlink_mbps": 48.5, "uplink_mbps": 9.8, "subscribed_downlink": 50, "subscribed_uplink": 10},
        "latency": {"rtt_ms": 8.0, "avg_24h": 9.5, "p95_24h": 18.0},
        "packet_loss": {"current_pct": 0.01, "avg_24h": 0.02, "max_24h": 0.3},
        "jitter": {"current_ms": 2.0, "avg_24h": 2.8, "max_24h": 8.0},
    },
}

DEFAULT_KPI: dict[str, Any] = {
    "cei": {"current": 80, "avg_24h": 82, "min_24h": 70, "max_24h": 95, "trend": "stable"},
    "bandwidth": {"downlink_mbps": 50.0, "uplink_mbps": 10.0, "subscribed_downlink": 100, "subscribed_uplink": 30},
    "latency": {"rtt_ms": 10.0, "avg_24h": 12.0, "p95_24h": 25.0},
    "packet_loss": {"current_pct": 0.01, "avg_24h": 0.03, "max_24h": 0.5},
    "jitter": {"current_ms": 2.5, "avg_24h": 3.0, "max_24h": 10.0},
}


class KpiQueryTool(BaseTool):
    """查询用户的网络 KPI 指标（当前为 Mock 实现）."""

    name = "kpi_query"
    description = "查询用户的网络KPI指标，包括CEI评分、带宽、延迟、丢包率、抖动等"
    input_model = KpiQueryInput

    async def execute(
        self, arguments: KpiQueryInput, context: ToolExecutionContext
    ) -> ToolResult:
        kpi = MOCK_KPI.get(arguments.user_id, DEFAULT_KPI)

        if arguments.metric_type == "all":
            result = kpi
        elif arguments.metric_type in kpi:
            result = {arguments.metric_type: kpi[arguments.metric_type]}
        else:
            return ToolResult(
                output=f"未知指标类型: {arguments.metric_type}，可用类型: {list(kpi.keys()) + ['all']}",
                is_error=True,
            )

        result_with_meta = {
            "user_id": arguments.user_id,
            "time_range": arguments.time_range,
            "query_time": "mock",
            "data": result,
        }

        return ToolResult(output=json.dumps(result_with_meta, ensure_ascii=False, indent=2))

    def is_read_only(self, arguments: BaseModel) -> bool:
        return True
