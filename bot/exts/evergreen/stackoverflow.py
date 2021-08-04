import logging
from html import unescape
from urllib.parse import quote_plus
from sys import stdout
from discord import Embed, HTTPException
from discord.ext import commands

from bot import bot
from bot.constants import Colours, Emojis

logger = logging.getLogger(__name__)

BASE_URL = "https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=activity&" \
           "tagged={tags}&site=stackoverflow&q={query}"
SEARCH_URL = "https://stackoverflow.com/search?q={query}"
ERR_EMBED = Embed(
    title="Error in fetching results from Stackoverflow",
    description=(
        "Sorry, there was en error while trying to fetch data from the Stackoverflow website. Please try again in some "
        "time. If this issue persists, please contact the staff or send a message in #dev-contrib."
    ),
    color=Colours.soft_red
)


class Stackoverflow(commands.Cog):
    """Contains command to interact with stackoverflow from discord."""

    def __init__(self, bot: bot.Bot):
        self.bot = bot

    @commands.command(aliases=["so"])
    @commands.cooldown(1, 15, commands.cooldowns.BucketType.user)
    async def stackoverflow(self, ctx: commands.Context, search_query: str, *, tag: str = '') -> None:
        """Sends the top 5 results of a search query from stackoverflow."""
        if ',' in tag:
            tag = tag.split(',') if ', ' not in tag else tag.split(', ')
        elif tag != '':
            tag = [tag]
        encoded_search_query = quote_plus(search_query)
        encoded_tag_query = quote_plus(';'.join(tag))

        async with self.bot.http_session.get(BASE_URL.format(query=encoded_search_query,
                                                             tags=encoded_tag_query)) as response:
            if response.status == 200:
                data = await response.json()
            else:
                logger.error(f'Status code is not 200, it is {response.status}')
                await ctx.send(embed=ERR_EMBED)
                return
        if not data['items']:
            no_search_result = Embed(
                title=f"No search results found for {search_query}",
                color=Colours.soft_red
            )
            if tag:
                no_search_result.description = f"A search result couldn't be found with " \
                                               f"the following tags added: {', '.join(tag)}"
            await ctx.send(embed=no_search_result)
            return

        top5 = data["items"][:5]
        embed = Embed(
            title="Search results - Stackoverflow",
            url=SEARCH_URL.format(query=encoded_search_query),
            description=f"Here are the top {len(top5)} results:",
            color=Colours.orange
        )
        for item in top5:
            embed.add_field(
                name=unescape(item['title']),
                value=(
                    f"[{Emojis.reddit_upvote} {item['score']}    "
                    f"{Emojis.stackoverflow_views} {item['view_count']}     "
                    f"{Emojis.reddit_comments} {item['answer_count']}   "
                    f"{Emojis.stackoverflow_tag} {', '.join(item['tags'][:3])}]"
                    f"({item['link']})"
                ),
                inline=False)
        embed.set_footer(text="View the original link for more results.")
        try:
            await ctx.send(embed=embed)
        except HTTPException:
            search_query_too_long = Embed(
                title="Your search query is too long, please try shortening your search query",
                color=Colours.soft_red
            )
            await ctx.send(embed=search_query_too_long)


def setup(bot: bot.Bot) -> None:
    """Load the Stackoverflow Cog."""
    bot.add_cog(Stackoverflow(bot))
