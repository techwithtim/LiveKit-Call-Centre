from __future__ import annotations

import logging
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai
from dotenv import load_dotenv
from api import AssistantFnc
from prompts import INSTRUCTIONS, LOOKUP_VIN_MESSAGE, WELCOME_MESSAGE
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


logger = logging.getLogger("myagent")
logger.setLevel(logging.INFO)

async def entrypoint(ctx: JobContext):
    logger.info("starting entrypoint")

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)

    await ctx.wait_for_participant()

    model = openai.realtime.RealtimeModel(
        instructions=INSTRUCTIONS,
        voice="shimmer",
        temperature=0.8,
        modalities=["audio", "text"],
    )
    assistant_fnc = AssistantFnc()
    assistant = MultimodalAgent(model=model, fnc_ctx=assistant_fnc)
    assistant.start(ctx.room)

    session = model.sessions[0]
    session.conversation.item.create(
      llm.ChatMessage(
        role="assistant",
        content=WELCOME_MESSAGE,
      )
    )
    session.response.create()

    @session.on("user_speech_committed")
    def on_user_speech_committed(msg: llm.ChatMessage):
        # convert string lists to strings, drop images
        if isinstance(msg.content, list):
            msg.content = "\n".join(
                "[image]" if isinstance(x, llm.ChatImage) else x for x in msg
            )

        if assistant_fnc.has_car():
            handle_query(msg)
        else:
            find_profile(msg)

    def find_profile(msg: str):
        session.conversation.item.create(
        llm.ChatMessage(
            role="system",
            content=LOOKUP_VIN_MESSAGE(msg),
            )
        )
        session.response.create()

    def handle_query(msg: str):
        session.conversation.item.create(
        llm.ChatMessage(
            role="user",
            content=msg.content,
            )
        )
        session.response.create()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))