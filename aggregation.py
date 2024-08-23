import argparse
import json
from pathlib import Path

VERTIFICATION_STRATEGIES = [
    "human_single_false_or_unsure",
    "human_majority_vote"
]


def read_qa_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    run_id = data['run_id']
    qa_pairs = data['qa_pairs']
    return run_id, qa_pairs


def verify_single_false_or_unsure(qa_pairs):
    verified_by_adf = True
    for qa_pair in qa_pairs:
        response = qa_pair['response_human']['response']
        if response == '?' or response == 'n':
            verified_by_adf = False
            break
    return verified_by_adf


def verify_majority_vote(qa_pairs):
    num_false = 0
    for qa_pair in qa_pairs:
        response = qa_pair['response_human']['response']
        if response == 'n' or response == '?':
            num_false += 1

    return num_false <= (len(qa_pairs) // 2)



def verify_post(run_id, qa_pairs, method="human_single_false_or_unsure"):
    if method == "human_single_false_or_unsure":
        return verify_single_false_or_unsure(qa_pairs)
    elif method == "human_majority_vote":
        return verify_majority_vote(qa_pairs)
    else:
        raise ValueError(f"Invalid verification method: '{method}', must be one of {VERTIFICATION_STRATEGIES}.")


def main():
    parser = argparse.ArgumentParser(description="A basic argparse example.")
    parser.add_argument('file', type=str, help='The path to a file containing the atomic questions/response pairs', default=None)
    parser.add_argument('--method', type=str, help='Aggregation method', default="human_single_false_or_unsure", choices=VERTIFICATION_STRATEGIES)
    args = parser.parse_args()

    run_id, qa_pairs = read_qa_file(Path(args.file))

    verified_by_adf = verify_post(run_id, qa_pairs, method=args.method)

    print(f"Verified by ADF: {verified_by_adf}")


if __name__ == "__main__":
    main()
