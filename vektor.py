#!/usr/bin/env python3
"""
GURU - Adaptive Student Career Operating System (Python Edition)

An adaptive career coach that compares a student's demonstrated skills
against expert-defined career competencies, identifies perception gaps,
and dynamically generates a living roadmap.

Usage:
  Interactive Mode:  python3 vektor.py
  HTTP Server Mode:  python3 vektor.py --serve --port 8080
"""

import sys
import json
import argparse
from typing import Dict, List, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==============================================================================
# 1. EXPERT-DEFINED CAREER RUBRICS
# ==============================================================================

AI_ML_ENGINEER_FRAMEWORK = {
    "career_id": "ai_ml_engineer",
    "title": "AI / Machine Learning Engineer",
    "description": "Designs, trains, evaluates, and deploys machine learning models to production.",
    "target_level": 4,
    "skills": {
        "python": {
            "name": "Python Engineering",
            "target_level": 4,
            "levels": {
                1: {"name": "Syntax & Basics", "criteria": "Variables, loops, conditionals, basic functions"},
                2: {"name": "Problem Solver", "criteria": "Complex logic, file I/O, error handling, basic algorithms"},
                3: {"name": "Builder", "criteria": "Object-oriented programming, data structures, unit testing, modular architecture"},
                4: {"name": "Advanced", "criteria": "Decorators, generators, concurrency, memory profiling, clean code architecture"},
                5: {"name": "Professional", "criteria": "Production microservices, high-throughput APIs, framework development, CI/CD"}
            }
        },
        "mathematics": {
            "name": "Linear Algebra & Calculus",
            "target_level": 4,
            "levels": {
                1: {"name": "High School Basics", "criteria": "Basic algebra, plotting, coordinate geometry"},
                2: {"name": "Vector Math", "criteria": "Dot products, matrix multiplication, vector norms"},
                3: {"name": "Multivariable Calculus", "criteria": "Partial derivatives, gradients, chain rule for backpropagation"},
                4: {"name": "Optimization", "criteria": "Jacobians, Hessians, convex optimization, Lagrange multipliers"},
                5: {"name": "Research Math", "criteria": "Advanced numerical methods, differential geometry"}
            }
        },
        "statistics": {
            "name": "Probability & Statistics",
            "target_level": 4,
            "levels": {
                1: {"name": "Descriptive Stats", "criteria": "Mean, median, variance, standard deviation"},
                2: {"name": "Basic Distributions", "criteria": "Normal, binomial, Poisson, basic hypothesis tests"},
                3: {"name": "Bayesian Probability", "criteria": "Conditional probability, Bayes Theorem, likelihood estimation, Central Limit Theorem"},
                4: {"name": "Statistical Inference", "criteria": "Maximum likelihood estimation (MLE), confidence intervals, p-hacking avoidance, A/B testing"},
                5: {"name": "Advanced Inference", "criteria": "Markov chains, Monte Carlo sampling, causal inference"}
            }
        },
        "machine_learning": {
            "name": "Machine Learning Algorithms",
            "target_level": 5,
            "levels": {
                1: {"name": "Conceptual Awareness", "criteria": "Supervised vs unsupervised definitions, overfitting vs underfitting"},
                2: {"name": "Classical Models", "criteria": "Linear regression, logistic regression, decision trees using scikit-learn"},
                3: {"name": "Model Diagnostics", "criteria": "Cross-validation, ROC-AUC, precision-recall tradeoffs, regularizations (L1/L2)"},
                4: {"name": "Advanced Architectures", "criteria": "Ensemble methods (XGBoost, LightGBM), deep neural networks, loss function design"},
                5: {"name": "Production MLOps", "criteria": "Model monitoring, feature stores, drift detection, low-latency inference pipelines"}
            }
        },
        "portfolio_projects": {
            "name": "Practical Portfolio & Deployment",
            "target_level": 4,
            "levels": {
                1: {"name": "Guided Exercises", "criteria": "Following step-by-step notebook tutorials"},
                2: {"name": "Standalone Analysis", "criteria": "Exploratory data analysis on raw real-world datasets"},
                3: {"name": "End-to-End System", "criteria": "Trained ML model served via FastAPI microservice with containerization"},
                4: {"name": "Production Grade", "criteria": "Deployed distributed pipeline with CI/CD, unit tests, and live traffic"},
                5: {"name": "Industry Scale", "criteria": "Serving millions of queries with low latency SLAs"}
            }
        }
    }
}

# ==============================================================================
# 2. VEKTOR CORE ADAPTIVE COACH ENGINE
# ==============================================================================

