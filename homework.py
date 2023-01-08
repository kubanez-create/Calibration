"""Telegram bot which keeps track of your predictions."""
from __future__ import annotations

import logging
import os
import sys
from logging import StreamHandler

from telethon import TelegramClient, events, Button # pip install telethon
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN: str = str(os.getenv("TELEGRAM_TOKEN"))
API_HASH: str = str(os.getenv("API_HASH"))
API_ID: int = int(os.getenv("API_ID"))
USER: str = str(os.getenv("USER"))
PASSWORD: str = str(os.getenv("PASSWORD"))
HOST: str = str(os.getenv("HOST"))
PORT: str = str(os.getenv("PORT"))
DATABASE: str = str(os.getenv("DATABASE"))

SESSION_NAME = "sessions/Bot"

# Start the Client (telethon)
client = TelegramClient(SESSION_NAME, API_ID, API_HASH).start(bot_token=TELEGRAM_TOKEN)

def check_tokens() -> bool:
    """Function which ckecks availability of global variables."""
    return all((TELEGRAM_TOKEN, API_HASH, API_ID))

### START COMMAND
@client.on(events.NewMessage(pattern="(?i)/start"))
async def start(event):
    # Get sender
    sender = await event.get_sender()
    SENDER = sender.id
    
    # set text and send message
    markup = event.client.build_reply_markup([
        [
            Button.inline('Make prediction', b'mkpred'),
            Button.inline('Help', b'help')
        ],
        [
            Button.inline('Update prediction', b'updpred'),
            Button.inline('Check calibration', b'check')
        ]
    ])
    
    text = "Hello let's make some pretty predictions, bwah"
    await client.send_message(SENDER, text, buttons=markup)

### insert will be here COMMAND
@client.on(events.CallbackQuery(data=b'mkpred'))
async def start(event):
    # Get sender
    sender = await event.get_sender()
    SENDER = sender.id
    
    # Start a conversation
    async with client.conversation(await event.get_chat(), exclusive=True) as conv:
        text = "Enter your prediction in right format"
        await conv.send_message(text)
        response = await conv.get_response()
        list_of_words = response.text.split("; ")
        user_id = SENDER
        date = datetime.now().strftime("%d/%m/%Y") # Use the datetime library to the get the date (and format it as DAY/MONTH/YEAR)
        task_description = list_of_words[0]
        task_category = list_of_words[1]
        unit_of_measure = list_of_words[2]
        prediction_50_percent_sure = list_of_words[3]
        prediction_90_percent_sure = list_of_words[4]
        actual = None

        # Create the tuple "params" with all the parameters inserted by the user
        params = (user_id, date, task_description, task_category,
                  unit_of_measure,prediction_50_percent_sure,
                  prediction_90_percent_sure, actual)
        sql_command = """INSERT INTO raw_predictions VALUES
                         (NULL, %s, %s, %s, %s, %s, %s, %s, %s);""" # the initial NULL is for the AUTOINCREMENT id inside the table
        crsr.execute(sql_command, params) # Execute the query
        conn.commit() # commit the changes

        # If at least 1 row is affected by the query we send specific messages
        if crsr.rowcount < 1:
            text = "Something went wrong, please try again"
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Order correctly inserted"
            await client.send_message(SENDER, text, parse_mode='html')

        await conv.cancel_all()
        return

### Insert command
@client.on(events.NewMessage(pattern="(?i)/insert"))
async def insert(event):
    try:
        # Get the sender of the message
        sender = await event.get_sender()
        SENDER = sender.id

        # /insert bottle 10

        # Get the text of the user AFTER the /insert command and convert it to a list (we are splitting by the SPACE " " simbol)
        list_of_words = event.message.text.split("; ")
        user_id = SENDER
        date = datetime.now().strftime("%d/%m/%Y") # Use the datetime library to the get the date (and format it as DAY/MONTH/YEAR)
        task_description = list_of_words[1]
        task_category = list_of_words[2]
        unit_of_measure = list_of_words[3]
        prediction_50_percent_sure = list_of_words[4]
        prediction_90_percent_sure = list_of_words[5]
        actual = None

        # Create the tuple "params" with all the parameters inserted by the user
        params = (user_id, date, task_description, task_category,
                  unit_of_measure,prediction_50_percent_sure,
                  prediction_90_percent_sure, actual)
        sql_command = """INSERT INTO raw_predictions VALUES
                         (NULL, %s, %s, %s, %s, %s, %s);""" # the initial NULL is for the AUTOINCREMENT id inside the table
        crsr.execute(sql_command, params) # Execute the query
        conn.commit() # commit the changes

        # If at least 1 row is affected by the query we send specific messages
        if crsr.rowcount < 1:
            text = "Something went wrong, please try again"
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Order correctly inserted"
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "Something Wrong happened... Check your code!", parse_mode='html')
        return



