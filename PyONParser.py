#!/usr/bin/python3
"""
Michael Liao
CSC 374
PyON Parser
"""
DESCRIPTION = '''
A homebrew JSON parser which extends standard JSON with sets and complex numbers.
'''

import argparse
import os.path
import sys
import re
from enum import IntEnum

YOUR_NAME_HERE = "Michael Liao" # Replace this with your name.

"""
0. High-Level Terminals
(BOOL) --> true | false
(INT) --> any integer
(FLOAT) --> any float
(STR) --> any string (wrapped between two quotes, which can be single (') or double (") quotes)

1. Defining a Grammar for JSON
G = (
    V = {
        S(tart),
        O(bject),
        L(ist),
        I(tem of List),
        K(ey),
        V(alue),
        P(air)
    },
    ∑ = {
        :, 
        [, 
        ], 
        ,, // note that this is a comma
        (BOOL), 
        (INT), 
        (FLOAT), 
        (STR)
    },
    S = O,
    P = {               // production numbers
        S --> O         // 1
        O --> { P }     // 2

        P --> K : V     // 3
        P --> P, P      // 4
        P --> P,        // 5 < ??
        P --> ε         // 6

        K --> (STR)     // 7

        V --> (BOOL)    // 8
        V --> (INT)     // 9
        V --> (FLOAT)   // 10
        V --> (STR)     // 11
        V --> O         // 12
        V --> L         // 13

        L --> [ I ]     // 14
        L --> [ I, ]    // 15 < ??

        I --> V         // 16
        I --> I, I      // 17
        I --> ε         // 18
    }
)
"""

class ParsedGeneric():
    """A generic class for parsed objects."""
    status: IntEnum
    value: any

    def __init__(self, status: int, value: any):
        self.status = status
        self.value = value

    def __str__(self):
        return f"Status: {self.status}, Value: {self.value}"
    
    def __repr__(self):
        return f"Status: {self.status}, Value: {self.value}"
    
class ParsedPair(ParsedGeneric):
    """Utility class for determining the result of parse_pair()."""
    class PairType(IntEnum):
        KEY_VALUE = 1
        MULTI_PAIR = 2
        EMPTY = 3
    
    value: tuple

    def __init__(self, status: PairType, value = None):
        self.status = status
        self.value = value

class ParsedListItem(ParsedGeneric):
    """Utility class for determining the result of parse_item()."""
    class ListItemType(IntEnum):
        VALUE = 1
        MULTI_ITEM = 2
        EMPTY = 3
    
    value: tuple

    def __init__(self, status: ListItemType, value = None):
        self.status = status
        self.value = value

def tokenize_file(file) -> list:
    """Turns a file into a list of potentially-meaningful tokens."""
    tokens = []
    for line in file:
        stripped = line.strip() # removes leading/trailing whitespace
        tokenized = re.split(r'({|}|:|,|\[|\])', stripped) # separates out all the special characters in ∑
        
        # gets rid of extra whitespace w/ strip(), ignores empty tokens
        tokens += [token.strip() for token in tokenized if token.strip() != '']
    # print('\n'.join(tokens)) # debug
    return tokens

def parse_file(filepath: str) -> dict | None: # this also functions as our parse_start function
    """
    Parses a file and returns a representative Python dictionary if the file is syntactically correct, None otherwise.
    Handles production 1: S --> O.
    """
    with open(filepath, "r") as file:
        tokens = tokenize_file(file)
        # early return; all objects need to begin/end with curly braces
        if tokens[0] != '{' or tokens[-1] != '}':
            return None
        
        return parse_object(tokens)

def match(current_tokens: list, token: str) -> bool:
    """Matches the current symbol in input and advances it."""
    if current_tokens[0] == token:
        current_tokens.pop(0)
        return True
    return False

# need to define custom match functions for each high-level terminal
# using None as a sentinel value for failure; False could be a valid value from match_bool()
def match_bool(current_tokens: list) -> bool | None:
    """Matches a (BOOL) and advances the input."""
    if current_tokens[0] == 'true' or current_tokens[0] == 'false':
        return str_to_bool(current_tokens.pop(0))
    return None

# this one needs a custom type conversion function
def str_to_bool(string: str) -> bool | None:
    """Converts a string to a boolean."""
    if string.lower() == 'true':
        return True
    elif string.lower() == 'false':
        return False
    
    return None

def match_int(current_tokens: list) -> int | None:
    """Matches an (INT) and advances the input."""
    try:
        int(current_tokens[0])
        return int(current_tokens.pop(0))
    except ValueError:
        return None
    
def match_float(current_tokens: list) -> float | None:
    """Matches a (FLOAT) and advances the input."""
    try:
        float(current_tokens[0])
        return float(current_tokens.pop(0))
    except ValueError:
        return None
    