class VektorCareerCoach:
    def __init__(self, student_name: str = "Alex Chen"):
        self.student_name = student_name
        self.target_career = AI_ML_ENGINEER_FRAMEWORK
        
        # Initial Student State
        self.skills_state = {
            "python": {"perceived": 4, "demonstrated": 3, "verified": True},
            "mathematics": {"perceived": 3, "demonstrated": 3, "verified": True},
            "statistics": {"perceived": 3, "demonstrated": 2, "verified": False},
            "machine_learning": {"perceived": 2, "demonstrated": 1, "verified": False},
            "portfolio_projects": {"perceived": 2, "demonstrated": 1, "verified": False}
        }
        self.roadmap = []
        self.mutation_history = []
        self.generate_initial_roadmap()

    def get_readiness_score(self) -> int:
        """Calculates demonstrated readiness against target levels."""
        total_target = sum(s["target_level"] for s in self.target_career["skills"].values())
        total_demo = sum(self.skills_state[sid]["demonstrated"] for sid in self.skills_state)
        return int((total_demo / total_target) * 100)

    def identify_primary_bottleneck(self) -> Dict[str, Any]:
        """Identifies the biggest current prerequisite gap."""
        # Statistics is required by ML and has the largest gap
        stats = self.skills_state["statistics"]
        if stats["demonstrated"] < 3:
            return {
                "skill_id": "statistics",
                "name": "Probability & Statistics",
                "current_level": stats["demonstrated"],
                "target_level": 4,
                "reason": "Prerequisite for Machine Learning algorithms. Weakness detected in conditional probability and Bayes' Theorem."
            }
        elif self.skills_state["machine_learning"]["demonstrated"] < 3:
            return {
                "skill_id": "machine_learning",
                "name": "Machine Learning Algorithms",
                "current_level": self.skills_state["machine_learning"]["demonstrated"],
                "target_level": 5,
                "reason": "Statistics prerequisite satisfied. Now need supervised loss function mastery."
            }
        return {
            "skill_id": "portfolio_projects",
            "name": "Practical Portfolio",
            "current_level": self.skills_state["portfolio_projects"]["demonstrated"],
            "target_level": 4,
            "reason": "Theory demonstrated; production deployment and FastAPI serving needed."
        }

    def get_perception_gaps(self) -> List[Dict[str, Any]]:
        """Calculates difference between self-reported and tested ability."""
        gaps = []
        for sid, meta in self.target_career["skills"].items():
            state = self.skills_state[sid]
            gap = state["perceived"] - state["demonstrated"]
            gaps.append({
                "skill_id": sid,
                "name": meta["name"],
                "self_reported": state["perceived"],
                "demonstrated": state["demonstrated"],
                "target": meta["target_level"],
                "gap": gap,
                "status": "Divergence Detected" if gap > 0 else "Calibrated"
            })
        return gaps

    def generate_initial_roadmap(self):
        """Generates a living roadmap that skips already-demonstrated skills."""
        self.roadmap = [
            {
                "id": "node_python_advanced",
                "title": "Python: Builder → Advanced",
                "level": 3,
                "status": "completed",
                "why": "Demonstrated Level 3 through coding diagnostics. Skipped 14 hours of beginner syntax."
            },
            {
                "id": "node_stats_l3",
                "title": "Statistics Level 2 → Level 3 (Bayesian Reasoning)",
                "level": 3,
                "status": "active",
                "why": "Current biggest bottleneck. Required prerequisite for Supervised ML."
            },
            {
                "id": "node_ml_supervised",
                "title": "Supervised Machine Learning & Optimization",
                "level": 2,
                "status": "locked",
                "why": "Locked until Statistics Level 3 is demonstrated."
            },
            {
                "id": "node_portfolio_api",
                "title": "Portfolio: Live ML Microservice",
                "level": 3,
                "status": "locked",
                "why": "Locked until ML algorithms and model evaluation are verified."
            }
        ]
        self.log_mutation("INITIAL_GEN", "Roadmap Generated", "Skipped beginner Python; elevated Statistics L3 to active priority.")

    def log_mutation(self, trigger: str, title: str, description: str):
        self.mutation_history.insert(0, {
            "trigger": trigger,
            "title": title,
            "description": description
        })

    def simulate_struggle_with_probability(self):
        """Simulates AI isolating root prerequisite gap and mutating the roadmap."""
        injected_node = {
            "id": "node_prereq_prob_drill",
            "title": "Targeted Drill: Conditional Probability & Base Rate Fallacies",
            "level": 2,
            "status": "active",
            "why": "AI detected repeated friction on Bayes' Theorem. Inserted targeted drill."
        }
        self.roadmap.insert(1, injected_node)
        self.log_mutation(
            "PREREQUISITE_INJECTED",
            "Root Gap Isolated: Conditional Probability",
            "Student struggled with joint distributions. Injected focused drill before proceeding to ML."
        )

    def verify_statistics_level_3(self):
        """Validates demonstrated mastery and unlocks ML stage."""
        self.skills_state["statistics"]["demonstrated"] = 3
        self.skills_state["statistics"]["verified"] = True
        
        for node in self.roadmap:
            if "node_stats" in node["id"] or "drill" in node["id"]:
                node["status"] = "completed"
            elif node["id"] == "node_ml_supervised":
                node["status"] = "active"

        self.log_mutation(
            "LEVEL_UP_VERIFIED",
            "Statistics Level 3 Verified",
            "Competency demonstrated. Supervised Machine Learning node unlocked."
        )

    def apply_mentor_feedback(self, advice: str):
        """Updates roadmap from real industry mentor advice."""
        mentor_node = {
            "id": "node_mentor_fastapi_rec",
            "title": "Mentor Project: Recommendation Engine with FastAPI",
            "level": 3,
            "status": "active",
            "why": f"Advised by Mentor Elena Rostova: '{advice}'"
        }
        self.roadmap.append(mentor_node)
        self.log_mutation(
            "MENTOR_FEEDBACK",
            "Roadmap Updated from Mentor Session",
            f"Elena Rostova recommended: {advice}. Added production microservice deliverable."
        )

    def generate_todays_mission(self, available_minutes: int = 60) -> Dict[str, Any]:
        """Restructures the mission to fit available time."""
        if available_minutes <= 15:
            steps = [
                {"step": 1, "time": "10 min", "task": "Express Python Challenge: Bayes Posterior Calculator"},
                {"step": 2, "time": "5 min", "task": "Targeted Competency Check"}
            ]
        elif available_minutes <= 30:
            steps = [
                {"step": 1, "time": "8 min", "task": "Accelerated Concept: Conditional Probability & Likelihood"},
                {"step": 2, "time": "15 min", "task": "Python Practical Task: Posterior Function"},
                {"step": 3, "time": "7 min", "task": "Targeted Competency Check"}
            ]
        else:
            steps = [
                {"step": 1, "time": "15 min", "task": "Learn Conditional Probability & Bayes' Rule"},
                {"step": 2, "time": "20 min", "task": "Solve Guided Problems (Base Rate Paradox)"},
                {"step": 3, "time": "15 min", "task": "Python Code Challenge: Calculate Bayes Posterior"},
                {"step": 4, "time": "10 min", "task": "Demonstrated Competency Assessment"}
            ]

        return {
            "goal": "Statistics Level 2 → Level 3",
            "estimated_minutes": available_minutes,
            "why": "Probability is currently your biggest prerequisite gap for Machine Learning.",
            "steps": steps
        }

    def print_five_core_questions(self):
        """Outputs the 5 core coaching answers."""
        bottleneck = self.identify_primary_bottleneck()
        readiness = self.get_readiness_score()
        print("\n" + "=" * 65)
        print("GURU CAREER COACH - THE 5 CORE CONTINUOUS QUESTIONS")
        print("=" * 65)
        print(f"1. WHERE AM I NOW?\n   Readiness: {readiness}% for {self.target_career['title']}")
        print(f"   Demonstrated: Python L{self.skills_state['python']['demonstrated']}, Stats L{self.skills_state['statistics']['demonstrated']}, ML L{self.skills_state['machine_learning']['demonstrated']}")
        print(f"\n2. WHERE DO I NEED TO BE?\n   Target: Level {self.target_career['target_level']} across Core Competencies")
        print(f"\n3. WHAT IS MY BIGGEST CURRENT GAP?\n   Bottleneck: {bottleneck['name']} (L{bottleneck['current_level']} vs Target L{bottleneck['target_level']})")
        print(f"   Reason: {bottleneck['reason']}")
        print(f"\n4. WHAT EXACTLY SHOULD I DO NEXT?\n   Today's Mission: Statistics Level 2 → Level 3 (Bayesian Probability)")
        print(f"\n5. HAS MY ROADMAP CHANGED BASED ON WHAT I DEMONSTRATED?\n   Mutations Logged: {len(self.mutation_history)} updates in audit trail")
        print("=" * 65 + "\n")


