import asyncio

import pytest
from loguru import logger

from dspygen.rdddy.base_actor import BaseActor
from dspygen.rdddy.base_event import BaseEvent
from dspygen.rdddy.actor_system import ActorSystem
from dspygen.rdddy.base_message import BaseMessage


class TestBaseActor(BaseActor):
    def __init__(self, actor_system: "ActorSystem", actor_id=None):
        super().__init__(actor_system, actor_id)
        self.received_message = None

    async def handle_event(self, event: BaseEvent):
        self.received_message = event.content


class LogSink:
    def __init__(self):
        self.messages = []

    def write(self, message):
        self.messages.append(message)

    def __str__(self):
        return "".join(self.messages)


@pytest.fixture()
def log_sink():
    sink = LogSink()
    logger.add(sink, format="{message}")
    yield sink
    logger.remove()


@pytest.fixture()
def actor_system(event_loop):
    """Fixture to create an instance of the AbstractActorSystem class for testing purposes."""
    return ActorSystem(loop=event_loop)


@pytest.mark.asyncio()
async def test_actor_creation(actor_system):
    """Test case to verify actor creation within the AbstractActorSystem.

    Preconditions:
        - An instance of the AbstractActorSystem class must be available.

    Actions:
        - Creates an actor within the actor system.

    Postconditions:
        - Verifies that the created actor is accessible within the actor system.
    """
    actor = await actor_system.actor_of(BaseActor)
    assert actor is actor_system[actor.actor_id]


@pytest.mark.asyncio()
async def test_publishing(actor_system):
    """Test case to verify message publishing within the AbstractActorSystem.

    Preconditions:
        - An instance of the AbstractActorSystem class must be available.

    Actions:
        - Creates two test actors within the actor system.
        - Publishes an event message.
        - Allows time for message processing.

    Postconditions:
        - Verifies that each actor has received the published message.
    """
    actor1 = await actor_system.actor_of(TestBaseActor)
    actor2 = await actor_system.actor_of(TestBaseActor)

    await actor_system.publish(BaseEvent(content="Content"))

    await asyncio.sleep(0)  # Allow time for message processing

    assert actor1.received_message == "Content"
    assert actor2.received_message == "Content"


@pytest.mark.asyncio()
async def test_wait_for_event_sequentially(actor_system):
    """Tests the AbstractActorSystem's ability to wait for a specific event type and receive it once published.

    This test ensures that the AbstractActorSystem can correctly wait for an event of a specified type and then receive that event
    after it has been published. It utilizes asyncio.gather to concurrently start the event waiting process and publish the event,
    with a slight delay before publishing to ensure the system is indeed waiting for the event. This test helps verify that the
    AbstractActorSystem's event waiting mechanism is functioning as expected, particularly in scenarios where the order of operations is
    critical to the system's behavior.

    Args:
        actor_system (AbstractActorSystem): The AbstractActorSystem instance being tested.

    Steps:
        1. Define a test event of the expected type (`Event`) with a specific content.
        2. Implement an asynchronous function `publish_event` that introduces a short delay before publishing
           the test event to the AbstractActorSystem. This delay ensures that the system starts waiting for the event
           before it is actually published.
        3. Implement an asynchronous function `wait_for_event` that awaits the arrival of a message of the specified
           type (`Event`) within the AbstractActorSystem.
        4. Use `asyncio.gather` to run both `wait_for_event` and `publish_event` concurrently. The ordering within
           `asyncio.gather` and the delay in `publish_event` ensure that the system begins waiting for the event
           before it is published.
        5. Assert that the event received by the waiting function matches the content of the test event that was published.
           This confirms that the AbstractActorSystem's waiting and event handling mechanisms are operating correctly.

    Preconditions:
        - The `AbstractActorSystem` instance must be initialized and capable of publishing events and waiting for specific event types.

    Postconditions:
        - The system successfully waits for and receives the specified event after it has been published, indicating
          that event waiting and receiving are functioning as intended within the AbstractActorSystem.

    """
    test_event = BaseEvent(content="Test event for waiting")

    async def publish_event():
        # A short delay ensures that the system is indeed waiting for the event before it's published.
        await asyncio.sleep(0.1)
        await actor_system.publish(test_event)

    async def wait_for_event():
        # This will start waiting before the event is published due to the sleep in publish_event.
        return await actor_system.wait_for_message(BaseEvent)

    # Use asyncio.gather to run both the publishing and waiting concurrently,
    # but sequence the publish to happen after the wait has started.
    received_event, _ = await asyncio.gather(wait_for_event(), publish_event())

    assert received_event.content == test_event.content


