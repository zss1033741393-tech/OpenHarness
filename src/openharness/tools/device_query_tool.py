"""设备信息查询 Tool（Mock 实现，Phase 3 对接真实 API）."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from openharness.tools.base import BaseTool, ToolExecutionContext, ToolResult


class DeviceQueryInput(BaseModel):
    """Input for device_query tool."""

    user_id: str = Field(description="用户标识")
    query_type: str = Field(
        default="all",
        description="查询类型: model / version / status / topology / all",
    )


# Mock 设备数据（Phase 3 将对接真实 MCP Server）
MOCK_DEVICES: dict[str, dict[str, Any]] = {
    "USER_001": {
        "model": "HG8145X6",
        "version": "V5R020C10",
        "managed": True,
        "status": "online",
        "uptime_hours": 720,
        "topology": {
            "wan_type": "GPON",
            "wifi_bands": ["2.4GHz", "5GHz"],
            "connected_devices": 8,
            "mesh_enabled": False,
        },
        "capabilities": [
            "光衰检测", "WIFI信道诊断", "PPPoE连接诊断", "DNS解析诊断",
            "路由追踪诊断", "QoS策略自动调整", "WIFI频段自动切换",
            "信道自动优化", "带宽动态分配", "漫游优化", "网关自动重启",
        ],
    },
    "USER_002": {
        "model": "HG8245Q2",
        "version": "V3R017C10",
        "managed": True,
        "status": "online",
        "uptime_hours": 360,
        "topology": {
            "wan_type": "GPON",
            "wifi_bands": ["2.4GHz", "5GHz"],
            "connected_devices": 5,
            "mesh_enabled": False,
        },
        "capabilities": [
            "光衰检测", "WIFI信道诊断", "PPPoE连接诊断", "DNS解析诊断",
            "WIFI频段自动切换", "信道自动优化",
        ],
    },
}

DEFAULT_DEVICE: dict[str, Any] = {
    "model": "HG8145X6",
    "version": "V5R020C10",
    "managed": True,
    "status": "online",
    "uptime_hours": 0,
    "topology": {
        "wan_type": "GPON",
        "wifi_bands": ["2.4GHz", "5GHz"],
        "connected_devices": 1,
        "mesh_enabled": False,
    },
    "capabilities": [
        "光衰检测", "WIFI信道诊断", "PPPoE连接诊断", "DNS解析诊断",
        "路由追踪诊断", "QoS策略自动调整", "WIFI频段自动切换",
        "信道自动优化", "带宽动态分配", "漫游优化", "网关自动重启",
    ],
}


class DeviceQueryTool(BaseTool):
    """查询用户的设备信息（当前为 Mock 实现）."""

    name = "device_query"
    description = "查询用户的网关设备信息，包括型号、版本、纳管状态、网络拓扑等"
    input_model = DeviceQueryInput

    async def execute(
        self, arguments: DeviceQueryInput, context: ToolExecutionContext
    ) -> ToolResult:
        device = MOCK_DEVICES.get(arguments.user_id, DEFAULT_DEVICE)

        if arguments.query_type == "all":
            result = device
        elif arguments.query_type == "model":
            result = {"model": device["model"], "version": device["version"]}
        elif arguments.query_type == "version":
            result = {"version": device["version"]}
        elif arguments.query_type == "status":
            result = {"status": device["status"], "managed": device["managed"], "uptime_hours": device["uptime_hours"]}
        elif arguments.query_type == "topology":
            result = device.get("topology", {})
        else:
            return ToolResult(
                output=f"未知查询类型: {arguments.query_type}",
                is_error=True,
            )

        return ToolResult(output=json.dumps(result, ensure_ascii=False, indent=2))

    def is_read_only(self, arguments: BaseModel) -> bool:
        return True
