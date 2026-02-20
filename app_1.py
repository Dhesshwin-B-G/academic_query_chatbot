import sys
sys.stdout.reconfigure(encoding='utf-8')
from pymongo import MongoClient
import certifi
import datetime
from datetime import datetime
import os 
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
#importing new libraries 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel #maintain the structure of the data being sent to the API

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY") #loading the API key from the .env file
mongodb_uri = os.getenv("MONGODB_URI") #loading the MongoDB URI from the .env file

if not mongodb_uri:
    raise ValueError("MongoDB URI missing")

client = MongoClient(
    mongodb_uri,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000
) #creating a MongoDB client using the URI
db=client["chatbot_db"] #selecting the database
collection=db["users"] #selecting the collection
 
app=FastAPI() #creating a FastAPI instance

class chat_request(BaseModel):
    user_id: str
    question: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allowing all origins for CORS
    allow_methods=["*"], # Allowing all HTTP methods for CORS
    allow_headers=["*"], # Allowing all headers for CORS
    allow_credentials=True, # Allowing credentials for CORS 
)

#creating a prompt template for the assistant to answer questions about fitness and health.
'''The system message sets the context for the assistant, 
and the human message is where the user's question will be inserted.'''

prompt_gen=ChatPromptTemplate.from_messages([
    ("system","Act as a knowledgeable Study Bot that explains academic concepts clearly with examples and structured steps. Provide honest, practical career guidance, skill-building advice, and learning roadmaps tailored to the student’s interests."),
    ("placeholder","{history}"),
    ("human","{question}")
])


llm=ChatGroq(api_key=groq_api_key,model="openai/gpt-oss-20b")
chain=prompt_gen | llm



def get_user_history(user_id):
    """Fetches the conversation history for a given user ID from the MongoDB collection."""
    chat = collection.find({"user_id": user_id}).sort("timestamp", 1) # Fetching the conversation history sorted by timestamp
    history=[]
    
    for i in chat:
        if i["role"] == "user":
            history.append(("human", i["question"]))
        else:
            history.append(("assistant", i["response"]))
    return history

@app.get("/")
def home():
    return {"message": "Welcome to the Study Bot API!"}
@app.post("/ask")
def chat(request: chat_request):
    history=get_user_history(request.user_id) # Fetching the conversation history for the user
    response=chain.invoke({"history": history, "question": request.question}) # Generating
    collection.insert_one({
        "user_id": request.user_id,
        "role": "user",
        "question": request.question, 
        "timestamp": datetime.now(),
        }) #storing the user's question and the assistant's response in the MongoDB collection

    collection.insert_one({
        "user_id": request.user_id,
        "role": "assistant",
        "response": response.content,
        "timestamp": datetime.now(),
    })
    return {"response": response.content} # Returning the assistant's response as a JSON object