# ==============================================================================
# 3. INTERACTIVE CLI RUNNER
# ==============================================================================

def run_interactive_cli():
    coach = VektorCareerCoach()
    
    print("""
========================================================================
    ____ _   _ ____  _   _ 
   / ___| | | |  _ \\| | | |
  | |  _| | | | |_) | | | |
  | |_| | |_| |  _ <| |_| |
   \\____|\\___/|_| \\_\\\\___/ 
   Adaptive Student Career Roadmap System (Python Engine)
========================================================================
""")
    coach.print_five_core_questions()

    while True:
        print("\nCHOOSE AN ACTION:")
        print("  [1] View Perception Gap (Reality Check)")
        print("  [2] View Living Roadmap")
        print("  [3] Simulate: Student Struggles with Probability -> AI Injects Prerequisite")
        print("  [4] Simulate: Complete Coding Task -> Verify Statistics Level 3")
        print("  [5] Simulate: Human Mentor Session -> Apply Advice to Roadmap")
        print("  [6] Print 5 Core Coaching Questions")
        print("  [7] Exit")

        choice = input("\nSelect option (1-7): ").strip()

        if choice == "1":
            print("\n--- PERCEPTION GAP REPORT ---")
            for gap in coach.get_perception_gaps():
                print(f"• {gap['name']:30} Self-Reported: L{gap['self_reported']} | Demonstrated: L{gap['demonstrated']} | Target: L{gap['target']} [{gap['status']}]")
            print("\nCoach Note: Notice the gap in Statistics (Self L3 vs Tested L2). This is your #1 prerequisite bottleneck.")

        elif choice == "2":
            print("\n--- LIVING ADAPTIVE ROADMAP ---")
            for idx, node in enumerate(coach.roadmap, 1):
                status_icon = "✓ [DONE]" if node["status"] == "completed" else "▶ [ACTIVE]" if node["status"] == "active" else "🔒 [LOCKED]"
                print(f"{idx}. {status_icon} {node['title']}")
                print(f"   Why: {node['why']}")

            print("\n--- RECENT ROADMAP MUTATIONS ---")
            for mut in coach.mutation_history[:3]:
                print(f"• [{mut['trigger']}] {mut['title']}: {mut['description']}")

        elif choice == "3":
            print("\n>>> Simulating struggle detection on Bayes base rates...")
            coach.simulate_struggle_with_probability()
            print("✓ Roadmap updated! Prerequisite drill inserted ahead of Machine Learning.")

        elif choice == "4":
            print("\n>>> Verifying Python code challenge test cases...")
            coach.verify_statistics_level_3()
            print("✓ SUCCESS: Statistics Level 3 — VERIFIED!")
            print("✓ Supervised Machine Learning node unlocked!")

        elif choice == "5":
            print("\n>>> Simulating Mentor Meeting with Elena Rostova...")
            advice = "Build a movie recommendation system and learn model deployment with FastAPI."
            coach.apply_mentor_feedback(advice)
            print(f"✓ Mentor feedback recorded: '{advice}'")
            print("✓ Living roadmap mutated with production microservice deliverable!")

        elif choice == "6":
            coach.print_five_core_questions()

        elif choice == "7":
            print("\nExiting GURU. Goodbye!\n")
            break
        else:
            print("Invalid selection. Please choose 1-7.")


