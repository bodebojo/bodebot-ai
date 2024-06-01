import json
import GPUtil
import discord
import psutil
import datetime
from dataclasses import dataclass
from threading import Thread
from time import sleep
import random


DEV_MODE = False


@dataclass
class Character:
    display_name: str
    temp: int
    system_prompt: str


def get_characters() -> dict[str, Character]:
    with open("characters.json", "r") as file:
        data = json.load(file)
    return {k: Character(**v) for k, v in data.items()}


def rfind_most_newlines(current_content: str) -> tuple[str, str]:
    max_concec_count = 0
    max_concec_loc_end = 0
    curr_concec = 0
    curr_concec_loc_end = 0
    for i, char in reversed(list(enumerate(current_content))):
        if char != "\n":
            curr_concec = 0
            continue
        if curr_concec == 0:
            curr_concec_loc_end = i
        curr_concec += 1
        if curr_concec > max_concec_count:
            # print(f"{len(current_content)=}, {curr_concec_loc_end=}, {len(current_content) - curr_concec_loc_end=}")
            if curr_concec_loc_end >= 2000:
                print("Still not splitting, first half would be too long.")
            elif len(current_content) - curr_concec_loc_end >= 2000:
                print("Still not splitting, second half would be too long.")
            else:
                print(f"Setting new max (count: {curr_concec}, loc: {curr_concec_loc_end})")
                max_concec_count = curr_concec
                max_concec_loc_end = curr_concec_loc_end
    print(f"Found {max_concec_count} newlines at end {max_concec_loc_end}")
    first_half = current_content[:max_concec_loc_end + 1]
    second_half = current_content[max_concec_loc_end + 1:]
    # print(f"{first_half=}, {second_half=}")
    return first_half, second_half


generating = False
current_date = datetime.date.today()


