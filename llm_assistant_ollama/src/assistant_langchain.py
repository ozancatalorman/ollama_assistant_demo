from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
import index_tools

# Turns the function into JSON schema format for ollama to use
def func_to_tool(func):
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


weather_tool = func_to_tool(index_tools.get_current_weather)

# In this demo we have only one tool
tools = [weather_tool]


# System prompt for the model
messages = [
    {"role":"system",
             "content":"""You are a function calling AI assistant that uses the data from a tool(get_current_weather) to answer user's questions.
                       """}
]

#Specifiying the LLM
model = OllamaFunctions(
    model="llama3",
    format="json",
    messages=messages,
    temperature=0
)

# Binding tools to the model
model = model.bind_tools(tools=tools)

# Chat function used to create responses from the user inputs with the model
def chat(user_input):
    response = model.invoke(user_input)
    if response.tool_calls:
        # If the model response has a function call, extract function name and arguments
        function_name = response.tool_calls[0]["name"]
        function_arguments = response.tool_calls[0]["args"]
        if function_name == "get_current_weather":
            # Executing the function and using the output to generate a response for the user response
            result = index_tools.get_current_weather(**function_arguments)
            prompt = PromptTemplate.from_template("""User's question{user_input}
                            Give me an answer with including this information {information} but do not use any tool for this operation""")
            chain = prompt | model | StrOutputParser()
            final_response = chain.invoke({"user_input": user_input, "information": result})
            # It can be returned as a structured string by us instead of making the model generate a response based on the function output. As below:
            # final_resonse = f"The current weather in {result["location"]} is {result["weather_condition"].lower()} with a temperature of {result["temperature"]} degree {result["unit"]}."
            return final_response
        return f"Unknown function: {function_name}"
    else:
        # If no function call return the response
        return response.content


# Loop for interacting with the model
while True:
    user_input = input("User: ")
    response = chat(user_input)
    print("Assistant:", response)