def match_str(current_tokens: list) -> str | None:
    """Matches a (STR) and advances the input."""
    if current_tokens[0][0] == '"' or current_tokens[0][0] == "'":
        if current_tokens[0][0] == current_tokens[0][-1]:
            return current_tokens.pop(0)
    return None

# defining individual parse nonterminal functions for recursive descent
# all return True if they successfully parse the given tokens, None otherwise
def parse_object(current_tokens: list) -> dict | None:
    """Handles production 2: O --> { P }"""
    if not match(current_tokens, '{'):
        return None
    pair = parse_pair(current_tokens)
    if not match(current_tokens, '}'):
        return None
    
    if pair:
        if pair.status == ParsedPair.PairType.KEY_VALUE:
            return {pair.value[0]: pair.value[1]}
        elif pair.status == ParsedPair.PairType.MULTI_PAIR:
            return {pair.value[0], pair.value[1]}
        else:
            return {}
    
    return None

def parse_pair(current_tokens: list) -> ParsedPair | None:
    """
    Returns a ParsedPair object if the pair is successfully parsed. Else, returns None.
    Handles productions 3, 4, 5: P --> K : V | P, P | ε
    """
    if len(current_tokens) == 0: # production 5
        return ParsedPair(ParsedPair.PairType.EMPTY)
    
    # production 4
    if current_tokens[1] == ',': # looking ahead to see if we have a comma
        comma_status = True
        pair1 = parse_pair(current_tokens)
        if not match(current_tokens, ','):
            comma_status = False
        pair2 = parse_pair(current_tokens)
        
        if (pair1 and comma_status and pair2):
            return ParsedPair(ParsedPair.PairType.MULTI_PAIR, (pair1.value, pair2.value))

    # production 3
    elif current_tokens[1] == ':':
        colon_status = True
        key = parse_key(current_tokens)
        if not match(current_tokens, ':'):
            colon_status = False
        value = parse_value(current_tokens)
        
        if (key and colon_status and value):
            return ParsedPair(ParsedPair.PairType.KEY_VALUE, (key, value))
    
    return None

def parse_key(current_tokens: list) -> str | None:
    """Handles production 6: K --> (STR)"""
    return match_str(current_tokens)

def parse_list(current_tokens: list) -> list | None:
    """Handles production 13: L --> [ I ]"""
    if not match(current_tokens, '['):
        return None
    item = parse_item(current_tokens)
    if not match(current_tokens, ']'):
        return None
    
    if item:
        if item.status == ParsedListItem.ListItemType.VALUE:
            return [item.value]
        elif item.status == ParsedListItem.ListItemType.MULTI_ITEM:
            return [item.value[0], item.value[1]]
        else:
            return []
        
    return None

def parse_item(current_tokens: list) -> ParsedListItem | None:
    """Handles productions 14, 15, 16: I --> V | I, I | ε"""
    if len(current_tokens) == 0: # production 16
        return ParsedListItem(ParsedListItem.ListItemType.EMPTY)

    # production 15
    if current_tokens[1] == ',': # looking ahead to see if we have a comma
        comma_status = True
        item1 = parse_item(current_tokens)
        if not match(current_tokens, ','):
            comma_status = False
        item2 = parse_item(current_tokens)

        if (item1 and comma_status and item2):
            return ParsedListItem(ParsedListItem.ListItemType.MULTI_ITEM, (item1.value, item2.value))   
   
    # production 14
    # elif current_tokens[0] != ']': # looking ahead to see if single value
    value = parse_value(current_tokens)
    if value:
        return ParsedListItem(ParsedListItem.ListItemType.VALUE, value)
    
    return None

    
def parse_value(current_tokens: list) -> bool | int | float | str | dict | list | None:
    """Handles productions 7, 8, 9, 10, 11, 12: V --> (BOOL) | (INT) | (FLOAT) | (STR) | O | L"""
    
    # production 7
    is_bool = match_bool(current_tokens)
    if is_bool is not None:
        return is_bool
    
    # production 8
    is_int = match_int(current_tokens)
    if is_int is not None:
        return is_int
    
    # production 9
    is_float = match_float(current_tokens)
    if is_float is not None:
        return is_float
    
    # production 10
    is_str = match_str(current_tokens)
    if is_str is not None:
        return is_str
    
    # production 11
    object = parse_object(current_tokens)
    if object:
        return object
    
    # production 12
    list = parse_list(current_tokens)
    if list:
        return list
    
    return None

def main():
    ap = argparse.ArgumentParser(description=(DESCRIPTION + f"\nBy: {YOUR_NAME_HERE}"))
    ap.add_argument('file_name', action='store', help='Name of the JSON file to read.')
    args = ap.parse_args()

    file_name = args.file_name
    local_dir = os.path.dirname(__file__)
    file_path = os.path.join(local_dir, file_name)

    dictionary = parse_file(file_path)

    print('DICTIONARY:')
    print(dictionary)

if __name__ == "__main__":
    main()