def init(client, ai):
    characters = get_characters()

    @client.event
    async def on_message(message):
        global generating
        if DEV_MODE and message.author.id != 720991789133070369:
            return
        if message.content == "!stats":
            # Get GPU usage and temperature
            gpus = GPUtil.getGPUs()
            gpu_usage = gpus[0].load * 100  # Assuming there is only one GPU
            gpu_temperature = gpus[0].temperature  # Assuming there is only one GPU

            # Get memory usage
            memory_usage = psutil.virtual_memory().used / (1024 ** 3)  # Convert bytes to gigabytes

            # Format the information
            gpu_info = f"{gpu_usage:.0f}% GPU, {gpu_temperature:.0f}°C GPU"
            memory_info = f"{memory_usage:.0f} GB Memory"

            await message.reply(f"[{gpu_info}, {memory_info}]")
            return
        if message.author == client.user:
            # Needed something here to compact in view lol
            return
        if message.content == "!reset":
            ai.set_system_prompt("")
            ai.reset()
            await message.reply(f"{client.user} has been reset.")
            return
        if message.content.startswith("!character"):
            character = message.content.removeprefix("!character ")
            if character not in characters:
                await message.reply(f"{character} does not exist.\n"
                                    f"Available characters: {', '.join(characters)}")
                return
            character = characters[character]
            for guild in client.guilds:
                try:
                    print(f"Setting nick to {character.display_name} for {guild}")
                    await guild.get_member(client.user.id).edit(nick=character.display_name)
                except discord.errors.Forbidden:
                    print(f"ERROR: Failed to set nick in guild {guild}, skipping")
            ai.set_system_prompt(character.system_prompt)
            ai.set_temp(character.temp)
            print(f"Setting temperature to {character.temp}")
            ai.reset()
            await message.reply(f"Switched character to {character.display_name}.")
            return
        if message.content.startswith("!roll"):
            dice = message.content.removeprefix("!roll ")

            def roll_dice(start, stop):
                return random.randrange(start, stop)

            if dice == "d4":
                await message.reply(f"<@{message.author.id}> **rolled a d4** \n **Result**: {roll_dice(1,4)}")
            elif dice == "d6":
                await message.reply(f"<@{message.author.id}> **rolled a d6** \n **Result**: {roll_dice(1,6)}")
            elif dice == "d8":
                await message.reply(f"<@{message.author.id}> **rolled a d8** \n **Result**: {roll_dice(1,8)}")
            elif dice == "d10":
                await message.reply(f"<@{message.author.id}> **rolled a d10** \n **Result**: {roll_dice(1,10)}")
            elif dice == "d12":
                await message.reply(f"<@{message.author.id}> **rolled a d12** \n **Result**: {roll_dice(1,12)}")
            elif dice == "d20":
                await message.reply(f"<@{message.author.id}> **rolled a d20** \n **Result**: {roll_dice(1,20)}")
            elif dice == "d100":
                await message.reply(f"<@{message.author.id}> **rolled a d100** \n **Result**: {roll_dice(1,100)}")
            return
        if message.content.startswith("!"):
            await message.reply(f"Command not found.")
            return

        initial_content = "Generating...\n"
        # if message.content.startswith("<@1222171268766502983>"):
        #     message.content = message.content.removeprefix("<@1222171268766502983>")
        if generating:
            print(f"Denying; already generating (prompt={message.content})")
            await message.reply("F u no gen")
            return
        generating = True
        response = await message.reply(initial_content)
        current_content = initial_content
        previous_messages = []
        done = False

        def generate_response():
            nonlocal current_content
            nonlocal done
            nonlocal response
            global generating
            global current_date

            print(current_date)
            generator = ai.generate(message.content, message.author, current_date)

            for token in generator:
                current_content += token
                # print(current_content)

            generating = False
            # print(current_content)
            print("Done generating")
            done = True

        gt = Thread(target=generate_response)
        gt.start()

        async def update_response():
            nonlocal response
            nonlocal current_content

            if len(current_content) > 2000:
                # Altijd van achteraan zoeken zodat de tweede message zo kort mogelijk wordt
                #   (alleen als het sws zo perfect mogelijk is)
                # Als hij nu in een code block zit, moet hij vlak voor de code block splitten
                if current_content.count("```") % 2 == 1:
                    print("In code block rn")
                    if "````" in current_content:
                        print("WARNING: quadruple backtick invalidates check for triple backtick. "
                              "Splitting is broken for this response.")
                    block_start = current_content.rfind("```")
                    # Als het dan nog langer is dan 2000, split dan halverwege (en log)
                    if block_start == 0:
                        print("Code block longer than 2000 characters, so splitting on most newlines")
                        # Meeste newlines achter elkaar
                        first_half, second_half = rfind_most_newlines(current_content)
                    else:
                        first_half = current_content[:block_start]
                        second_half = current_content[block_start:]
                # Als hij niet in een code block zit, maar er wel een code block is geweest in de message,
                #   moet hij vlak na de code block splitten
                elif current_content.count("```") >= 1:
                    print("Not in code block, but have had at least one")
                    block_end = current_content.rfind("```") + 3
                    first_half = current_content[:block_end]
                    second_half = current_content[block_end:]
                # Meeste newlines achter elkaar (een newline vervangen door de message break)
                else:
                    print("Nothing weird, just splitting on most newlines")
                    first_half, second_half = rfind_most_newlines(current_content)

                # print(f"{len(first_half)=}, {first_half=}")
                # print(f"{len(second_half)=}, {second_half=}")
                if len(first_half) > 2000:
                    print("uuhhhh how did this happen")
                    raise RuntimeError(len(first_half), first_half)
                if len(second_half) > 2000:
                    print("Kan dit?")
                    raise RuntimeError(len(second_half), second_half)
                if first_half.endswith("\n"):
                    first_half = first_half.removesuffix("\n")
                while True:
                    if first_half.endswith("\n"):
                        first_half = first_half.removesuffix("\n")
                        second_half = "_ _\n" + second_half
                    else:
                        break
                while True:
                    if second_half.startswith("\n"):
                        second_half = second_half.removeprefix("\n")
                        second_half = "_ _\n" + second_half
                    else:
                        break
                await response.edit(content=first_half)
                second_message = await response.channel.send("Generating...")
                current_content = second_half
                previous_messages.append(response)
                response = second_message

            suffix = ""
            if current_content.count("```") % 2 == 1:
                suffix += "```"
            await response.edit(content=current_content + suffix)

        while not done:
            await update_response()
            sleep(1.0)
        await update_response()
        if previous_messages:
            await previous_messages[0].edit(
                content=(await previous_messages[0].fetch()).content.removeprefix("Generating...\n"))
        else:
            await response.edit(
                content=(await response.fetch()).content.removeprefix("Generating...\n"))
        gt.join()
