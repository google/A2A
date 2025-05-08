# server.py
import sqlite3
import psycopg2
import os

from loguru import logger
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()

# Create an MCP server
mcp = FastMCP("Demo")


@mcp.tool()
def query_data(sql: str) -> str:
    """Execute SQL queries safely"""
    logger.info(f"Executing SQL query: {sql}")
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    try:
        cursor = conn.cursor()
        cursor.execute(sql)  # Execute the query
        if sql.strip().lower().startswith("select"):  # Check if it's a SELECT query
            result = cursor.fetchall()  # Fetch all rows for SELECT queries
            return "\n".join(str(row) for row in result)  # Format the result as a string
        else:
            conn.commit()  # Commit for non-SELECT queries
            return "Query executed successfully."
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return f"Error: {str(e)}"
    finally:
        conn.close()


@mcp.prompt()
def example_prompt(code: str) -> str:
    return f"Please review this code:\n\n{code}"


if __name__ == "__main__":
    print("Starting server...")
    # Initialize and run the server
    mcp.run(transport="stdio")