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
import re
import os

# Initialize FastMCP server
mcp = FastMCP("test")

# Get absolute path to data.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")


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


def extract_keywords(query: str) -> list[str]:
    """Extract meaningful keywords from a user query.
    
    Args:
        query (str): The user's query string
    
    Returns:
        list[str]: List of extracted keywords
    """
    # Common stopwords to ignore
    stopwords = {
        'what', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'about', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
        'how', 'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
        'too', 'very', 'can', 'will', 'just', 'should', 'do', 'does', 'did',
        'tell', 'me', 'please', 'you', 'i', 'my', 'your', 'it', 'its', 'this',
        'that', 'these', 'those', 'and', 'or', 'but', 'if', 'because'
    }
    
    # Convert to lowercase and remove punctuation
    query_lower = query.lower()
    # Keep only alphanumeric characters and spaces
    query_clean = re.sub(r'[^a-z0-9\s]', ' ', query_lower)
    
    # Split into words
    words = query_clean.split()
    
    # Filter out stopwords and very short words
    keywords = [word for word in words if word not in stopwords and len(word) > 2]
    
    return keywords


def calculate_match_score(query_keywords: list[str], db_question: str) -> float:
    """Calculate how well a database question matches the query keywords.
    
    Args:
        query_keywords (list[str]): Keywords extracted from user query
        db_question (str): A question from the database
    
    Returns:
        float: Match score (0.0 to 1.0)
    """
    if not query_keywords:
        return 0.0
    
    db_question_lower = db_question.lower()
    matches = 0
    
    for keyword in query_keywords:
        if keyword in db_question_lower:
            matches += 1
    
    # Return percentage of keywords that matched
    return matches / len(query_keywords)


@mcp.tool()
async def smart_query(user_query: str) -> str:
    """Gets answers from the knowledge base.
    
    This function:
    1. Extracts keywords from the user's query
    2. Searches for matching questions in the database
    3. Returns the best matching answers
    
    Args:
        user_query (str): The user's natural language question
    
    Returns:
        str: Formatted answer(s) from the database, or an error message if no match found
    """
    # Connect to the data.db file
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    result = ""
    
    try:
        # Extract keywords from user query
        keywords = extract_keywords(user_query)
        
        if not keywords:
            return "I couldn't identify any meaningful keywords in your query. Please try rephrasing your question."
        
        # Get all questions from database
        cursor.execute("SELECT * FROM main")
        rows = cursor.fetchall()
        
        # Calculate match scores for each database entry
        matches = []
        for row in rows:
            score = calculate_match_score(keywords, row['question'])
            if score > 0:
                matches.append({
                    'question': row['question'],
                    'answer': row['answer'],
                    'score': score
                })
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        if not matches:
            # Fallback: try partial matching with LIKE
            cursor.execute("SELECT * FROM main WHERE question LIKE ? OR answer LIKE ?", 
                            (f'%{keywords[0]}%', f'%{keywords[0]}%'))
            fallback_rows = cursor.fetchall()
            if fallback_rows:
                result += f"Based on keyword '{keywords[0]}':\n"
                for row in fallback_rows:
                    result += f"Q: {row['question']}\nA: {row['answer']}\n--------\n"
            
            if not result:
                result = f"No matches found for your query. Keywords searched: {', '.join(keywords)}"
        else:
            # Return top 3 matches
            for i, match in enumerate(matches[:3], 1):
                result += f"Match {i} (Relevance: {match['score']*100:.0f}%):\n"
                result += f"Q: {match['question']}\n"
                result += f"A: {match['answer']}\n--------\n"
        
    except sqlite3.Error as e:
        result = f"Database error: {str(e)}"
    finally:
        conn.close()
    
    return result


@mcp.tool()
async def query_keywords() -> str:
    """Gets all keywords for search use in Knowledge Base.
    
    Args:
        none

    Returns:
        Str: query result
    """
    # Connect to the data.db file
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    cursor = conn.cursor()
    result = ""

    try:
        cursor.execute("SELECT * FROM main")
        rows = cursor.fetchall()
        # Convert each row object to a standard dictionary
        for row in rows:
            result += row['question'] + ","

    except sqlite3.Error as e:
        # Return an error message if the query fails
        result = f"error: {str(e)}"
    finally:
        conn.close()

    return result


@mcp.tool()
async def query_db(keyword: str) -> str:
    """Gets answer from Knowledge Base using keywords from query_keywords.
    
    Args:
        keyword (str): search keyword

    Returns:
        Str: query result
    """
    # Connect to the data.db file
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    result = ""

    try:
        cursor.execute("SELECT * FROM main where question LIKE ?", ('%'+keyword+'%',))
        rows = cursor.fetchall()
        # Convert each row object to a standard dictionary
        for row in rows:
            result += row['question'] + ", " + row['answer'] + "--------\n"

    except sqlite3.Error as e:
        # Return an error message if the query fails
        result = f"error: {str(e)}"
    finally:
        conn.close()

    return result


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")