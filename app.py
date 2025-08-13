import streamlit as st
import logging
from uuid import uuid4
import asyncio
import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest

BASE_URL = "http://localhost:10000"

async def send_currency_query(query: str):
    """Fetch agent card and send query in one async client session."""
    async with httpx.AsyncClient() as httpx_client:
        # Resolve agent card
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=BASE_URL)
        agent_card: AgentCard = await resolver.get_agent_card()

        # Create client and send message
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        send_message_payload = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": query}],
                "message_id": uuid4().hex,
            }
        }
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload)
        )

        response = await client.send_message(request)
        return response.model_dump(mode="json", exclude_none=True)

# --- Streamlit UI ---
st.set_page_config(page_title="💱 Currency Conversion Agent", layout="centered")
st.title("💱 Currency Conversion Agent")

currency_from = st.text_input("From Currency", "USD")
currency_to = st.text_input("To Currency", "EUR")
amount = st.number_input("Amount", value=1.0, min_value=0.0)

if st.button("Convert"):
    query = f"What is the exchange rate from {amount} {currency_from} to {currency_to}?"
    with st.spinner("Querying Currency Agent..."):
        try:
            raw_result = asyncio.run(send_currency_query(query))
            # Extract only the text from the first artifact
            artifacts = raw_result.get("result", {}).get("artifacts", [])
            if artifacts and "parts" in artifacts[0] and artifacts[0]["parts"]:
                conversion_text = artifacts[0]["parts"][0]["text"]
                st.success(conversion_text)
            else:
                st.warning("No conversion result found in response.")
        except Exception as e:
            st.error(f"Error communicating with backend: {e}")
