import discord
import os
import importlib
from bson.objectid import ObjectId
import pagination_and_embeds
#Dictionary to convert the category names to slang
catSlang = {"Open Source Intelligence" : "OSI", "Enumeration & Exploitation" : "E&E"}

#Class defining the Submission Modal
class SubmitField(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        self.challenge = kwargs.pop("challenge")
        self.conn = kwargs.pop("conn")
        self.prac = kwargs.pop("prac")
        super().__init__(*args, **kwargs)
        for question in self.challenge['questions']:
            #Necessary due to hard limit on the length of the label
            try:
                self.add_item(discord.ui.InputText(label=question, placeholder="Answer"))
            except Exception as e:
                self.add_item(discord.ui.InputText(label=question[:42] + '...', placeholder="Answer"))


    async def callback(self, interaction: discord.Interaction):
        currChallenge = self.challenge
        category = catSlang[currChallenge['category']] if currChallenge['category'] in catSlang else currChallenge['category']
        title = currChallenge['title'].replace(" ", "_")
        person = self.conn.users.find_one({"user_id": interaction.user.id})
        if person is not None and currChallenge['challNum'] in person['solves']:
            await interaction.response.send_message("You have already solved this challenge", ephemeral=True)
            return
        correct = True
        wrongquestions = []
        complex = currChallenge.get('Complex_Answer')
        for i in range(len(self.children)):
            submission = self.children[i].value
            if complex and currChallenge['Complex_Answer'] == i:
                if os.path.exists(f"{category}/{title}/validate_{i}.py"):
                    module = importlib.import_module(f"{category}.{title}.validate_{i}")
                    validate = module.validate
                    if not validate(submission):
                        correct = False
                        wrongquestions.append(i+1)
                else:
                    await interaction.response.send_message("Complex answer required but not setup properly, contact Officer", ephemeral=True)
            else:
                if submission.lower() != currChallenge['answers'][i].lower():
                    correct = False
                    wrongquestions.append(i+1)
        if correct:
            points = self.pointsCalc(person, currChallenge) if not self.prac else 0
            if person is None:
                self.conn.users.insert_one({"user_id": interaction.user.id, "points": points, "solves": [currChallenge['challNum']], "attempts": 1})
            else:
                self.conn.users.update_one({"user_id": interaction.user.id}, {"$set": {"points": person['points'] + points, "solves": person['solves'] + [currChallenge['challNum']], "attempts": person['attempts'] + 1}})       
            await interaction.response.send_message(f"Correct Answer! You have been awarded {points} points", ephemeral=True)
        else:
            wrongstring = ', '.join([str(i) for i in wrongquestions])
            if wrongquestions == 1:
                await interaction.response.send_message(f"Question {wrongstring} is incorrect", ephemeral=True)
            else:
                await interaction.response.send_message(f"Questions {wrongstring} are incorrect", ephemeral=True)
                #calculate the points for a challenge

    def pointsCalc(self, person, currChallenge):
        updated_challenge = self.conn.challenges.find_one_and_update(
            {"title": currChallenge['title']},
            {'$inc': {'solves': 1}},
            return_document=True 
        )
        points = int(updated_challenge['points']) - int(updated_challenge['solves'] - 1) * 5

        if points < 10:
            points = 10
        return points

    

#Class for the changeactive selection
class SelectChallengeView(discord.ui.View):
    def __init__(self, *args, **kwargs) -> None:
        self.conn = kwargs.pop("conn")
        super().__init__(*args, **kwargs)
        self.select = discord.ui.Select(
            placeholder="Select the active challenges",
            min_values=1,
            max_values=self.conn.challenges.count_documents({}),
            options=[
                discord.SelectOption(label=doc["title"], value=str(doc["_id"]))
                for doc in self.conn.challenges.find()
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        selected = self.select.values
        self.conn.challenges.update_many({}, {"$set": {"active": False}})
        for challenge in selected:
            self.conn.challenges.update_one({"_id": ObjectId(challenge)}, {"$set": {"active": True}})
        await interaction.response.send_message("Challenges have been updated", ephemeral=True)

class PracticeCatSelectView(discord.ui.View):
    def __init__(self, *args, **kwargs) -> None:
        self.conn = kwargs.pop("conn")
        super().__init__(*args, **kwargs)
        self.select = discord.ui.Select(
            placeholder="Select the category you want to practice",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=cat, value=cat)
                for cat in self.conn.challenges.distinct("category")
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        selected = self.select.values
        practiceChallenges = (self.conn.challenges.find({"category": selected[0]})).sort("challNum")
        embeds, Images, views = pagination_and_embeds.genPaginStuff(practiceChallenges, self.conn, practice=True)
        await interaction.response.send_message(embed=embeds[0], view=views[0], files=pagination_and_embeds.fileListAssembler(Images[0]), ephemeral=True)

#Class for the changetestactive selection
class TestSelectChallengeView(discord.ui.View):
    def __init__(self, *args, **kwargs) -> None:
        self.conn = kwargs.pop("conn")
        super().__init__(*args, **kwargs)
        self.select = discord.ui.Select(
            placeholder="Select the Test challenges",
            min_values=1,
            max_values= self.conn.challenges.count_documents({}),
            options=
            [
                discord.SelectOption(label=doc["title"], value=str(doc["_id"]))
                for doc in self.conn.challenges.find()
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)
    async def select_callback(self, interaction: discord.Interaction):
        selected = self.select.values
        self.conn.challenges.update_many({}, {"$set": {"Testactive": False}})
        for challenge in selected:
            self.conn.challenges.update_one({"_id": ObjectId(challenge)}, {"$set": {"Testactive": True}})
        await interaction.response.send_message("Test Challenges have been updated", ephemeral=True)


#Class for the the user modification modal
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
                self.conn.users.update_one({"user_id": self.user["user_id"]}, {"$set": {child.label: child.value}})
        await interaction.response.send_message("User has been updated", ephemeral=True)