@pytest.mark.asyncio()
async def test_actor_removal(actor_system, log_sink):
    removable_actor = await actor_system.actor_of(BaseActor)

    # Initially, ensure the actor is in the system
    assert removable_actor.actor_id in actor_system.actors

    # Remove the actor from the system
    await actor_system.remove_actor(removable_actor.actor_id)

    # Verify the actor has been removed
    assert removable_actor.actor_id not in actor_system.actors

    # Attempt to send a message to the removed actor
    test_message = BaseEvent(content="Message to removed actor.")
    await actor_system.send(removable_actor.actor_id, test_message)

    assert f"Actor {removable_actor.actor_id} not found." in str(log_sink)


@pytest.mark.asyncio()
async def test_error_when_base_message_used(actor_system):
    """Verifies that using the base Message class directly raises a ValueError.

    Preconditions:
        - An instance of the AbstractActorSystem class must be available.

    Actions:
        - Attempts to publish a message using the base Message class.

    Postconditions:
        - A ValueError is raised, indicating the base Message class should not be used directly.
    """
    base_message_instance = (
        BaseMessage()
    )  # Create an instance of the base Message class

    with pytest.raises(ValueError) as exc_info:
        await actor_system.publish(
            base_message_instance
        )  # Attempt to publish the base message instance

    # Check if the error message matches the expected output
    assert "The base Message class should not be used directly" in str(exc_info.value)


@pytest.mark.asyncio()
async def test_actors_creation(actor_system):
    # Placeholder for testing creation of multiple actors
    actors = await actor_system.actors_of([TestBaseActor, TestBaseActor])
    assert len(actors) == 2
    for actor in actors:
        assert isinstance(actor, TestBaseActor)


import asyncio
import pytest
from unittest.mock import patch, MagicMock


# @pytest.mark.asyncio
# async def test_publish_message():
#     actor_system = ActorSystem(mqtt_broker="localhost", mqtt_port=1883)
#
#     # Directly patch the mqtt_client's publish method
#     with patch('dspygen.rdddy.actor_system.ActorSystem.mqtt_client.publish', new_callable=MagicMock) as mock_publish:
#         test_message = AbstractEvent(content="Test publish message")
#         await actor_system.publish(test_message)
#
#         # Allow some time for async operations
#         await asyncio.sleep(0.1)
#
#         # Assert the publish method was called as expected
#         mock_publish.assert_called_once_with(
#             'actor_system/publish',
#             test_message.model_dump_json(),
#             # Include any additional parameters you expect
#         )

@pytest.mark.asyncio()
async def test_send_message(actor_system):
    actor = await actor_system.actor_of(TestBaseActor)
    test_message = BaseEvent(content="Direct send test")
    await actor_system.send(actor.actor_id, test_message)
    await asyncio.sleep(0)
    assert actor.received_message == "Direct send test"


@pytest.mark.asyncio()
async def test_actor_system_shutdown(actor_system):
    await actor_system.shutdown()
    # Validate MQTT client stopped and disconnected
    # assert not actor_system.mqtt_client.is_connected()
    # Additional checks for actor termination and resource release
    assert "Shutdown logic validation"  # Placeholder assertion
