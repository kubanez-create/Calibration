# Calibration bot

Many people have trouble telling the difference between what they can control, know, predict and understand, and what they can't. We often base our expectations on our past experiences, without checking how accurate they were or how much they match the current situation. For example, we might ignore the dark clouds in the sky and trust our intuition that says it won't rain, even if the weather report said otherwise.

This bot was created to help people realize their limits in these cognitive tasks, especially when it comes to forecasting the future.  

## Installation

1. Clone this repository to your local machine:

```bash
git clone git@github.com:kubanez-create/Calibration.git
cd Calibration
```
2. Create and activate a virtual environment:
```bash
python3 -m venv env
source env/bin/activate
```
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```
4. Set up your environment variables by creating a .env file and adding the following:
```bash
TELEGRAM_TOKEN=<your_telegram_bot_token>
API_HASH=<your_api_hash>
API_ID=<your_api_id>
USER=<your_database_user>
PASSWORD=<your_database_users_password>
HOST=<your_database_host>
PORT=<your_database_port>
DATABASE=<your_database_name>
```
5. You might want to change some constants as well:
```bash
SESSION_NAME=<your_favorite_word>
CHUNK_SIZE=<number_predictions_for_page>
```
6. Run the bot:
```bash
python ru_calibration_bot.py
```

Alternatively you can use Docker:
`docker pull kubanez/calibration_bot:latest` then `docker run`

## Usage
This bot helps you track your predictions and measure your calibration. You can use it to record your beliefs about future events and compare them with the actual outcomes. 
Here's how to use it:
- **To make a new prediction**, click on the 'Добавить предсказание' button and enter the details of the event and your probability estimate.
- **To view your previous predictions**, click on the 'Показать предсказания' button and you will see a list of your predictions with their IDs.
- **To edit your previous prediction**, click on the 'Обновить предсказание' button and enter the ID of the prediction you want to change.
- **To delete your previous prediction**, click on the 'Удалить предсказание' button and enter the ID of the prediction you want to remove.
- **To enter the outcome of your prediction**, click on the 'Результат предсказания' button and enter the ID of the prediction and the actual result.
- **To check your calibration**, click on the 'Проверить калибровку' button and you will see a summary of how accurate your predictions were.
- **To show your categories added so far**, click on the 'Мои категории' button and you will see a list of your categories you use.
- **To contact the author of this bot**, send an email to kubanez74@gmail.com if you have any feedback, suggestions or complaints.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request. Alternatively you might contact me through [kubanez74@google.com](mailto:kubanez74@google.com).
