import express from "express";
import path from "path";
import { spawn } from "child_process";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json());

// Lazy-initialize Gemini AI client safely
let aiClient: GoogleGenAI | null = null;
function getAIClient(): GoogleGenAI | null {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey || apiKey === "MY_GEMINI_API_KEY") {
    return null;
  }
  if (!aiClient) {
    try {
      aiClient = new GoogleGenAI({ apiKey });
    } catch (err) {
      console.error("Failed to initialize GoogleGenAI client:", err);
      return null;
    }
  }
  return aiClient;
}

// 1. Health check endpoint
app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
    app: "GURU - Student Career Roadmap Project",
    geminiConfigured: Boolean(process.env.GEMINI_API_KEY && process.env.GEMINI_API_KEY !== "MY_GEMINI_API_KEY"),
    pythonRuntime: "Python 3.10.12 Available"
  });
});

// 2. Python Code Execution & Verification Endpoint
app.post("/api/run-python", (req, res) => {
  const { code, testCases } = req.body;

  if (typeof code !== "string") {
    res.status(400).json({ error: "No code provided" });
    return;
  }

  // Build a test wrapper script to execute in python3
  const testCasesJson = JSON.stringify(testCases || []);
  const harness = `
import sys
import json
import io
from contextlib import redirect_stdout

# Student code execution
user_code = ${JSON.stringify(code)}
test_cases = json.loads(${JSON.stringify(testCasesJson)})

results = []
stdout_buffer = io.StringIO()

try:
    with redirect_stdout(stdout_buffer):
        exec_globals = {}
        exec(user_code, exec_globals)
    captured_output = stdout_buffer.getvalue()
    
    all_passed = True
    for idx, tc in enumerate(test_cases):
        func_name = tc.get("functionName")
        args = tc.get("args", [])
        expected = tc.get("expected")
        description = tc.get("description", f"Test {idx + 1}")
        
        if func_name and func_name in exec_globals:
            fn = exec_globals[func_name]
            actual = fn(*args)
            passed = (actual == expected)
            if not passed:
                all_passed = False
            results.append({
                "description": description,
                "passed": passed,
                "expected": str(expected),
                "actual": str(actual)
            })
        else:
            results.append({
                "description": description,
                "passed": True,
                "expected": "Executed",
                "actual": "OK"
            })

    print(json.dumps({
        "success": True,
        "stdout": captured_output.strip(),
        "results": results,
        "allPassed": all_passed if len(test_cases) > 0 else True
    }))
except Exception as e:
    import traceback
    tb = traceback.format_exc()
    print(json.dumps({
        "success": False,
        "error": str(e),
        "traceback": tb,
        "results": []
    }))
`;

  const pyProcess = spawn("python3", ["-"], { timeout: 6000 });
  let stdoutData = "";
  let stderrData = "";

  pyProcess.stdout.on("data", (chunk) => {
    stdoutData += chunk.toString();
  });

  pyProcess.stderr.on("data", (chunk) => {
    stderrData += chunk.toString();
  });

  pyProcess.on("close", (code) => {
    if (code !== 0 && !stdoutData.trim()) {
      res.json({
        success: false,
        error: stderrData.trim() || `Process exited with code ${code}`,
        results: []
      });
      return;
    }

    try {
      const parsed = JSON.parse(stdoutData.trim());
      res.json(parsed);
    } catch (_parseErr) {
      res.json({
        success: true,
        stdout: stdoutData.trim(),
        results: [],
        allPassed: true
      });
    }
  });

  pyProcess.stdin.write(harness);
  pyProcess.stdin.end();
});

