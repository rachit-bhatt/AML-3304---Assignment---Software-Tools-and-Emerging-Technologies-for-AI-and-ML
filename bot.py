import os
from slack_bolt import App
from slackeventsapi import SlackEventAdapter
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get the Slack tokens from the environment
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')  # Add this to your .env file for channel ID

# Check if tokens are loaded correctly
if SLACK_SIGNING_SECRET is None or SLACK_BOT_TOKEN is None:
    raise ValueError("SLACK_SIGNING_SECRET or SLACK_BOT_TOKEN is missing!")

# Bot Class Definition
class SlackBot:
    def __init__(self, bot_token, signing_secret, channel_id):
        """
        The function initializes a Flask app, SlackEventAdapter, and Slack Bolt App with specified
        parameters.
        
        :param bot_token: The `bot_token` parameter is a unique token that identifies your Slack bot and
        allows it to authenticate and interact with the Slack API on behalf of your app. This token is
        necessary for your bot to send messages, listen for events, and perform other actions within a
        Slack workspace
        :param signing_secret: The `signing_secret` is a unique secret value provided by Slack when
        setting up a Slack app. It is used to verify the authenticity of incoming events and requests
        from Slack to your app. This helps ensure that the events are indeed coming from Slack and not
        from a malicious source
        :param channel_id: The `channel_id` parameter in the `__init__` method is used to store the ID
        of the Slack channel where the bot will be interacting. This ID is typically a unique identifier
        for a specific channel within a Slack workspace. It allows the bot to target specific channels
        for sending messages, listening
        """
        # Initialize the Flask app
        self.app = Flask(__name__)

        # Initialize SlackEventAdapter for receiving events
        self.slack_event_adapter = SlackEventAdapter(signing_secret, "/slack/events", self.app)

        # Initialize Slack Bolt App using the bot token
        self.slack_app = App(token=bot_token)

        self.channel_id = channel_id

        # Register events and routes
        self.register_events()
        self.add_routes()

    def register_events(self):
        """Method to register Slack event handlers"""

        @self.slack_event_adapter.on("message")
        def handle_message(event_data):
            """Handle incoming messages"""
            message = event_data['event']
            if 'subtype' not in message:  # Avoid bot messages or special events
                channel = message['channel']
                user_message = message['text']
                
                # Echo the message back to the channel
                self.slack_app.client.chat_postMessage(channel=channel, text=f"Echo: {user_message}")

    def add_routes(self):
        """Add routes for the UI and message handling"""

        @self.app.route("/")
        def index():
            """Render the dashboard page"""
            return render_template('index.html')

        @self.app.route("/send_message", methods=["POST"])
        def send_message():
            """Send a message to the Slack channel"""
            data = request.get_json()
            message = data.get('text')
            
            if message:
                # Send message to the Slack channel
                self.slack_app.client.chat_postMessage(channel=self.channel_id, text=message)
                return jsonify({"status": "Message sent"}), 200
            return jsonify({"status": "Failed to send message"}), 400

        @self.app.route("/get_messages", methods=["GET"])
        def get_messages():
            """Fetch recent messages from the Slack channel"""
            result = self.slack_app.client.conversations_history(channel=self.channel_id, limit=10)

            messages = []
            for message in result['messages']:
                # Get user info
                user_info = self.slack_app.client.users_info(user=message['user'])
                user_name = user_info['user']['real_name']
                messages.append({
                    "text": message['text'],
                    "user": user_name,
                    "timestamp": message['ts']
                })
            return jsonify({"messages": messages})

    def run(self, port=3000):
        """Method to run the Flask app"""
        self.app.run(port=port)

# Main Function to Start the Bot
if __name__ == "__main__":
    # Create an instance of SlackBot
    slack_bot = SlackBot(SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_CHANNEL_ID)

    # Run the bot
    slack_bot.run()