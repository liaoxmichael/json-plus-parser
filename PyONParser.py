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

YOUR_NAME_HERE = "Michael Liao"

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
    P = {                       // production numbers
        S --> O                 // 1
        O --> { P }             // 2

        P --> K : V             // 3
        P --> P, P              // 4
        P --> ε                 // 5

        K --> (STR)             // 6

        V --> (BOOL)            // 7
        V --> (INT)             // 8
        V --> (FLOAT)           // 9
        V --> (STR)             // 10
        V --> O                 // 11
        V --> L                 // 12

        L --> [ I ]             // 13

        I --> V                 // 14
        I --> I, I              // 15
        I --> ε                 // 16
    }
)

3. Extend the Standard:
We now define a grammar G' = (V', ∑', S, P') where:
V' = V ∪ {T( for seT), E(lement of a Set), C(omplex)}
P' = P ∪ {
    V --> C                     // 17
    V --> T                     // 18

    T --> { E }                 // 19

    E --> (STR)                 // 20
    E --> (INT)                 // 21
    E --> (FLOAT)               // 22
    E --> C                     // 23
    E --> E, E                  // 24
    E --> ε                     // 25

    C --> (FLOAT) + (FLOAT)i    // 26
    C --> (FLOAT) - (FLOAT)i    // 27
    C --> (FLOAT)i              // 28
    C --> -(C)                  // 29
}
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
        EMPTY = 0
        KEY_VALUE = 1
    
    value: tuple

    def __init__(self, status: PairType, value = None):
        self.status = status
        self.value = value

