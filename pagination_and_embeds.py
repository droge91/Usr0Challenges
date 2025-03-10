import discord
import modals_and_views
import os




#Class defining the Paginator
class Paginator(discord.ui.View):
    def __init__(self, **kwargs):
        self.challenge = kwargs.pop("challenge")
        super().__init__(timeout=None)
        self.embeds = kwargs.pop("embeds")
        self.files = kwargs.pop("files")
        self.current_page = kwargs.pop("current_page")
        self.views = kwargs.pop("views")
        self.conn = kwargs.pop("conn")
        self.practice = kwargs.pop("practice") if "practice" in kwargs else False

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
        await interaction.response.send_modal(modals_and_views.SubmitField(title="Submit Answer", challenge=self.challenge, conn=self.conn, prac = self.practice))

    #Function to generate the pages for the paginator
def genPaginStuff(activeChallenges, conn, test=False, practice=False):
        len = sum(1 for _ in activeChallenges)
        activeChallenges.rewind()
        embeds = [None] * len
        Images = []
        views = []
        for i, currChallenge in enumerate(activeChallenges):
            category = modals_and_views.catSlang[currChallenge['category']] if currChallenge['category'] in modals_and_views.catSlang else currChallenge['category']
            title = currChallenge['title'].replace(" ", "_")
            Images.append([])
            fileLinks = []
            if os.path.exists(f"{category}/{title}"):
                #Iterate through the files in the challenge directory
                for file in os.listdir(f"{category}/{title}"):
                    #Image files are added to the image list, other files are uploaded to S3 to be refereced as links
                    if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg"):
                        currChallenge['image'] = f"{category}/{title}/{file}"
                        Images[i].append(f"{category}/{title}/{file}")
                    elif not file.endswith(".py") and not file == '__pycache__':
                        if not conn.checkS3(f"{category}/{title}/{file}"):
                            conn.uploadS3(f"{category}/{title}/{file}")
                        fileLinks.append(f"https://challfiles.s3.us-east-2.amazonaws.com/{category}/{title}/{file}")
            if 'image' not in currChallenge:
                currChallenge['image'] = ""
            embed = assembleEmbed(currChallenge, fileLinks, i+1, len)
            embeds[i] = embed
            views.append(Paginator(embeds = embeds, files = Images, views = views, current_page = i,challenge=currChallenge, conn=conn, practice=practice))
        return embeds, Images, views



    #helper function to assemble a list of discord files
def fileListAssembler(files):
        return list(discord.File(file) for file in files)

    #Function to assemble the embed for a challenge
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