# ==============================================================================
# 4. LIGHTWEIGHT HTTP SERVER MODE
# ==============================================================================

class VektorHTTPHandler(BaseHTTPRequestHandler):
    coach = VektorCareerCoach()

    def _send_json(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json({
                "career": self.coach.target_career["title"],
                "readiness_score": self.coach.get_readiness_score(),
                "bottleneck": self.coach.identify_primary_bottleneck(),
                "skills": self.coach.skills_state,
                "roadmap_nodes": len(self.coach.roadmap)
            })
        elif self.path == "/api/gaps":
            self._send_json(self.coach.get_perception_gaps())
        elif self.path == "/api/roadmap":
            self._send_json({
                "roadmap": self.coach.roadmap,
                "mutations": self.coach.mutation_history
            })
        else:
            self._send_json({"service": "Vektor Python API", "endpoints": ["/api/status", "/api/gaps", "/api/roadmap"]})


def main():
    parser = argparse.ArgumentParser(description="Vektor Career Coach (Python)")
    parser.add_argument("--serve", action="store_true", help="Run as lightweight HTTP API server")
    parser.add_argument("--port", type=int, default=8080, help="Port for HTTP server (default: 8080)")
    args = parser.parse_args()

    if args.serve:
        server_address = ("", args.port)
        httpd = HTTPServer(server_address, VektorHTTPHandler)
        print(f"Vektor Python HTTP server running on http://localhost:{args.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
    else:
        run_interactive_cli()


if __name__ == "__main__":
    main()
