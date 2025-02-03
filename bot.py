import os
import discord
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId
#Requires a .env
try:
    load_dotenv()
    MONGODB_URI = os.environ['MONGODB_URI']
    Discord_Key = os.environ['Discord_Key']

    client = MongoClient(MONGODB_URI)
except Exception as e:
    print(f'MongoDB connection failed: {e}')
    exit(1)
print("Connected to MongoDB")
users = client['Usr0Comp']['Users']
challenges = client['Usr0Comp']['Challenges']
print("Connected to the Users and Challenges collections")
bot = discord.Bot()



#Class defining the Submission Modal
class SubmitField(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        self.challenge = kwargs.pop("challenge")
        super().__init__(*args, **kwargs)
        for question in self.challenge['questions']:
            try:
                self.add_item(discord.ui.InputText(label=question, placeholder="Answer"))
            except Exception as e:
                print(f"Error adding question: {e}")
                print(f"Ensure question is 45 characters or less, currently {len(question)}")


    async def callback(self, interaction: discord.Interaction):
        currChallenge = self.challenge
        person = users.find_one({"user_id": interaction.user.id})
        if person is not None and currChallenge['challNum'] in person['solves']:
            await interaction.response.send_message("You have already solved this challenge", ephemeral=True)
            return
        correct = True
        wrongquestions = []
        for i in range(len(self.children)):
            submission = self.children[i].value
            if submission.lower() != currChallenge['answers'][i].lower():
                correct = False
                wrongquestions.append(i+1)
        if correct:
            points = pointsCalc(person, currChallenge)
            if person is None:
                users.insert_one({"user_id": interaction.user.id, "points": currChallenge['points'], "solves": [currChallenge['challNum']], "attempts": 1})
            else:
                users.update_one({"user_id": interaction.user.id}, {"$set": {"points": person['points'] + points, "solves": person['solves'] + [currChallenge['challNum']], "attempts": person['attempts'] + 1}})       
            await interaction.response.send_message(f"Correct Answer! You have been awarded {points} points", ephemeral=True)
        else:
            wrongstring = ', '.join([str(i) for i in wrongquestions])
            await interaction.response.send_message(f"Questions {wrongstring} are incorrect", ephemeral=True)
            

#Function to calculate the points received
def pointsCalc(person, currChallenge):
    points = int(currChallenge['points']) - int(currChallenge['solves']) * 5
    challenges.update_one({"title": currChallenge['title']}, {"$set": {"solves": currChallenge['solves'] + 1}})
    if points < 10:
        points = 10
    return points



@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


catSlang = {"Open Source Intelligence" : "OSI"}



class Paginator(discord.ui.View):
    def __init__(self, **kwargs):
        self.challenge = kwargs.pop("challenge")
        super().__init__(timeout=None)
        self.embeds = kwargs.pop("embeds")
        self.files = kwargs.pop("files")
        self.current_page = kwargs.pop("current_page")
        self.views = kwargs.pop("views")

        self.previous_page.disabled = True if self.current_page == 0 else False
        self.next_page.disabled = True if self.current_page == len(self.embeds) - 1 else False

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, disabled=True)
    async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Go to the previous page."""
        self.message = await interaction.response.edit_message(
            embed=self.embeds[self.current_page - 1],
            files=fileListAssembler(self.files[self.current_page - 1]) if self.files else None,
            view=self.views[self.current_page - 1]
        )

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Go to the next page."""
        self.message = await interaction.response.edit_message(
            embed=self.embeds[self.current_page + 1],
            files=fileListAssembler(self.files[self.current_page + 1]) if self.files else None,
            view=self.views[self.current_page + 1]
        )

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.primary)
    async def submit(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(SubmitField(title="Submit Answer", challenge=self.challenge))

@bot.command(description="Start the bot")
async def start(ctx):
    activeChallenges = (challenges.find({"active": True})).sort("points", 1)
    if activeChallenges is None:
        await ctx.response.send_message("No active challenges", ephemeral=True)
        return
    await ctx.channel.purge()
    embeds = [None] * activeChallenges.collection.count_documents({"active": True})
    Images = []
    views = []
    for i, currChallenge in enumerate(activeChallenges):
        category = catSlang[currChallenge['category']] if currChallenge['category'] in catSlang else currChallenge['category']
        title = currChallenge['title'].replace(" ", "_")
        Images.append([])
        fileLinks = []
        for file in os.listdir(f"{category}/{title}"):
            if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg"):
                currChallenge['image'] = f"{category}/{title}/{file}"
                Images[i].append(f"{category}/{title}/{file}")
            else:
                fileLinks.append(f"https://github.com/droge91/Usr0Challenges/blob/main/{category}/{title}/{file}?raw=true")
        embed = assembleEmbed(currChallenge, fileLinks, i+1, activeChallenges.collection.count_documents({"active": True}))
        embeds[i] = embed
        views.append(Paginator(embeds = embeds, files = Images, views = views, current_page = i,challenge=currChallenge))


    await ctx.response.send_message(embed=embeds[0], view=views[0], files = fileListAssembler(Images[0]), ephemeral=True)


def fileListAssembler(files):
    return list(discord.File(file) for file in files)

def assembleEmbed(challenge, fileLinks, iter,tot):
    hyperlinks = "\n".join([f"[{file.split('/')[-1].split('?')[0]}]({file})" for file in fileLinks])
    questions = "\n".join([f"{i+1}. {question}" for i, question in enumerate(challenge['questions'])])

    embed = discord.Embed(
        title=f"{challenge['title']} - {challenge['points']} points",
        description=challenge['desc'] + f"\n{hyperlinks}" + f"\n\n{questions}",
        color=discord.Colour.blurple(),
    )

    embed.set_author(name= f"{challenge['category']}        {iter}/{tot}")
    embed.set_thumbnail(url=challenge['categoryIcon'])
    if challenge['image'] != "":
        embed.set_image(url=f"attachment://{challenge['image'].split('/')[-1]}")
    return embed

@bot.command(description="Show the current Standings")
async def standings(ctx):
    embed = discord.Embed(title="Standings", color=0x00ff00)
    top5 = users.find().sort([("points", -1), ("attempst", 1)]).limit(5)

    user = users.find_one({"user_id": ctx.author.id})
    if user is None:
        user = {"user_id": ctx.author.id, "points": 0, "solves": [], "attempts": 0}
        users.insert_one(user)

    leaderboard = ""
    top_5_ids = []
    for i, person in enumerate(top5):
        name = ctx.guild.get_member(person['user_id']).name if ctx.guild.get_member(person['user_id']) else "Unknown"
        leaderboard += f"{i+1}. {name} - {person['points']} points\n"
        top_5_ids.append(person['user_id'])

    embed.add_field(name="Leaderboard", value=leaderboard, inline=False)
    if ctx.author.id not in top_5_ids:
        name = ctx.guild.get_member(ctx.author.id).name if ctx.guild.get_member(ctx.author.id) else "Unknown"
        userplace = f"{name} - {user['points']} points"
        embed.add_field(name="Your Current Placement", value=userplace, inline=True)
    await ctx.response.send_message(embed=embed, ephemeral=True)


@bot.command(description="Change which challenges are active")
async def changeactive(ctx):
    await ctx.response.send_message("Select the challenges you want to be active", view=SelectChallengeView(), ephemeral=True)

class SelectChallengeView(discord.ui.View):
    @discord.ui.select(
        placeholder="Select the active challenges",
        min_values=1,
        max_values= challenges.count_documents({}),
        options=
        [
            discord.SelectOption(label=doc["title"], value=str(doc["_id"]))
            for doc in challenges.find()
        ]
    )

    async def callback(self, select, interaction: discord.Interaction):
        selected = select.values
        challenges.update_many({}, {"$set": {"active": False}})
        for challenge in selected:
            challenges.update_one({"_id": ObjectId(challenge)}, {"$set": {"active": True}})
        await interaction.response.send_message("Challenges have been updated", ephemeral=True)

class ModifyChallengeView(discord.ui.View):
    @discord.ui.select(
        placeholder="Select the challenge you want to modify",
        min_values=1,
        max_values= 1,
        options=
        [
            discord.SelectOption(label=doc["title"], value=str(doc["_id"]))
            for doc in challenges.find()
        ]
    )

    async def callback(self, select, interaction: discord.Interaction):
        selected = select.values
        for challenge in selected:
            currChallenge = challenges.find_one({"_id": ObjectId(challenge)})
            await interaction.response.send_modal(ModifyFieldView(title="Modify Challenge", challenge=currChallenge))

class ModifyFieldView(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        self.challenge = kwargs.pop("challenge")
        super().__init__(*args, **kwargs)
        excluded = ["_id", "active", "categoryIcon", "image", "challNum", "links", "category", "desc"]
        for key in self.challenge.keys():
            if key not in excluded:
                self.add_item(discord.ui.InputText(label=key, value=self.challenge[key]))

    async def callback(self, interaction: discord.Interaction):
        for child in self.children:
            if child.label == "points" or child.label == "solves":
                challenges.update_one({"_id": self.challenge["_id"]}, {"$set": {child.label: int(child.value)}})
            else:
                challenges.update_one({"_id": self.challenge["_id"]}, {"$set": {child.label: child.value}})
        await interaction.response.send_message("Challenge has been updated", ephemeral=True)

@bot.command(description="Modify a challenge")
async def modify(ctx):
    await ctx.response.send_message("Select the challenge you want to modify", view=ModifyChallengeView(), ephemeral=True)


@bot.command(description="Modify a User")
async def modifyuser(ctx, user: discord.User):
    person = users.find_one({"user_id": user.id})
    if person is None:
        await ctx.response.send_message("User not found", ephemeral=True)
        return
    await ctx.response.send_modal(ModifyUserFieldView(title="Modify User", user=person))

class ModifyUserFieldView(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        excluded = ["_id", "user_id", "solves"]
        for key in self.user.keys():
            if key not in excluded:
                self.add_item(discord.ui.InputText(label=key, value=self.user[key]))
    async def callback(self, interaction: discord.Interaction):
        for child in self.children:
                users.update_one({"user_id": self.user["user_id"]}, {"$set": {child.label: child.value}})
        await interaction.response.send_message("User has been updated", ephemeral=True)
bot.run(Discord_Key)
