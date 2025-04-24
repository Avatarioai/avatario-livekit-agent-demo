from __future__ import annotations

import asyncio
from typing import AsyncIterable, Literal

import time
from livekit import rtc

from livekit.agents.pipeline.agent_playout import AgentPlayout
from livekit.agents import transcription, utils
from livekit.agents.pipeline.log import logger

EventTypes = Literal["playout_started", "playout_stopped"]


class CustomAgentPlayout(AgentPlayout):
    def __init__(
        self,
        avatario_client,
        *args, **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.avatario_client = avatario_client

    @utils.log_exceptions(logger=logger)
    async def _playout_task(
        self, old_task: asyncio.Task[None] | None, handle: PlayoutHandle
    ) -> None:

        if old_task is not None:
            await utils.aio.gracefully_cancel(old_task)

        if self._audio_source.queued_duration > 0:
            # this should not happen, but log it just in case
            logger.warning(
                "new playout while the source is still playing",
                extra={
                    "speech_id": handle.speech_id,
                    "queued_duration": self._audio_source.queued_duration,
                },
            )
        
        first_frame = True

        @utils.log_exceptions(logger=logger)
        async def _capture_task():
            nonlocal first_frame
            start_time = time.monotonic()
            async for frame in handle._playout_source:
                if first_frame:
                    handle._tr_fwd.segment_playout_started()

                    logger.debug(
                        "speech playout started",
                        extra={"speech_id": handle.speech_id},
                    )

                    self.emit("playout_started")
                    first_frame = False

                handle._pushed_duration += frame.samples_per_channel / frame.sample_rate
                self.avatario_client.send_audio(frame)
                
            time_taken = time.monotonic() - start_time
            if handle._pushed_duration > time_taken:
                sleep_time = handle._pushed_duration - time_taken
                logger.info(f"time left, sleeping for: {sleep_time}")
                await asyncio.sleep(sleep_time)
            else:
                logger.info(f"time taken is : {time_taken}, more than playout duration: {handle._pushed_duration}")

        capture_task = asyncio.create_task(_capture_task())
        try:
            await asyncio.wait(
                [capture_task, handle._int_fut],
                return_when=asyncio.FIRST_COMPLETED,
            )
        finally:
            await utils.aio.gracefully_cancel(capture_task)

            handle._total_played_time = (
                handle._pushed_duration - self._audio_source.queued_duration
            )

            if handle.interrupted or capture_task.exception():
                self._audio_source.clear_queue()  # make sure to remove any queued frames

            if not first_frame:
                if not handle.interrupted:
                    handle._tr_fwd.segment_playout_finished()

            await handle._tr_fwd.aclose()
            handle._done_fut.set_result(None)
            
            self.emit("playout_stopped", handle.interrupted)
            
            logger.debug(
                "speech playout finished",
                extra={
                    "speech_id": handle.speech_id,
                    "interrupted": handle.interrupted,
                },
            )
