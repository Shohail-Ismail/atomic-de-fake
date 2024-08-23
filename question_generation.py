import os
import json
import time
from dotenv import load_dotenv
from mistralai import Mistral

# Load API key
load_dotenv()

def question_generation(post_text, client):
    chat_response = client.chat.complete(
        model = model,
        messages = [
            {
                "role": "user",
                "content": f"Generate questions to verify whether the following post is NOT misleading: {post_text}. Return the questions in a short JSON object. Please include at least 5 questions.",
            },
        ],
        response_format = {
            "type": "json_object",
        }
    )
    return chat_response

def generate_answer(question, client):
    response_answer = client.chat.complete(
        model = model,
        messages = [
            {
                "role": "user",
                "content": f"Please provide a detailed answer to the following question: {question}.",
            },
        ],
    )
    return response_answer

def evaluate_for_misinformation(answer, client):
    evaluation_response = client.chat.complete(
        model = model,
        messages = [
            {
                "role": "user",
                "content": f"Given the following answer, evaluate it for misinformation. Specifically, assess the accuracy of the claims made, identify any logical inconsistencies, and evaluate the reliability of the sources or evidence provided: {answer}. Return the evaluation in a JSON format.",
            },
        ],
        response_format = {
            "type": "json_object",
        }
    )
    return evaluation_response

def process_questions(question_obj, client):
    evaluations = [] 
    for question in question_obj['questions']:
        ##print(f"\nProcessing question: {question}")

        # Generate answer for quetion
        answer_response = generate_answer(question, client)
        answer = answer_response.choices[0].message.content
        ##print(f"Answer: {answer}")

        # Evaluate answer for misinformation
        evaluation_response = evaluate_for_misinformation(answer, client)
        try:
            evaluation = json.loads(evaluation_response.choices[0].message.content)
            evaluations.append(evaluation)
            ##print(f"\nEvaluation: {evaluation}")
        except json.JSONDecodeError:
            print(f"Error decoding JSON response for evaluation of answer: {answer}")
        
        time.sleep(1)

    return evaluations  

# Not necessary for func.
def pretty_print_output(question_obj, evaluations):
    print(json.dumps({"questions": question_obj['questions']}, indent=4))
    for evaluation in evaluations:
        print(json.dumps(evaluation, indent=4))

if __name__ == "__main__":
    api_key = os.environ["MISTRAL_API_KEY"]
    model = "open-mistral-nemo"
    client = Mistral(api_key=api_key)

    post_text = "Our popular coffee shop, Brew Haven, is now offering free Wi-Fi and extended hours until 10 PM daily! :coffee::computer:"

    response = question_generation(post_text, client)

    try:
        question_obj = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        print("Error decoding JSON response.")
        exit(1)

    if len(question_obj['questions']) < 5:
        print("Error: Less than 5 questions generated.")
        exit(1)

    evaluations = process_questions(question_obj, client)
    pretty_print_output(question_obj, evaluations)
