"""
Michael Liao
CSC 374
PyON Parser
"""

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
        P --> ε         // 5

        K --> (STR)     // 6

        V --> (BOOL)    // 7
        V --> (INT)     // 8
        V --> (FLOAT)   // 9
        V --> (STR)     // 10
        V --> O         // 11
        V --> L         // 12

        L --> [ I ]     // 13

        I --> V         // 14
        I --> I, I      // 15
        I --> ε         // 16
    }
)
"""
import sys
import re

def tokenize_file(file) -> list:
    """Turns a file into a list of potentially-meaningful tokens."""
    tokens = []
    for line in file:
        stripped = line.strip() # removes leading/trailing whitespace
        tokenized = re.split(r'({|}|:|,|\[|\])', stripped) # separates out all the special characters in ∑
        
        # gets rid of extra whitespace w/ strip(), ignores empty tokens
        tokens += [token.strip() for token in tokenized if token.strip() != '']
    print('\n'.join(tokens))
    return tokens

def parse_file(filepath: str) -> dict | False: # this also functions as our parse_start function
    """
    Parses a file and returns True if the file is syntactically correct, False otherwise.
    Handles production 1: S --> O.
    """
    with open(filepath, "r") as file:
        tokens = tokenize_file(file)
        # early return; all objects need to begin/end with curly braces
        if tokens[0] != '{' or tokens[-1] != '}':
            return False
        return parse_object(tokens)

def match(current_tokens: list, token: str) -> bool:
    """Matches the current symbol in input and advances it"""
    if current_tokens[0] == token:
        current_tokens.pop(0)
        return True
    return False

# need to define custom match functions for each high-level terminal
def match_bool(current_tokens: list) -> bool:
    """Matches a (BOOL) and advances the input"""
    if current_tokens[0] == 'true' or current_tokens[0] == 'false':
        current_tokens.pop(0)
        return True
    return False

def match_int(current_tokens: list) -> bool:
    """Matches an (INT) and advances the input"""
    try:
        int(current_tokens[0])
        current_tokens.pop(0)
        return True
    except ValueError:
        return False
    
def match_float(current_tokens: list) -> bool:
    """Matches a (FLOAT) and advances the input"""
    try:
        float(current_tokens[0])
        current_tokens.pop(0)
        return True
    except ValueError:
        return False
    
def match_str(current_tokens: list) -> bool: # wip, needs testing
    """Matches a (STR) and advances the input."""
    if current_tokens[0][0] == '"' or current_tokens[0][0] == "'":
        if current_tokens[0][0] == current_tokens[0][-1]:
            current_tokens.pop(0)
            return True
    return False

# defining individual parse nonterminal functions for recursive descent
# all return True if they successfully parse the given tokens, False otherwise
def parse_object(current_tokens: list) -> bool:
    """Handles production 2: O --> { P }"""
    if not match(current_tokens, '{'):
        return False
    pair_status = parse_pair(current_tokens)
    if not match(current_tokens, '}'):
        return False
    
    return pair_status

def parse_pair(current_tokens: list) -> bool:
    """Handles productions 3, 4, 5: P --> K : V | P, P | ε"""
    if len(current_tokens) == 0: # production 5
        return True
    
    # production 3
    colon_status = True
    key_status = parse_key(current_tokens)
    if not match(current_tokens, ':'):
        colon_status = False
    
    value_status = parse_value(current_tokens)

    # production 4
    comma_status = True
    pair1_status = parse_pair(current_tokens)
    if not match(current_tokens, ','):
        comma_status = False
    pair2_status = parse_pair(current_tokens)

    return (key_status and colon_status and value_status) or (pair1_status and comma_status and pair2_status)

def parse_key(current_tokens: list) -> bool:
    """Handles production 6: K --> (STR)"""
    return match_str(current_tokens)

def parse_list(current_tokens: list) -> bool:
    """Handles production 13: L --> [ I ]"""
    if not match(current_tokens, '['):
        return False
    item_status = parse_item(current_tokens)
    if not match(current_tokens, ']'):
        return False
    return item_status

def parse_item(current_tokens: list) -> bool:
    """Handles productions 14, 15, 16: I --> V | I, I | ε"""
    if len(current_tokens) == 0: # production 16
        return True

    # production 14
    value_status = parse_value(current_tokens)

    # production 15
    comma_status = True
    item1_status = parse_item(current_tokens)
    if not match(current_tokens, ','):
        comma_status = False
    item2_status = parse_item(current_tokens)

    return value_status or (comma_status and item1_status and item2_status)
    
def parse_value(current_tokens: list) -> bool:
    """Handles productions 7, 8, 9, 10, 11, 12: V --> (BOOL) | (INT) | (FLOAT) | (STR) | O | L"""
    # productions 7-10
    if match_bool(current_tokens) or match_int(current_tokens) or match_float(current_tokens) or match_str(current_tokens):
        return True
    # productions 11, 12
    object_status = parse_object(current_tokens)
    list_status = parse_list(current_tokens)

    return object_status or list_status

def main():
    filepath = sys.argv[1]

    if (parse_file(filepath)):
        pass

if __name__ == "__main__":
    main()