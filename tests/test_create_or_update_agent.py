from unittest.mock import MagicMock
from src.core.upload import create_or_update_agent
from . import test_consts
from .test_agent_client_mock import AgentsClientMock

def make_agent(name, id="id1"):
    agent = MagicMock()
    agent.name = name
    agent.id = id
    return agent

class DummyClient:
    def __init__(self, agents=None):
        self._agents = agents or []
        self.create_agent = MagicMock(return_value=make_agent("created", "newid"))
        self.update_agent = MagicMock(return_value=make_agent("updated", "upid"))
        self.list_agents = MagicMock(return_value=self._agents)

def test_create_new_agent():
    client = AgentsClientMock()
    result = create_or_update_agent(test_consts.TEST_AGENT_DATA, client)
    assert result.name == test_consts.TEST_AGENT_DATA["name"]

def test_update_existing_agent():
    client = AgentsClientMock()
    create_or_update_agent(test_consts.TEST_AGENT_DATA, client)
    agent_data_update = test_consts.TEST_AGENT_DATA.copy()
    agent_data_update["instructions"] = "updated"
    result = create_or_update_agent(agent_data_update, client)
    assert result.instructions == "updated"
