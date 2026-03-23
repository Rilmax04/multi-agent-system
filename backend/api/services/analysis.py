import api.app as app_module


def get_analysis(question: str) -> dict:
    controller = app_module.controller
    if controller is None:
        raise RuntimeError("Контроллер не инициализирован")
    return controller.get_trace(question)