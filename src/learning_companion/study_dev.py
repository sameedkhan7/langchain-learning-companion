import sys

from learning_companion.chain import ConfigurationError, get_study_chain


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python -m learning_companion.study_dev "your question"')
        return 2
    question = " ".join(sys.argv[1:])
    try:
        answer = get_study_chain().invoke({"question": question, "history": []})
    except ConfigurationError as error:
        print(error)
        return 1
    print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
