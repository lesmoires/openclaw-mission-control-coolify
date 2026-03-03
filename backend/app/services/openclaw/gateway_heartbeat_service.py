"""Gateway-proxied heartbeat reporting for board agents.

Since OpenClaw board agents are configured but don't run as separate processes,
the gateway reports heartbeats on their behalf.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.core.logging import get_logger
from app.core.time import utcnow
from app.schemas.agents import AgentRead

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

    from app.models.agents import Agent

logger = get_logger(__name__)


class GatewayHeartbeatService:
    """Service for handling gateway-proxied agent heartbeats.

    Board agents in OpenClaw are configured (files written, config patched)
    but don't run as separate processes. The gateway reports their "liveness"
    to Mission Control on their behalf.
    """

    async def report_board_agent_heartbeat(
        self,
        session: AsyncSession,
        agent_id: UUID,
    ) -> AgentRead:
        """Record a heartbeat for a board agent reported by the gateway.

        This is called by the gateway to report that a board agent is "alive"
        based on the agent being configured and ready in the OpenClaw system.

        Args:
            session: Database session
            agent_id: UUID of the board agent

        Returns:
            Updated agent read model

        Raises:
            ValueError: If agent not found or is a gateway-main agent
        """
        from app.models.agents import Agent

        agent = await Agent.objects.by_id(agent_id).first(session)
        if agent is None:
            msg = f"Agent {agent_id} not found"
            raise ValueError(msg)

        # Only process board-scoped agents (not gateway-main)
        if agent.board_id is None:
            msg = "Use standard heartbeat endpoint for gateway-main agents"
            raise ValueError(msg)

        # Update heartbeat
        now = utcnow()
        agent.last_seen_at = now
        agent.updated_at = now

        # Transition from provisioning to online on first heartbeat
        if agent.status == "provisioning":
            agent.status = "online"
            logger.info(
                "agent.heartbeat.first_from_gateway agent_id=%s name=%s",
                agent.id,
                agent.name,
            )

        # Clear any provision errors since gateway is reporting success
        agent.last_provision_error = None
        agent.wake_attempts = 0
        agent.checkin_deadline_at = None

        session.add(agent)
        await session.commit()
        await session.refresh(agent)

        logger.debug(
            "agent.heartbeat.gateway_reported agent_id=%s name=%s status=%s",
            agent.id,
            agent.name,
            agent.status,
        )

        return AgentRead.model_validate(agent)

    async def report_multiple_board_agent_heartbeats(
        self,
        session: AsyncSession,
        agent_ids: list[UUID],
    ) -> list[AgentRead]:
        """Record heartbeats for multiple board agents.

        Called by the gateway to batch-report heartbeats for efficiency.

        Args:
            session: Database session
            agent_ids: List of board agent UUIDs

        Returns:
            List of updated agent read models
        """
        results: list[AgentRead] = []
        for agent_id in agent_ids:
            try:
                agent_read = await self.report_board_agent_heartbeat(session, agent_id)
                results.append(agent_read)
            except ValueError as e:
                logger.warning(
                    "agent.heartbeat.gateway_skip agent_id=%s error=%s",
                    agent_id,
                    str(e),
                )
                # Continue processing other agents even if one fails
                continue
        return results