# Function that creates a message containing a list of all the oders
def create_message_select_query(ans):
    text = ""
    for i in ans:
        id = i[0]
        product = i[1]
        quantity = i[2]
        creation_date = i[3]
        text += "<b>"+ str(id) +"</b> | " + "<b>"+ str(product) +"</b> | " + "<b>"+ str(quantity)+"</b> | " + "<b>"+ str(creation_date)+"</b>\n"
    message = "<b>Received 📖 </b> Information about orders:\n\n"+text
    return message

### SELECT COMMAND
@client.on(events.NewMessage(pattern="(?i)/select"))
async def select(event):
    try:
        # Get the sender of the message
        sender = await event.get_sender()
        SENDER = sender.id
        # Execute the query and get all (*) the oders
        crsr.execute("SELECT * FROM orders")
        res = crsr.fetchall() # fetch all the results
        # If there is at least 1 row selected, print a message with the list of all the oders
        # The message is created using the function defined above
        if(res):
            text = create_message_select_query(res) 
            await client.send_message(SENDER, text, parse_mode='html')
        # Otherwhise, print a default text
        else:
            text = "No orders found inside the database."
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "Something Wrong happened... Check your code!", parse_mode='html')
        return



### UPDATE COMMAND
@client.on(events.NewMessage(pattern="(?i)/update"))
async def update(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        # Get the text of the user AFTER the /update command and convert it to a list (we are splitting by the SPACE " " simbol)
        list_of_words = event.message.text.split(" ")
        id = int(list_of_words[1]) # second (1) item is the id
        new_product = list_of_words[2] # third (2) item is the product
        new_quantity = list_of_words[3] # fourth (3) item is the quantity
        dt_string = datetime.now().strftime("%d/%m/%Y") # We create the new date

        # create the tuple with all the params interted by the user
        params = (id, new_product, new_quantity, dt_string, id)

        # Create the UPDATE query, we are updating the product with a specific id so we must put the WHERE clause
        sql_command="UPDATE orders SET id=%s, product=%s, quantity=%s, LAST_EDIT=%s WHERE id =%s"
        crsr.execute(sql_command, params) # Execute the query
        conn.commit() # Commit the changes

        # If at least 1 row is affected by the query we send a specific message
        if crsr.rowcount < 1:
            text = "Order with id {} is not present".format(id)
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Order with id {} correctly updated".format(id)
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "Something Wrong happened... Check your code!", parse_mode='html')
        return



@client.on(events.NewMessage(pattern="(?i)/delete"))
async def delete(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        #/ delete 1

        # get list of words inserted by the user
        list_of_words = event.message.text.split(" ")
        id = list_of_words[1] # The second (1) element is the id

        # Crete the DELETE query passing the id as a parameter
        sql_command = "DELETE FROM orders WHERE id = (%s);"

        # ans here will be the number of rows affected by the delete
        ans = crsr.execute(sql_command, (id,))
        conn.commit()
        
        # If at least 1 row is affected by the query we send a specific message
        if ans < 1:
            text = "Order with id {} is not present".format(id)
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Order with id {} was correctly deleted".format(id)
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "Something Wrong happened... Check your code!", parse_mode='html')
        return


if __name__ == "__main__":
    try:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        logger: logging.Logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        handler: StreamHandler = StreamHandler(stream=sys.stdout)
        logger.addHandler(handler)

        # Connect to the database
        conn = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )

        # Create a cursor
        crsr = conn.cursor()

        # Command that creates the "oders" table 
        sql_command = """CREATE TABLE IF NOT EXISTS raw_predictions ( 
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id INT(10), 
            date VARCHAR(100),
            task_description VARCHAR(200),
            task_category VARCHAR(50),
            unit_of_measure VARCHAR(30), 
            prediction_50_percent_sure INT(10),
            prediction_90_percent_sure INT(10), 
            actual_outcome INT(10));"""

        crsr.execute(sql_command)
        print("All tables are ready")
        
        print("Bot Started...")
        client.run_until_disconnected()

    except Exception as error:
        print('Cause: {}'.format(error))
