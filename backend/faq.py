def get_answer(question: str):
    with open("data/faq.txt", "r", encoding="utf-8") as f:
        docs = f.readlines()

    for doc in docs:
        if any(word in doc for word in question.split()):
            return doc.strip()

    return None