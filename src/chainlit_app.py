"""Chainlit chat interface for the Agentic RAG system."""

import chainlit as cl

from src.agent import create_agent, log_interaction


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="What documents are available?",
            message="What documents do you have access to? Give me a summary of the available content.",
        ),
        cl.Starter(
            label="Search the knowledge base",
            message="Search the knowledge base and tell me what topics are covered.",
        ),
    ]


@cl.on_chat_start
async def on_chat_start():
    """Initialize the Agno agent when a new chat session starts."""
    try:
        agent = create_agent(session_id=cl.context.session.id)
    except ValueError as e:
        await cl.Message(content=f"Configuration error: {str(e)}").send()
        return

    cl.user_session.set("agent", agent)

    await cl.Message(
        content=(
            "Hello! I'm your Agentic RAG assistant.\n\n"
            "I can search through your documents and answer questions "
            "based on their content. Just ask me anything!"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages — run the agent and log the interaction."""
    agent = cl.user_session.get("agent")

    if agent is None:
        await cl.Message(
            content="Agent not initialized. Please refresh the page."
        ).send()
        return

    msg = cl.Message(content="")
    await msg.send()

    try:
        response = await agent.arun(message.content, stream=False)

        if hasattr(response, "content") and response.content:
            msg.content = response.content
            log_interaction(
                cl.context.session.id, message.content, response.content
            )
        elif hasattr(response, "content"):
            msg.content = "I couldn't find any relevant information for your query."
        else:
            msg.content = str(response) if response else "No response received."

    except Exception as e:
        msg.content = f"An error occurred: {str(e)}"

    await msg.update()


@cl.on_chat_end
async def on_chat_end():
    """Cleanup when the chat session ends."""
    pass