#this is the file that handles our database connection 
import os
import dotenv
from sqlalchemy import create_engine

def database_connection_url():
    dotenv.load_dotenv()    #Loads environment variables from a .env file into the environment

    return os.environ.get("POSTGRES_URI")   #POSTGRES_URI contains the connection URL for the database

engine = create_engine(database_connection_url(), pool_pre_ping=True)