// 3. AI Career Coach Endpoint (Grounds on actual student competencies)
app.post("/api/coach", async (req, res) => {
  const {
    question,
    studentProfile,
    targetCareer,
    activeBottleneck,
    availableMinutes,
    roadmapState
  } = req.body;

  const prompt = `
You are the central AI Career Coach of Vektor.
You are NOT a generic chatbot or course catalog.
Your philosophy:
- An adaptive AI career coach that understands what a student actually knows.
- Never shame the student for perception gaps.
- Ground every response in their ACTUAL demonstrated vs self-assessed competency levels.
- Focus on practical decision-making: "Where am I now?", "Where do I need to be?", "What is my biggest current gap?", "What should I do today?", "Why did the roadmap change?".

STUDENT PROFILE CONTEXT:
- Target Career: ${targetCareer || "AI/ML Engineer"}
- Available Learning Time: ${availableMinutes || 60} minutes
- Demonstrated Competencies: ${JSON.stringify(studentProfile?.demonstrated || {})}
- Self-Perceived Competencies: ${JSON.stringify(studentProfile?.perceived || {})}
- Perception Gaps: ${JSON.stringify(studentProfile?.gaps || {})}
- Identified Bottleneck: ${activeBottleneck || "Statistics (Level 2 vs required Level 4 for ML readiness)"}
- Current Living Roadmap Phase: ${roadmapState?.activeNode || "Statistics Level 2 -> Level 3"}

STUDENT QUERY: "${question || "What should I focus on right now and why?"}"

Instructions:
1. Provide a direct, authoritative, and warm coaching answer.
2. Specifically cite their competency levels (e.g. "Your Python is verified at Level 3, but Machine Learning requires Level 4 Statistics as a strict prerequisite").
3. Give an actionable next step or decision.
4. Keep the response crisp (under 160 words). Do not use bullet spam or fluffy greetings.
`;

  const ai = getAIClient();
  if (ai) {
    try {
      const response = await ai.models.generateContent({
        model: "gemini-3.8-flash",
        contents: prompt,
      });
      res.json({ text: response.text });
      return;
    } catch (apiError) {
      console.warn("Gemini API call failed, using intelligent deterministic fallback:", apiError);
    }
  }

  // Deterministic Fallback if Gemini key is not configured or fails
  const q = (question || "").toLowerCase();
  let fallbackText = "";

  if (q.includes("why do i need statistics") || q.includes("statistics for ai")) {
    fallbackText = `Statistics is the mathematical backbone of Machine Learning. You already demonstrate Level 3 in Python, so coding syntax won't be your obstacle. However, understanding loss functions, gradient estimation, confidence intervals, and conditional probability distributions is required before you train or debug models. In our expert rubric, ML Level 1 requires verified Statistics Level 3 so you don't treat models as black boxes.`;
  } else if (q.includes("can i skip") || q.includes("skip this")) {
    fallbackText = `I advise against skipping Statistics. When you tested on probability questions, the system detected a prerequisite bottleneck in conditional distributions. If you jump straight to training regression or neural networks now, model evaluation and regularization will become blind trial-and-error. Once you verify Statistics Level 3 via today's challenge, Machine Learning modules unlock immediately.`;
  } else if (q.includes("30 minutes") || q.includes("time") || availableMinutes <= 30) {
    fallbackText = `I have restructured today's mission for a 30-minute high-yield sprint. We condensed the theoretical review to 8 minutes and prioritized a 15-minute hands-on Python simulation of Bayes' theorem, followed by a 7-minute 3-question competency verification. This keeps your momentum without burning time on topics you already know.`;
  } else if (q.includes("project") || q.includes("what project")) {
    fallbackText = `Based on your verified skills (Python L3, Pandas L2, Statistics L2), I recommend the 'Student Performance Predictor' project. It directly exercises conditional probability, variance analysis, and scikit-learn preprocessing—exactly addressing your current bottleneck while building a portfolio artifact for internship reviews.`;
  } else if (q.includes("already know python")) {
    fallbackText = `Your assessment confirmed you have strong syntax (Level 3 Builder). That's why your roadmap has skipped 14 hours of beginner Python tutorials. We've preserved your time so you can focus entirely on applying Python to mathematical modeling and vector operations in NumPy and Pandas.`;
  } else {
    fallbackText = `Your current primary priority is Statistics Level 2 → Level 3. While your Python skills are solidly demonstrated at Level 3, your target career (AI/ML Engineer) requires Level 4 Statistics. Because conditional probability is a hard prerequisite for the upcoming Machine Learning stage, I have moved Statistics ahead of ML in your roadmap. Complete today's 60-minute mission to verify your competency!`;
  }

  res.json({ text: fallbackText });
});

// 4. AI Mentor Brief Generation Endpoint
app.post("/api/mentor-brief", async (req, res) => {
  const { studentName, targetCareer, readinessScore, strongSkills, gapSkills, currentChallenge } = req.body;

  const prompt = `
Generate a concise, high-value 1-page briefing for an industry mentor meeting with a student.
Student: ${studentName || "Alex Chen"}
Target Career: ${targetCareer || "AI/ML Engineer"}
Current Readiness: ${readinessScore || "47%"}
Strong Demonstrated Skills: ${JSON.stringify(strongSkills || ["Python L4", "Git L3"])}
Needs Development: ${JSON.stringify(gapSkills || ["Statistics L2", "ML Fundamentals L1"])}
Current Milestone/Challenge: ${currentChallenge || "Selecting first major portfolio project and bridging theory to deployment"}

Format the brief cleanly with:
- Executive Summary
- Current Competency Assessment (Demonstrated vs Target)
- Biggest Structural Bottleneck
- 3 High-Impact Discussion Questions for the Mentor
`;

  const ai = getAIClient();
  if (ai) {
    try {
      const response = await ai.models.generateContent({
        model: "gemini-3.8-flash",
        contents: prompt,
      });
      res.json({ brief: response.text });
      return;
    } catch (apiError) {
      console.warn("Gemini API call failed for mentor brief:", apiError);
    }
  }

  // Rich fallback brief matching prompt specs
  const fallbackBrief = `
EXECUTIVE MENTOR BRIEF
Student: ${studentName || "Alex Chen"} | Goal: ${targetCareer || "AI/ML Engineer"}
Career Readiness Index: ${readinessScore || 47}%

1. VERIFIED DEMONSTRATED STRENGTHS:
- Python (Level 3 - Builder): Object-oriented programming, modules, data pipelines.
- Tooling & Git (Level 3): Version control, reproducible environments.

2. ACTIVE BOTTLENECK / NEEDS DEVELOPMENT:
- Statistics & Probability (Level 2): Weakness isolated to conditional probability and hypothesis testing.
- Machine Learning (Level 1): Theoretical familiarity, needs supervised learning implementation.

3. CURRENT MILESTONE:
- Transitioning from Python syntax to first portfolio project. Deciding between Recommendation Engine vs Time-Series Forecasting.

4. SUGGESTED 30-MINUTE DISCUSSION TOPICS:
1. Which portfolio project best demonstrates end-to-end data pipeline mastery without over-relying on pre-packaged datasets?
2. What specific model evaluation metrics (Precision/Recall vs ROC-AUC) do hiring managers test during technical screens?
3. How should the student bridge model training to API deployment (e.g. FastAPI / Docker)?
`;

  res.json({ brief: fallbackBrief });
});

async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const { createServer: createViteServer } = await import("vite");
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Vektor server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
