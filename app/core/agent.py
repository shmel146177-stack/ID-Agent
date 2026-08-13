class IDAgent:
    def __init__(self):
        self.name = "ID-Agent"
        self.version = "0.1"

    def status(self):
        return {
            "agent": self.name,
            "version": self.version,
            "status": "Готов к работе"
        }


agent = IDAgent()