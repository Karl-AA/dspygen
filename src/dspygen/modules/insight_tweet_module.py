"""
The source code is used to import the necessary libraries and modules for the program. It also defines a class called "InsightTweetModule" which contains a function called "forward" that takes in an "insight" parameter and returns a result. The "insight_tweet_call" function uses the "InsightTweetModule" class to call the "forward" function and return the result. The "call" function is used to initialize the program and print the result of the "insight_tweet_call" function. The "main" function is used to initialize the program and print the result of the "insight_tweet_call" function.
"""
import dspy
import pyperclip
from typer import Typer

from dspygen.rdddy.abstract_actor import AbstractActor
from dspygen.rdddy.abstract_command import AbstractCommand
from dspygen.rdddy.abstract_event import AbstractEvent
from dspygen.utils.dspy_tools import init_dspy


app = Typer()


class InsightTweetModule(dspy.Module):
    """InsightTweetModule"""

    def forward(self, insight):
        pred = dspy.ChainOfThought("insight -> tweet_with_length_of_100_chars")
        result = pred(insight=insight).tweet_with_length_of_100_chars
        return result


def insight_tweet_call(insight):
    insight_tweet = InsightTweetModule()
    return insight_tweet.forward(insight=insight)


class InsightTweetModuleCommand(AbstractCommand):
    """Generate Tweet"""


class InsightTweetModuleEvent(AbstractEvent):
    """Generate Tweet"""


class InsightTweetModuleActor(AbstractActor):
    async def handle_tax_return(self, command: InsightTweetModuleCommand):
        await self.publish(InsightTweetModuleEvent(content=insight_tweet_call(command.content)))



@app.command()
def call(insight):
    """InsightTweetModule"""
    init_dspy()

    print(insight_tweet_call(insight=insight))


def main():
    init_dspy()
    insight = pyperclip.paste()
    print(insight_tweet_call(insight=insight))


if __name__ == "__main__":
    main()
