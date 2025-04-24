import asyncio
import time

from livekit import rtc
from livekit.agents.pipeline.log import logger
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents.pipeline.agent_output import AgentOutput
from agent_pipeline.custom_agent_playout import CustomAgentPlayout
from livekit.agents import utils


class CustomPipelineAgent(VoicePipelineAgent):
    def __init__(self,
            avatario_client,
            *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.avatario_client = avatario_client
        

    @utils.log_exceptions(logger=logger)
    async def _main_task(self) -> None:
        if self._opts.plotting:
            await self._plotter.start()

        self._update_state("initializing")
        audio_source = rtc.AudioSource(self._tts.sample_rate, self._tts.num_channels)        
        track = rtc.LocalAudioTrack.create_audio_track("assistant_voice", audio_source)
        self._agent_publication = await self._room.local_participant.publish_track(
            track, rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        )

        agent_playout = CustomAgentPlayout(
            audio_source=audio_source,
            avatario_client=self.avatario_client
        )
        
        self._agent_output = AgentOutput(
            room=self._room,
            agent_playout=agent_playout,
            llm=self._llm,
            tts=self._tts,
        )

        def _on_playout_started() -> None:
            self._plotter.plot_event("agent_started_speaking")
            self.emit("agent_started_speaking")
            self._update_state("speaking")

        def _on_playout_stopped(interrupted: bool) -> None:
            self._plotter.plot_event("agent_stopped_speaking")
            self.emit("agent_stopped_speaking", interrupted)
            self._update_state("listening")


        agent_playout.on("playout_started", _on_playout_started)
        agent_playout.on("playout_stopped", _on_playout_stopped)

        self._track_published_fut.set_result(None)
        while True:
            await self._speech_q_changed.wait()
            
            while self._speech_q:
                speech = self._speech_q[0]
                self._playing_speech = speech
                await self._play_speech(speech)
                self._speech_q.pop(0)  # Remove the element only after playing
                self._playing_speech = None

            self._speech_q_changed.clear()
