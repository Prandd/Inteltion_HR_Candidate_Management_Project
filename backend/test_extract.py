from app.extraction import extract_candidate


with open(
    "test_cv.pdf",
    "rb"
) as f:

    data = extract_candidate(
        f.read(),
        "test_cv.pdf"
    )


print(data)