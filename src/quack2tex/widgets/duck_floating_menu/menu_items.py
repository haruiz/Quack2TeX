menu_items = [
    {
        "icon": ":icons/tex.png",
        "value": "tex",
        "tooltip": "Image to LaTeX",
        "data": {
            "system_instruction": "Provide the response in markdown format.",
            "guidance_prompt": "Convert the content in the image to LaTeX code. If there is an equation, generate the "
            "corresponding LaTeX code and provide a brief explanation of the equation. "
            "Make sure to wrap the LaTeX code using markdown syntax.",
        },
    },
    {
        "icon": ":icons/cooking.png",
        "value": "cooking",
        "tooltip": "How to cook?",
        "data": {
            "system_instruction": "Provide the response in markdown format.",
            "guidance_prompt": "Analyze the image to identify the recipe. Detail the cooking steps, listing all "
            "necessary ingredients with precise measurements, and explain the process.",
        },
    },
    {
        "icon": ":icons/painter.png",
        "value": "painter",
        "tooltip": "Describe the picture",
        "data": {
            "system_instruction": "Provide the response in markdown format.",
            "guidance_prompt": "Offer a detailed description of the image. Identify and describe the objects, "
            "elements, and any significant features present.",
        },
    },
    {
        "icon": ":icons/programmer.png",
        "value": "programmer",
        "tooltip": "Explain the code",
        "data": {
            "system_instruction": "Provide the response in markdown format.",
            "guidance_prompt": "Examine the code in the image. Identify the programming language, describe the code's "
            "functionality, and explain its purpose or the problem it solves.",
        },
    },
    # {
    #     "icon": ":icons/translate.png",
    #     "value": "translate",
    #     "tooltip": "Translate the text",
    #     "data": {
    #         "system_instruction": "Provide the response in markdown format.",
    #         "guidance_prompt": "Translate the text in the image into Spanish. Ensure the translation is accurate and "
    #                            "maintains the original meaning."
    #     }
    # },
    {
        "icon": ":icons/map.png",
        "value": "map",
        "tooltip": "Where is this?",
        "data": {
            "system_instruction": "Provide the response in markdown format.",
            "guidance_prompt": "Identify the location depicted in the image. Provide a brief description of the "
            "place, including interesting facts or historical details.",
        },
    },
    # {
    #     "icon": ":icons/history.png",
    #     "value": "history",
    #     "tooltip": "History",
    #     "data": None
    # },
    {"icon": ":icons/close.png", "value": "close", "tooltip": "Close", "data": None},
]
