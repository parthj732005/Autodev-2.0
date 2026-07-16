def log(message: str):
    with open("app/logs/run.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")
