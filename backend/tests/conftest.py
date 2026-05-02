import os


def pytest_sessionstart(session):
    os.environ["BS_DETECTOR_DISABLE_LLM"] = "1"
