#!/usr/bin/env python
#
# Brief description here
#
##############################################################################
# Authors:
# - Alessio Xompero, alessio.xompero@gmail.com
# - Michiel van der Meer, m.t.van.der.meer@liacs.leidenuniv.nl
# - Shohail Ismael, shohailusman@gmail.com
#
#  Created Date: 2024/08/23
# Modified Date: 2023/08/26
#
# Copyright (c) 2024 AtomicDeFake
#
##############################################################################
import json
import os
import uuid
import time
import random
from pathlib import Path

from dotenv import load_dotenv
from mistralai import Mistral

from atomic_defake.aggregation import verify_post, VERTIFICATION_STRATEGIES
from atomic_defake.llm_response_generation import generate_llm_responses
from atomic_defake.question_generation import question_generation

load_dotenv()


STATUSES = ["wait", "human_responses", "completed", "start", "aggregation"]


class AtomicDeFake:
    def __init__(self, aggregation_method):
        self.aggregation_method = aggregation_method
        if self.aggregation_method not in VERTIFICATION_STRATEGIES:
            raise ValueError(
                f"Invalid verification method: '{self.aggregation_method}', must be one of {VERTIFICATION_STRATEGIES}."
            )

        ## TO MOVE SOMEWHERE ELSE
        api_key = os.environ["MISTRAL_API_KEY"]
        self.model = "open-mistral-nemo"
        self.client = Mistral(api_key=api_key)

        self.reset()

    def reset(self):
        self.status = "start"
        self.verified = False
        self.post_text = None

        # LLM generated questions
        self.generated_questions = None

        # LLM responses
        self.llm_responses = None

        # Human responses
        self.qa_pairs_h = {}

    def get_status(self):
        return self.status

    def set_status(self, status):
        """Brief description here."""
        assert status in STATUSES

        self.status = status

    def generate_run_id(self):
        """Brief description here."""
        return str(uuid.uuid4().hex)

    def generate_atomic_questions(self, post_text):
        """Brief description here."""
        questions = question_generation(post_text, self.client)
        return questions

    def generate_LLM_responses(self, post_text, questions):
        """Brief description here."""
        qa_pairs = generate_llm_responses(post_text, questions, self.client)
        return qa_pairs

    def store_run(self, run_id, post_text, qa_pairs, final_label):
        """Brief description here."""
        filename = Path(f"responses/{run_id}.json")

        if not filename.parent.exists():
            filename.parent.mkdir(parents=True)

        with open(filename, "w") as f:
            data = {
                "run_id": run_id,
                "prompt_data": {"post_text": post_text},
                "qa_pairs": qa_pairs,
                "final_label": final_label,
            }

            json.dump(data, f)

    def aggregate_responses(self, qa_pairs_human, qa_pairs_llm):
        """Brief description here."""
        return verify_post(qa_pairs_human, qa_pairs_llm, method=self.aggregation_method)

    def verify_ai(self, post_text):
        """Brief description here."""
        self.set_status("wait")
        self.post_text = post_text
        self.set_status("human_responses")

    def set_human_responses(self, uuid, user_qas):
        """Brief description here."""
        if uuid not in self.qa_pairs_h:
            self.qa_pairs_h[uuid] = user_qas

    def try_detect_llm(self):
        llm_responses = None
        attempt = 0
        while llm_responses is None:
            try:
                llm_responses = self.generate_LLM_responses(
                    self.post_text, self.generated_questions
                )
            except Exception as e:
                print(f"[Attempt {attempt}] Error generating LLM responses: {e}")
                time.sleep(10)
                attempt += 1
                if attempt > 5:
                    break

        return llm_responses

    def detect_mislead_info(self):
        """Brief description here."""
        self.set_status("aggregation")

        self.llm_responses = self.try_detect_llm()

        final_label = self.aggregate_responses(self.qa_pairs_h, self.llm_responses)

        print(self.qa_pairs_h)
        print(self.llm_responses)

        self.verified = final_label

        time.sleep(3)

        self.set_status("completed")

    def format_feedback(self):
        """Re-arrange dictionary of question-answer pairs and prepare the feedback report."""

        feedback_dict = dict()

        for user_id, user in self.qa_pairs_h.items():
            # Number of Question-Answer pairs
            n_qa_pair = len(user["qa_pair"])

            for idx in range(0, n_qa_pair):
                if idx not in feedback_dict:
                    feedback_dict[idx] = {
                        "question": user["qa_pair"][idx]["question"],
                        "human_responses": [user["qa_pair"][idx]["response_human"]],
                    }
                elif user_id not in feedback_dict[idx]:
                    feedback_dict[idx]["human_responses"].append(
                        user["qa_pair"][idx]["response_human"]
                    )

        print(" ---- LLM responses ---- ")
        print(self.llm_responses)

        if self.llm_responses is not None:
            # feedback_report += "=== LLM Responses ===\n"
            for idx, qa_pair in enumerate(self.llm_responses):
                llm_answer = qa_pair["response_llm"]["response"]

                if idx not in feedback_dict:
                    feedback_dict[idx] = {
                        "question": user["qa_pair"][idx]["question"],
                        "ai_response": llm_answer,
                    }
                else:
                    feedback_dict[idx]["ai_response"] = llm_answer

        feedback_report = "\n\n -- Feedback report -- \n\n"

        for idx in range(0, n_qa_pair):
            feedback_report += "Question {:d}: ".format(idx + 1)
            feedback_report += feedback_dict[idx]["question"]
            feedback_report += "\n\nHuman Responses:\n"
            for h_res in feedback_dict[idx]["human_responses"]:
                feedback_report += f"  > {h_res}\n\n"

            if self.llm_responses is not None:
                feedback_report += f"\n\nAI response: {feedback_dict[idx]['ai_response']}\n\n"

        return feedback_report

    def get_output(self):
        """Brief description here."""
        post_text_verified = None

        if self.post_text is None:
            # It should never enter here in a working pipeline.
            post_text_verified = -1
            user_response = "No post to verify"
        else:
            if self.verified:
                post_text_verified = 1
                user_response = self.post_text + "\n(✅ Verified by ADF)"
            else:
                post_text_verified = 0
                user_response = "YOUR POST:\n " + self.post_text + self.format_feedback()

        return post_text_verified, user_response

    def get_ai_questions_fake(self):
        """Brief description here."""
        adf_questions = {
            "qa_pair": [
                {
                    "question": "Is this OK? 1",
                },
                {
                    "question": "Is this OK? 2",
                },
                {
                    "question": "Is this OK? 3",
                },
                {
                    "question": "Is this OK? 4",
                },
                {
                    "question": "Is this OK? 5",
                },
            ]
        }

        return adf_questions

    def detect_mislead_info_fake(self):
        """Brief description here."""
        # final_label = self.aggregate_responses(run_id, responses)

        ### Aggregate results from the human and the AI
        self.set_status("aggregation")

        threshold = 0.5

        likelihood = random.random()

        print(threshold)
        print(likelihood)

        if likelihood > threshold:
            self.verified = True
        else:
            self.verified = False

        time.sleep(3)

        self.set_status("completed")
