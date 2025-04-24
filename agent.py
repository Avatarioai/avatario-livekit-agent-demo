import os
import logging, asyncio
import multiprocessing
import requests, datetime, time
import threading
import numpy as np

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.plugins import deepgram, openai, silero

from agent_pipeline.custom_pipeline_agent import CustomPipelineAgent
from livekit import rtc

load_dotenv()
logger = logging.getLogger("openai_assistant")

import datetime
from datetime import timezone

from avatario_python_sdk import Avatario

async def entrypoint(ctx: JobContext):
    """This example demonstrates a VoicePipelineAgent that uses OpenAI's Assistant API as the LLM"""
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
        ),
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()

    avatario_client = Avatario(
        api_key=os.environ.get("AVATARIO_API_KEY"),
        room_name=ctx.job.metadata,
    )
    avatario_client.initialize()

    agent = CustomPipelineAgent(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
        avatario_client=avatario_client,
    )
    agent.start(ctx.room, participant)


    @agent.on("agent_stopped_speaking")
    def call_interrupt(interruption: bool):
        if interruption:
            avatario_client.interrupt()

    @agent.on("agent_started_speaking")
    def call_resume():
        avatario_client.resume()

    ctx.add_shutdown_callback(avatario_client.close)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="test-agent"))
