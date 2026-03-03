"""Background heartbeat reporter for board agents.

This service runs as a background task (via RQ or cron) to periodically
report heartbeats for configured board agents to Mission Control.

Since OpenClaw board agents are configured but don't run as separate
processes, this reporter queries the gateway for configured agents
and reports their "liveness" to Mission Control on their behalf.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.core.logging import get_logger
from app.core.time import utcnow
from app.db.session import async_session_maker
from app.services.openclaw.gateway_heartbeat_service import GatewayHeartbeatService
from app.services.openclaw.gateway_resolver import gateway_client_config
from app.services.openclaw.gateway_rpc import openclaw_call
from app.services.openclaw.shared import GatewayAgentIdentity

if TYPE_CHECKING:
    from app.models.agents import Agent
    from app.models.gateways import Gateway

logger = get_logger(__name__)


class GatewayHeartbeatReporter:
    """Reports heartbeats for configured board agents via the gateway."""

    def __init__(self) -> None:
        self._shutdown = False

    async def report_heartbeats_for_gateway(
        self,
        gateway: Gateway,
    ) -> dict[str, Any]:
        """Report heartbeats for all configured board agents on a gateway.

        Args:
            gateway: The gateway to report heartbeats for

        Returns:
            Dict with report statistics
        """
        if not gateway.url:
            logger.warning("gateway.no_url gateway_id=%s", gateway.id)
            return {"success": False, "error": "Gateway URL not configured"}

        config = gateway_client_config(gateway)
        reported: list[UUID] = []
        failed: list[dict[str, Any]] = []

        try:
            # Get list of configured agents from gateway
            agents_list = await self._get_gateway_agents(config)

            async with async_session_maker() as session:
                for agent_data in agents_list:
                    agent_id = await self._resolve_agent_id(agent_data, gateway)
                    if not agent_id:
                        continue

                    try:
                        service = GatewayHeartbeatService()
                        await service.report_board_agent_heartbeat(session, agent_id)
                        reported.append(agent_id)
                        logger.debug(
                            "heartbeat.reported agent_id=%s gateway_id=%s",
                            agent_id,
                            gateway.id,
                        )
                    except ValueError as e:
                        failed.append({"agent_id": str(agent_id), "error": str(e)})
                        logger.warning(
                            "heartbeat.failed agent_id=%s error=%s",
                            agent_id,
                            str(e),
                        )

            return {
                "success": True,
                "gateway_id": str(gateway.id),
                "reported_count": len(reported),
                "failed_count": len(failed),
                "reported": [str(a) for a in reported],
                "failed": failed,
            }

        except Exception as e:
            logger.error(
                "heartbeat.gateway_error gateway_id=%s error=%s",
                gateway.id,
                str(e),
                exc_info=True,
            )
            return {"success": False, "error": str(e)}

    async def _get_gateway_agents(self, config: Any) -> list[dict[str, Any]]:
        """Get list of configured agents from the gateway.

        Args:
            config: Gateway client configuration

        Returns:
            List of agent data from gateway
        """
        try:
            result = await openclaw_call("agents.list", {}, config=config)
            if isinstance(result, dict) and "agents" in result:
                return result["agents"]
            if isinstance(result, list):
                return result
            return []
        except Exception as e:
            logger.error("gateway.agents_list_failed error=%s", str(e))
            return []

    async def _resolve_agent_id(
        self,
        agent_data: dict[str, Any],
        gateway: Gateway,
    ) -> UUID | None:
        """Resolve gateway agent data to Mission Control agent ID.

        Args:
            agent_data: Agent data from gateway
            gateway: The gateway the agent belongs to

        Returns:
            UUID of the agent in Mission Control, or None if not found
        """
        from app.models.agents import Agent
        from sqlalchemy import select
        from sqlmodel import col

        # Get agent identifier from gateway data
        agent_key = agent_data.get("id") or agent_data.get("name")
        if not agent_key:
            return None

        # Skip gateway-main agent
        main_agent_id = GatewayAgentIdentity.openclaw_agent_id(gateway)
        if agent_key == main_agent_id:
            return None

        async with async_session_maker() as session:
            # Find agent by session key (which matches gateway agent id)
            result = await session.exec(
                select(Agent).where(
                    (Agent.gateway_id == gateway.id)
                    & (Agent.openclaw_session_id.contains(agent_key))
                )
            )
            agent = result.first()
            if agent:
                return agent.id

            # Fallback: find by name on this gateway's boards
            result = await session.exec(
                select(Agent).where(
                    (Agent.gateway_id == gateway.id)
                    & (Agent.board_id.isnot(None))
                    & (col(Agent.name) == agent_data.get("name"))
                )
            )
            agent = result.first()
            if agent:
                return agent.id

        return None

    async def run_once(self) -> dict[str, Any]:
        """Run heartbeat reporting once for all gateways.

        Returns:
            Dict with statistics for all gateways
        """
        from app.models.gateways import Gateway
        from sqlalchemy import select

        async with async_session_maker() as session:
            result = await session.execute(select(Gateway))
            gateways = result.scalars().all()

        results = []
        for gateway in gateways:
            gateway_result = await self.report_heartbeats_for_gateway(gateway)
            results.append({
                "gateway_id": str(gateway.id),
                **gateway_result,
            })

        total_reported = sum(r.get("reported_count", 0) for r in results)
        total_failed = sum(r.get("failed_count", 0) for r in results)

        logger.info(
            "heartbeat.run_complete gateways=%s reported=%s failed=%s",
            len(results),
            total_reported,
            total_failed,
        )

        return {
            "timestamp": utcnow().isoformat(),
            "gateways": results,
            "total_reported": total_reported,
            "total_failed": total_failed,
        }

    async def run_continuously(
        self,
        interval_seconds: float = 30.0,
    ) -> None:
        """Run heartbeat reporting continuously.

        Args:
            interval_seconds: How often to report heartbeats (default 30s)
        """
        logger.info(
            "heartbeat.continuous_start interval=%ss",
            interval_seconds,
        )

        while not self._shutdown:
            try:
                await self.run_once()
            except Exception as e:
                logger.error("heartbeat.run_error error=%s", str(e), exc_info=True)

            # Wait for next iteration
            await asyncio.sleep(interval_seconds)

    def shutdown(self) -> None:
        """Signal the reporter to shut down."""
        self._shutdown = True
        logger.info("heartbeat.shutdown_requested")


async def run_heartbeat_reporter() -> None:
    """Entry point for running the heartbeat reporter.

    This can be called from:
    - RQ scheduled job (cron)
    - Background task
    - CLI command
    """
    reporter = GatewayHeartbeatReporter()
    result = await reporter.run_once()
    return result
