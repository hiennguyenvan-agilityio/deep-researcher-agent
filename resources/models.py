from langchain.chat_models import BaseChatModel, init_chat_model


_reason_model = None
_chat_model = None

def initialise_reason_model(model_name: str):
    global _reason_model

    _reason_model = init_chat_model(model=model_name)

def initialise_chat_model(model_name: str):
    global _chat_model

    _chat_model = init_chat_model(model=model_name)


def get_reason_model() -> BaseChatModel:
    if _reason_model is None:
        raise ValueError(
            "Reason model is not initialised. "
            "Call `initialise_reason_model(model_name)` first."
        )

    return _reason_model

def get_chat_model() -> BaseChatModel:
    if _reason_model is None:
        raise ValueError(
            "Chat model is not initialised. "
            "Call `initialise_chat_model(model_name)` first."
        )
    
    return _chat_model
