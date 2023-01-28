"""
    前体消息构造
"""

def ExceptionBuilder(excMsg:str) -> str:
    return excMsg.split("\n")[-2]