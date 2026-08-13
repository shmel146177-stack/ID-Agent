from app.core.agent import IDAgent, agent


def test_agent_status_contract():

    local_agent = IDAgent()

    assert local_agent.name == "ID-Agent"
    assert local_agent.version == "0.1"

    status = local_agent.status()

    assert status["agent"] == "ID-Agent"
    assert status["version"] == "0.1"
    assert "status" in status
    assert status["status"]

    global_status = agent.status()

    assert global_status["agent"] == "ID-Agent"
    assert global_status["version"] == "0.1"
