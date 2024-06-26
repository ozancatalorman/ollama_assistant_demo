import re
import json
from openai import OpenAI
import index_tools

client = OpenAI(base_url='http://localhost:11434/v1', api_key='dolphin-llama3')

# Converts the function into JSON Schema format for API to use
def convert_to_openani_fuction(func):
    return {
        "name": func.__name__,
        "description": func.__doc__,
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "The city, e.g. Istanbul"},
            },
            "required": ["location"],
        },
    }


functions = [
    convert_to_openani_fuction(index_tools.get_current_weather),
]

# Parses the input str to find and extract the function call
def parse_function_call(input_str):
    match = re.search(r'<functioncall>(.*?)</functioncall>', input_str, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return None
    return None

# Sends the messages to the model with API for generating a response
def chat(messages):
    # System prompt for the assistant to handle the function call
    system_message = f"""
    You are an AI Assistant that is an expert in following instructions and your name is ReefAssistant1.0. You will engage in conversation and provide information to the best of your knowledge. You have a set of functions you can use but only use if needed.
    You have access to these functions:
    {json.dumps(functions, indent=2)}

    If the user's input contains "what is the weather" or similar, extract the necessary information (location) from the input and generate a function call in the following format:
    <functioncall>{{"name": "get_current_weather","arguments": {{"location": "user_provided_location"}}}}</functioncall>
    Make sure to replace the placeholders (user_provided_location) with the actual location information provided by the user, and ensure that the entire function call is on a single line.
    After generating the function call, execute the function and get the relevant weather data from the function and use it in your response to answer the user's question.
    If you use the function (get_current_weather) for answering at the end of the response add "Hey REEFer" for just one time.

    Example: Tell the user how is the weather in the location user provided
"""
    # Inserting the system message into messages and passing them to the model
    messages.insert(0, {"role": "system", "content": system_message})
    response = client.chat.completions.create(model="dolphin-llama3", messages=messages, functions=functions,
                                              temperature=0)
    # Taking the content of the response and parsing it to find a function call if there is any
    message_content = response.choices[0].message.content
    function_call = parse_function_call(message_content)
    if function_call:
        # If there is a function call, extract function name and arguments
        function_name = function_call["name"]
        function_arguments = function_call["arguments"]
        if function_name == "get_current_weather":
            # Execute the function and push back the output to the model for it to generate a final response for the user
            data = index_tools.get_current_weather(**function_arguments)
            result = f"Relevant content:\n{data}\n\nUser arguments: {function_arguments}"
            content = chat([{"role": "user", "content": result}])
            # Adding the system message to the conversation history
            conversation_history.append({"role": "system", "content": content})
            return content
        else:
            return f"Unknown function: {function_name}"
    # If no function call return the response
    return message_content


conversation_history = []
# Loop for interacting with the model
while True:
    user_input = input("User: ")
    # Only using the last message in the conversation history
    conversation_history = conversation_history[-1:]
    conversation_history.append({"role": "user", "content": user_input})
    response = chat(conversation_history)
    conversation_history.append({"role": "assistant", "content": response})
    print("Assistant:", response)

