import discord
import logging
from modals_and_views import SelectChallengeView, TestSelectChallengeView, ModifyUserFieldView
from botExternals import Connections
from pagination_and_embeds import genPaginStuff, fileListAssembler

# Configure logging
logging.basicConfig(filename='bot.log',level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

conn = Connections()
bot = discord.Bot()

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")

# Command opens test challenges
@bot.command(description="Test the bot")
async def test(ctx):
    logging.info("Test command invoked")
    activeChallenges = (conn.challenges.find({"Testactive": True})).sort("points", 1)
    if activeChallenges is None:
        await ctx.response.send_message("No active challenges", ephemeral=True)
        logging.info("No active challenges found for test")
        return

    embeds, Images, views = genPaginStuff(activeChallenges, conn, test=True)
    await ctx.response.send_message(embed=embeds[0], view=views[0], files=fileListAssembler(Images[0]), ephemeral=True)


@bot.command(description="Start the bot")
async def start(ctx):
    logging.info("Start command invoked")
    activeChallenges = (conn.challenges.find({"active": True})).sort("points", 1)
    if activeChallenges is None:
        await ctx.response.send_message("No active challenges", ephemeral=True)
        logging.info("No active challenges found for start")
        return

    embeds, Images, views = genPaginStuff(activeChallenges, conn)
    await ctx.response.send_message(embed=embeds[0], view=views[0], files=fileListAssembler(Images[0]), ephemeral=True)

# Command to show challenge standings
@bot.command(description="Show the current Standings")
async def standings(ctx):
    logging.info("Standings command invoked")
    embed = discord.Embed(title="Standings", color=0x00ff00)
    top5 = conn.users.find().sort([("points", -1), ("attempts", 1)]).limit(5)

    user = conn.users.find_one({"user_id": ctx.author.id})
    if user is None:
        user = {"user_id": ctx.author.id, "points": 0, "solves": [], "attempts": 0}
        conn.mongo.users.insert_one(user)

    leaderboard = ""
    top_5_ids = []
    for i, person in enumerate(top5):
        member = ctx.guild.get_member(person['user_id']) or await ctx.guild.fetch_member(person['user_id'])
        name = member.name if member else "Unknown"
        leaderboard += f"{i+1}. {name} - {person['points']} points\n"
        top_5_ids.append(person['user_id'])

    embed.add_field(name="Leaderboard", value=leaderboard, inline=False)
    if ctx.author.id not in top_5_ids:
        member = ctx.guild.get_member(ctx.author.id) or await ctx.guild.fetch_member(ctx.author.id)
        name = member.name if member else "Unknown"
        
        userplace = f"{name} - {user['points']} points"
        embed.add_field(name="Your Current Placement", value=userplace, inline=True)
    await ctx.response.send_message(embed=embed, ephemeral=True)

# Changes current active challenges
@bot.command(description="Change which challenges are active")
async def changeactive(ctx):
    logging.info("Change active challenges command invoked")
    global challenges
    challenges = conn.mongo['Usr0Comp']['Challenges']
    await ctx.response.send_message("Select the challenges you want to be active", view=SelectChallengeView(conn=conn), ephemeral=True)

# Command to change the testing active challenges
@bot.command(description="Change which challenges are active for testing")
async def changetestactive(ctx):
    logging.info("Change test active challenges command invoked")
    global challenges
    challenges = conn.mongo['Usr0Comp']['Challenges']
    await ctx.response.send_message("Select the challenges you want to be Testing active", view=TestSelectChallengeView(conn=conn), ephemeral=True)


# Command to modify a user
@bot.command(description="Modify a User")
async def modifyuser(ctx, user: discord.User):
    logging.info(f"Modify user command invoked for user {user.id}")
    person = conn.mongo.users.find_one({"user_id": user.id})
    if person is None:
        await ctx.response.send_message("User not found", ephemeral=True)
        logging.info(f"User {user.id} not found")
        return
    await ctx.response.send_modal(ModifyUserFieldView(title="Modify User", user=person))
print (conn.discord_key)
bot.run(conn.discord_key)
