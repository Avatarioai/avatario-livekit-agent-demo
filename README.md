# Avatario LiveKit Agent Demo

This repository demonstrates how to integrate [LiveKit agents](https://github.com/livekit/agents) with the [Avatario Python SDK](https://github.com/Avatarioai/avatario-python-sdk) to enable video-based conversational agents. With this setup, you can connect a LiveKit voice agent to Avatario’s backend, allowing for real-time, lip-synced video avatar responses.

---

## How It Works

- The core logic resides in `agent.py`, which initializes the Avatario Python SDK and sets up the integration pipeline.
- Inside the `agent_pipeline` folder:
  - **`custom_agent_pipeline.py`**: CustomPipelineAgent Initializes and configures the LiveKit agent. This file is modified to use `avatario_client` as input, channeling the Avatario client into the agent’s audio playout.
  - **`custom_agent_playout.py`**: Relays TTS-generated audio frames to the Avatario backend and manages video agent interruption and resume based on microphone input.
---

## Usage

**Install dependencies:**
```
pip install -r requirements.txt
```

**Run Agent:**
```
python3 agent.py start
```


**Customization:**
- Reference and modify the `entrypoint` function in `agent.py` as needed.
- Customize the elements in `agent_pipeline/custom_agent_pipeline.py`  and `agent_pipeline/custom_agent_playout.py`to fit your use case.
---

## Demo

Check out the [demo page](https://app.onezot.work/dashboard/zxlb3t5j/demo) to see this integration in action.

---

For questions or support, please open an issue or contact the Avatario team at support@avatario.com