class ParsedListItem(ParsedGeneric):
    """Utility class for determining the result of parse_item()."""
    class ListItemType(IntEnum):
        EMPTY = 0
        VALUE = 1
    
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
    Parses a file and returns a representative Python dictionary if the file is valid JSON, None otherwise.
    Handles production 1: S --> O.
    """
    with open(filepath, "r") as file:
        tokens = tokenize_file(file)
        # early return; all objects need to begin/end with curly braces
        if tokens[0] != '{' or tokens[-1] != '}':
            return None
        return parse_object(tokens)[0] # all subsequent function calls always return the parse result, then the list of tokens; so we need to pull out the first item in the tuple

def match(current_tokens: list, token: str) -> tuple[bool, list]:
    """Matches the current symbol in input and advances it."""
    if current_tokens[0] == token:
        return True, current_tokens[1:]
    return False, current_tokens

# need to define custom match functions for each high-level terminal
# using None as a sentinel value for failure; False could be a valid value from match_bool()
def match_bool(current_tokens: list) -> tuple[bool | None, list]:
    """Matches a (BOOL) and advances the input."""
    if current_tokens[0] == 'true' or current_tokens[0] == 'false':
        return str_to_bool(current_tokens[0]), current_tokens[1:]
    return None, current_tokens

# this one needs a custom type conversion function
def str_to_bool(string: str) -> bool | None:
    """Converts a string to a boolean."""
    if string.lower() == 'true':
        return True
    elif string.lower() == 'false':
        return False
    
    return None

def match_int(current_tokens: list) -> tuple[int | None, list]:
    """Matches an (INT) and advances the input."""
    try:
        return int(current_tokens[0]), current_tokens[1:]
    except ValueError:
        return None, current_tokens
    
def match_float(current_tokens: list) -> tuple[float | None, list]:
    """Matches a (FLOAT) and advances the input."""
    try:
        return float(current_tokens[0]), current_tokens[1:]
    except ValueError:
        return None, current_tokens
    
def match_str(current_tokens: list) -> tuple[str | None, list]:
    """Matches a (STR) and advances the input."""
    if current_tokens[0][0] == '"' or current_tokens[0][0] == "'":
        if current_tokens[0][0] == current_tokens[0][-1]:
            return current_tokens[0][1:-1], current_tokens[1:] # funky notation to slice off quote ends here
    return None, current_tokens

def match_complex(current_tokens: list) -> tuple[complex | None, list]:
    """Matches a (COMPLEX) and advances the input."""
    # last thing should be i
    if current_tokens[0][-1] != 'i': # early termination
        return None, current_tokens

    j_token = current_tokens[0][:-1] + 'j' # Python's complex wants it to be j, so replace it
    
    

match_high_level_terminals_list = [
    match_bool,
    match_int,
    match_float,
    match_str
]

# defining individual parse nonterminal functions for recursive descent
# all return True if they successfully parse the given tokens, None otherwise
def parse_object(current_tokens: list) -> tuple[dict | None, list]:
    """
    Handles production 2: O --> { P }
    Technically also handles production 4 in a loop: P --> P, P
    """
    matched, next_tokens = match(current_tokens, '{')
    if not matched:
        return None, current_tokens

    # looping and finding pairs until we terminate - if only one pair, production 2; if multiple pairs, production 4
    matched = True
    pairs = {}
    while matched and len(next_tokens) > 0:
        pair, next_tokens = parse_pair(next_tokens)
        if pair is not None:
            if pair.status == ParsedPair.PairType.KEY_VALUE:
                pairs[pair.value[0]] = pair.value[1]
            matched, next_tokens = match(next_tokens, ',')
            # if matched is False, no more pairs
            # possible to have trailing comma
        else:
            break # if pair is None, we're done - no more things to parse
    
    matched, next_tokens = match(next_tokens, '}') # check for closing brace

    if not matched:
        return None, current_tokens
    
    # else object should be valid
    return pairs, next_tokens

def parse_pair(current_tokens: list) -> tuple[ParsedPair | None, list]:
    """
    Returns a ParsedPair object if the pair is successfully parsed. Else, returns None.
    Handles productions 3, 5: P --> K : V | ε
    """
    if len(current_tokens) == 0: # production 5
        return ParsedPair(ParsedPair.PairType.EMPTY), current_tokens[1:]
    
    # production 4 - handled in loop in parse_object()

    # production 3
    elif current_tokens[1] == ':':
        key, next_tokens = parse_key(current_tokens)
        colon_status, next_tokens = match(next_tokens, ':')
        value, next_tokens = parse_value(next_tokens)
        
        if (key and colon_status and value):
            return ParsedPair(ParsedPair.PairType.KEY_VALUE, (key, value)), next_tokens
    
    return None, current_tokens

def parse_key(current_tokens: list) -> tuple[str | None, list]:
    """Handles production 6: K --> (STR)"""
    return match_str(current_tokens)

def parse_list(current_tokens: list) -> list | None:
    """
    Handles production 13: L --> [ I ]
    Technically also handles production 15 in a loop: I --> I, I
    """
    matched, next_tokens = match(current_tokens, '[')
    if not matched:
        return None, current_tokens
    
    # looping and finding list items until we terminate - if only one item, production 13; if multiple, production 15
    matched = True
    items = []
    while matched and len(next_tokens) > 0:
        item, next_tokens = parse_item(next_tokens)
        if item is not None:
            if item.status == ParsedListItem.ListItemType.VALUE:
                items.append(item.value)
            matched, next_tokens = match(next_tokens, ',')
            # if matched is False, no more items
            # possible to have trailing comma
        else:
            break # if pair is None, we're done - no more things to parse

    matched, current_tokens = match(next_tokens, ']')

    if not matched:
        return None, current_tokens
    
    # else items should be valid
    return items, current_tokens

def parse_item(current_tokens: list) -> tuple[ParsedListItem | None, list]:
    """Handles productions 14, 16: I --> V | ε"""
    if len(current_tokens) == 0: # production 16
        return ParsedListItem(ParsedListItem.ListItemType.EMPTY), current_tokens[1:]

    # production 15 - handled in loop in parse_list()
   
    # production 14
    value, next_tokens = parse_value(current_tokens)
    if value is not None:
        return ParsedListItem(ParsedListItem.ListItemType.VALUE, value), next_tokens
    
    return None, current_tokens

def parse_value(current_tokens: list) -> tuple[bool | int | float | str | dict | list | None, list]:
    """Handles productions 7, 8, 9, 10, 11, 12: V --> (BOOL) | (INT) | (FLOAT) | (STR) | O | L"""

    # productions 7-10
    for match_fn in match_high_level_terminals_list:
        is_terminal, next_tokens = match_fn(current_tokens)
        if is_terminal is not None:
            return is_terminal, next_tokens
    
    # production 11
    object, next_tokens = parse_object(current_tokens)
    if object is not None:
        return object, next_tokens
    
    # production 12
    list, next_tokens = parse_list(current_tokens)
    if list is not None:
        return list, next_tokens
    
    return None, current_tokens

def main():
    ap = argparse.ArgumentParser(description=(DESCRIPTION + f"\nBy: {YOUR_NAME_HERE}"))
    ap.add_argument('file_name', action='store', help='Name of the JSON file to read.')
    args = ap.parse_args()

    file_name = args.file_name
    local_dir = os.path.dirname(__file__)
    file_path = os.path.join(local_dir, file_name)

    # file_path = "Sample JSON Input Files/easy_test.json" # debug
    # file_path = "Sample JSON Input Files/medium_test.json" # debug

    dictionary = parse_file(file_path)

    print('DICTIONARY:')
    print(dictionary)

if __name__ == "__main__":
    main()