import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

import discord
import httpx
from bs4 import BeautifulSoup
from discord import app_commands
from openai import AsyncOpenAI

DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_GUILD_ID = int(os.environ["DISCORD_GUILD_ID"])
GUIDE_CHANNEL_ID = int(os.environ["DISCORD_GUIDE_CHANNEL_ID"])
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()


class PluginDocBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=DISCORD_GUILD_ID)

        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        print("Slash commands synced.")


client = PluginDocBot()


def get_plugin_name(url: str) -> str:
    """Get a readable plugin name from the Modrinth URL."""

    path = urlparse(url).path.strip("/")

    if not path:
        return "Minecraft Plugin"

    slug = path.split("/")[-1]

    # Convert common URL formats into a readable name.
    name = slug.replace("-", " ").replace("_", " ")

    return name.title()


async def fetch_page(url: str) -> str:
    """Download and extract readable text from the plugin page."""

    headers = {
        "User-Agent": "Melonville-Plugin-Docs/1.0"
    }

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30
    ) as http:

        response = await http.get(url, headers=headers)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove things that aren't useful documentation.
    for element in soup([
        "script",
        "style",
        "noscript",
        "svg"
    ]):
        element.decompose()

    text = soup.get_text("\n")

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return "\n".join(lines)


async def generate_guide(plugin_name: str, url: str, documentation: str) -> str:
    """Ask OpenAI to turn the plugin documentation into a player guide."""

    prompt = f"""
You are creating a Minecraft plugin guide for players on a private SMP server.

Plugin:
{plugin_name}

Modrinth page:
{url}

Below is information retrieved from the plugin's Modrinth page.

--- DOCUMENTATION START ---
{documentation}
--- DOCUMENTATION END ---

Create a clear, practical player-facing guide.

Important rules:

1. Only describe commands, permissions, features, and behavior that are supported by the supplied documentation.
2. Do not invent commands.
3. Do not invent permissions.
4. Do not invent configuration options.
5. If something is unclear from the documentation, say that it is unclear rather than guessing.
6. Focus on what normal players need to know.
7. Do not include administrator/server-owner setup instructions unless they are necessary for players to understand the plugin.
8. Include command examples when the documentation provides them.
9. Explain what each command does.
10. Include useful tips when supported by the documentation.
11. Use Discord-friendly Markdown.
12. Keep the guide reasonably concise.

Use this structure when applicable:

# {plugin_name}

## What It Does

Brief explanation.

## How To Use It

Step-by-step instructions.

## Commands

List useful player commands and explain each one.

## Tips

Useful player tips.

## Important Notes

Anything players should know.

Do not claim anything that isn't supported by the supplied documentation.
"""

    response = await openai_client.responses.create(
        model="gpt-5",
        input=prompt
    )

    return response.output_text.strip()


def split_for_discord(text: str, max_length: int = 1900):
    """Split text into chunks small enough for Discord messages."""

    chunks = []

    while len(text) > max_length:
        split_at = text.rfind("\n", 0, max_length)

        if split_at == -1:
            split_at = max_length

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    if text:
        chunks.append(text)

    return chunks


@client.tree.command(
    name="plugin",
    description="Create player instructions for a Minecraft plugin."
)
@app_commands.describe(
    url="The Modrinth plugin page URL"
)
async def plugin(interaction: discord.Interaction, url: str):

    if not url.startswith("https://modrinth.com/"):
        await interaction.response.send_message(
            "Please provide a Modrinth plugin URL.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        print(f"Processing plugin: {url}")

        # Get plugin name.
        plugin_name = get_plugin_name(url)

        print(f"Plugin name: {plugin_name}")

        # Fetch documentation.
        documentation = await fetch_page(url)

        print(f"Downloaded {len(documentation)} characters.")

        # Prevent an enormous webpage from being sent to the AI.
        if len(documentation) > 30000:
            documentation = documentation[:30000]

        # Generate guide.
        guide = await generate_guide(
            plugin_name,
            url,
            documentation
        )

        print(f"Generated guide: {len(guide)} characters.")

        # Find Discord channel.
        channel = client.get_channel(GUIDE_CHANNEL_ID)

        if channel is None:
            raise RuntimeError(
                "Could not find the configured Discord guide channel."
            )

        # Make sure this really is a Forum channel.
        if not isinstance(channel, discord.ForumChannel):
            raise RuntimeError(
                f"Configured channel is not a Forum channel. "
                f"Channel type: {type(channel).__name__}"
            )

        # Split guide into Discord-sized messages.
        chunks = split_for_discord(guide)

        # Add source information to the first post.
        first_chunk = (
            f"{chunks[0]}\n\n"
            f"---\n"
            f"📖 **Source:** {url}"
        )

        # Discord forum post titles have a length limit.
        thread_name = f"📚 {plugin_name}"

        if len(thread_name) > 100:
            thread_name = thread_name[:100]

        print(f"Creating forum post: {thread_name}")

        # Create the Forum post.
        thread, message = await channel.create_thread(
            name=thread_name,
            content=first_chunk
        )

        print(f"Forum post created: {thread.id}")

        # Send remaining sections into the forum post.
        for chunk in chunks[1:]:
            await thread.send(chunk)

        await interaction.followup.send(
            f"✅ Plugin guide created: {thread.mention}"
        )

    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")

        await interaction.followup.send(
            "❌ I couldn't create the guide. "
            "Check the bot logs for details."
        )


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    print(f"Bot ID: {client.user.id}")


client.run(DISCORD_TOKEN)
