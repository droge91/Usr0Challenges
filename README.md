# Usr0 Challenge Submissions Bot

A Discord bot that allows users to participate in and submit answers for various challenges, track their points, and manage challenges within a MongoDB database.

---

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Slash Commands](#slash-commands)
  - [Submitting an Answer](#submitting-an-answer)
  - [Challenge Management](#challenge-management)
- [Folder Structure](#folder-structure)
- [How It Works](#how-it-works)
  - [MongoDB Collections](#mongodb-collections)
  - [Points Calculation](#points-calculation)
  - [Pagination and File Embeds](#pagination-and-file-embeds)
- [Contributing](#contributing)
- [License](#license)

---

## Features
- **Slash Commands** for starting a challenge, viewing standings, modifying challenges, and more.
- **Modal-based Submissions**: Users can submit their solutions via Discord modals.
- **MongoDB Integration** for storing and retrieving user data and challenge info.
- **Dynamic Challenge Activation**: Activate or deactivate specific challenges.
- **Standings**: Displays a leaderboard with the top 5 users and your own current points.
- **User & Challenge Management**: Modify user points or challenge attributes on the fly.

---

## Prerequisites
1. [Python 3.8+](https://www.python.org/downloads/)
2. [pip](https://pip.pypa.io/en/stable/)
3. A [MongoDB](https://www.mongodb.com/) database or MongoDB Atlas connection URI.
4. A Discord Bot Token from the [Discord Developer Portal](https://discord.com/developers/applications).

    The MongoDB URI and Discord Token should be provided by a .env
---

## Installation
1. **Clone** or **download** this repository.
2. In your terminal, **navigate to the project folder**.
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   - You need the following packages:
     - `py-cord`
     - `python-dotenv`
     - `pymongo`
   - Adjust as needed for your Python environment.

---

## Configuration
1. Ensure that you have the .env file with the Bot token and MongoDB URI

2. Ensure the `.env` file is **not** committed to version control (check it is present in the `.gitignore`).

---

## Usage
1. **Run the bot**:
   ```bash
   python bot.py
   ```


### Slash Commands

- **`/start`**  
  Posts an interactive embed for **active** challenges. Users can navigate between challenges with "Previous" and "Next," then submit their answers.

- **`/standings`**  
  Shows the top 5 users by points and also displays your own points if you're not in the top 5.

- **`/changeactive`**  
  Lets you select which challenges should be set to **active**. Only active challenges appear when you run `/start`.

- **`/modify`**  
  Opens a selection menu for challenges you can edit. Upon selecting a challenge, you can modify various fields (like `title`, `answer`, `points`, etc.).

- **`/modifyuser <@User>`**  
  Modify a specific user's document in the database (e.g., change points). Selecting a user triggers a modal to update the stored data.

### Submitting an Answer
1. After running `/start`, you’ll see embeds for each active challenge.
2. To submit an answer, click the **Submit** button on the embed or the modal's "Submit" button.
3. A modal pops up, prompting you to enter your solution.  
   - If correct, you'll receive points (based on the challenge’s point rules).
   - If you've already solved that challenge, the bot will let you know.

### Challenge Management
- **Activating & Deactivating Challenges**:  
  Via `/changeactive`, you can toggle which challenges are displayed in `/start`.
- **Modifying Challenges**:  
  Use `/modify` to change challenge fields such as `title`, `answer`, `points`, etc.
- **Modifying Users**:  
  Use `/modifyuser @Username` to update user-specific data like points or any custom fields.

---

## Folder Structure
A typical folder structure might look like this:

```
.
├─ OSI/
│  ├─ challenge_one/
│  │  ├─ image.png
│  │  ├─ ...
│  ├─ ...
├─ other_category/
│  ├─ challenge_two/
│  │  ├─ image.jpg
│  │  ├─ ...
├─ bot.py
├─ requirements.txt
└─ .env
```
Ensure that your challenges folder is named the same as what is described in the MongoDB title field(Replace spaces with underscores)

- **OSI/**, **other_category/**, etc.:  
  Each category folder holds subfolders for each challenge (`challenge_one`, `challenge_two`, etc.), which contain images or files needed for that challenge.
  Images will be included in the embed while other filetypes will be included in the embed as hyperlinks.

---

## How It Works

### MongoDB Collections
- **Users** (collection: `Usr0Comp.Users`)  
  Each document represents a Discord user who has participated in at least one challenge.
  ```json
  {
    "user_id": 123456789012345678,
    "points": 100,
    "solves": [1, 2, 5, ...]
  }
  ```
  
- **Challenges** (collection: `Usr0Comp.Challenges`)  
  Each document represents a single challenge.
  ```json
  {
    "_id": ObjectId(...),
    "challNum": 1,
    "title": "Challenge Title",
    "desc": "Challenge Description",
    "points": 100,
    "solves": 0,
    "questions": "[question1, question2]",
    "answers": "[answer1, answer2]",
    "active": true,
    "category": "Open Source Intelligence",
    "categoryIcon": "https://link_to_icon.png",
    "image": "",
    ...
  }
  ```

### Points Calculation
When a user submits the correct answer:
1. The bot checks how many times the challenge has been solved so far (`challenge['solves']`).
2. Points are calculated as:
   ```
   points = challenge['points'] - (challenge['solves'] * 5)
   ```
   - **Minimum** of `10` points is enforced (i.e., if the formula drops below `10`, the user still gets `10`).
3. The database increments the `solves` count for that challenge.
4. The user’s document is updated with the new total points and the challenge number is added to their `solves` array.

### Pagination and File Embeds
- The bot uses a custom `Paginator` class to display each active challenge in an embed.
- **Navigation**: "Previous" and "Next" buttons switch between pages.
- **Images/Files**: If an image file is found in the corresponding folder, it gets attached to the embed.

---

## Contributing
1. Create a new **feature branch**.
2. Commit your changes.
3. Submit a **pull request**.

All contributions are welcome to improve features, documentation, or performance.

