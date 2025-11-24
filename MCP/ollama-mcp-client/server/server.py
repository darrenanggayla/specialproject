# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx",
#     "mcp[cli]",
# ]
# ///

import random
import httpx
from mcp.server.fastmcp import FastMCP
import math
import sqlite3

# Initialize FastMCP server
mcp = FastMCP("test")


@mcp.tool()
async def get_random(max_value: float | None = None) -> float:
    """Generate a random number with 2 decimals.
    If max_value is provided, the number will be in [0, max_value].
    If no max_value, it will generate an unboundedly large number.
    
    Args:
        max_value (float | None): Optional upper limit for the random number.
    
    Returns:
        float: random number rounded to 2 decimal places
    """
    if max_value is None:
        # Pick a large range if no max_value is given
        number = random.uniform(0, 1e12)  
    else:
        number = random.uniform(0, max_value)
    
    return round(number, 2)


@mcp.tool()
async def pow(a: float, b: float) -> float:
    """Calculate a of the power b

    Args:
        a (float): number
        b (float): power

    Returns:
        float: Calculated result
    """
    return math.pow(a, b)


@mcp.tool()
async def random_user(count: int) -> dict:
    """Generates random user data

    Args:
        count (int): returned user count

    Returns:
        dict: user data json as dict
    """
    res = httpx.get(f"https://randomuser.me/api?results={count}&inc=gender,name,email,phone,id")
    res.raise_for_status()
    return res.json()


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")

@mcp.tool()
async def read_db(query: str) -> list[dict]:
    """Run a SQL query on test.sqlite and return the results as a list of rows.

    Args:
        query (str): The SQL query to execute (e.g., "SELECT * FROM questions")

    Returns:
        list[dict]: Query results as a list of rows (each row is a dict column→value)
    """
    conn = sqlite3.connect("test.sqlite")
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        # Convert each row to dict
        result = [dict(row) for row in rows]
    except sqlite3.Error as e:
        result = [{"error": str(e)}]
    finally:
        conn.close()

    return result

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")

@mcp.tool()
async def query_ntust_db(query: str) -> list[dict]:
    """Run a SQL query on the NTUST database (data.db) and return the results.
    The available table is 'questions_and_answers' with columns: id, question, answer.

    Args:
        query (str): The SQL query to execute (e.g., "SELECT * FROM questions_and_answers")

    Returns:
        list[dict]: Query results as a list of rows. Each row is a dictionary mapping column names to values.
    """
    # Connect to the data.db file
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        # Convert each row object to a standard dictionary
        result = [dict(row) for row in rows]
    except sqlite3.Error as e:
        # Return an error message if the query fails
        result = [{"error": str(e)}]
    finally:
        conn.close()

    return result