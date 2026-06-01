from logic import *

AKnight = Symbol("A is a Knight")
AKnave = Symbol("A is a Knave")

BKnight = Symbol("B is a Knight")
BKnave = Symbol("B is a Knave")

CKnight = Symbol("C is a Knight")
CKnave = Symbol("C is a Knave")

AEitherKnightOrKnave = And(
    Or(AKnight, AKnave),
    Not(And(AKnight, AKnave)),
)

BEitherKnightOrKnave = And(
    Or(BKnight, BKnave),
    Not(And(BKnight, BKnave)),
)

CEitherKnightOrKnave = And(
    Or(CKnight, CKnave),
    Not(And(CKnight, CKnave)),
)

# Puzzle 0
# A says "I am both a knight and a knave."
ASentence0 = And(AKnight, AKnave)
knowledge0 = And(
    AEitherKnightOrKnave,
    Or(
        And(AKnight, ASentence0),
        And(AKnave, Not(ASentence0)),
    ),
)

# Puzzle 1
# A says "We are both knaves."
# B says nothing.
ASentence1 = And(AKnave, BKnave)
knowledge1 = And(
    AEitherKnightOrKnave,
    BEitherKnightOrKnave,
    Or(
        And(AKnight, ASentence1),
        And(AKnave, Not(ASentence1)),
    ),
)

# Puzzle 2
# A says "We are the same kind."
# B says "We are of different kinds."
ASentence2 = Or(
    And(AKnight, BKnight),
    And(AKnave, BKnave),
)
BSentence2 = Or(
    And(AKnight, BKnave),
    And(AKnave, BKnight),
)
knowledge2 = And(
    AEitherKnightOrKnave,
    BEitherKnightOrKnave,
    Or(
        And(AKnight, ASentence2),
        And(AKnave, Not(ASentence2)),
    ),
    Or(
        And(BKnight, BSentence2),
        And(BKnave, Not(BSentence2)),
    ),
)

# Puzzle 3
# A says either "I am a knight." or "I am a knave.", but you don't know which.
# B says "A said 'I am a knave'."
# B says "C is a knave."
# C says "A is a knight."
ASaidKnave = Symbol("A said 'I am a knave'.")
ASaidKnight = Symbol("A said 'I am a knight'.")
ASentence3 = Or(
    And(ASaidKnave, AKnave),
    And(ASaidKnight, AKnight),
)
CSentence3 = AKnight

knowledge3 = And(
    AEitherKnightOrKnave,
    BEitherKnightOrKnave,
    CEitherKnightOrKnave,
    Or(ASaidKnave, ASaidKnight),
    Not(And(ASaidKnave, ASaidKnight)),
    Or(
        And(AKnight, ASentence3),
        And(AKnave, Not(ASentence3)),
    ),
    Or(
        And(BKnight, ASaidKnave, CKnave),
        And(BKnave, Not(ASaidKnave), Not(CKnave)),
    ),
    Or(
        And(CKnight, CSentence3),
        And(CKnave, Not(CSentence3)),
    ),
)


def main():
    symbols = [AKnight, AKnave, BKnight, BKnave, CKnight, CKnave]
    puzzles = [
        ("Puzzle 0", knowledge0),
        ("Puzzle 1", knowledge1),
        ("Puzzle 2", knowledge2),
        ("Puzzle 3", knowledge3)
    ]
    for puzzle, knowledge in puzzles:
        print(puzzle)
        if len(knowledge.conjuncts) == 0:
            print("    Not yet implemented.")
        else:
            for symbol in symbols:
                if model_check(knowledge, symbol):
                    print(f"    {symbol}")


if __name__ == "__main__":
    main()
