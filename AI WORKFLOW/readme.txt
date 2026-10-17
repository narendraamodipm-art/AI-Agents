================================================================================
  AI WORKFLOW PROJECTS
  1. YouTube Video -> Study Notes Generator
  2. Resume <-> Job Description Matcher + Cover Letter Writer
  Built with: Python, Streamlit (UI), Mistral AI (LLM + embeddings), LangChain
================================================================================


--------------------------------------------------------------------------------
0. WHAT IS AN "AI WORKFLOW"?
--------------------------------------------------------------------------------
An AI workflow is a program where the DEVELOPER decides the steps, in a fixed
order, and the LLM does the work inside some of those steps.

    Input --> Step 1 --> Step 2 (LLM) --> Step 3 (LLM) --> Step 4 --> Output
              the same path every time

Compare with an AI AGENT, where the LLM itself decides which step/tool to use
next and loops until it is done. Both projects here are WORKFLOWS: every run
goes through the same steps in the same order, so they are predictable, easy
to debug, and their cost is easy to estimate.

Workflow patterns used in these projects:
  - Prompt chaining      : the output of one LLM call is the input of the next
  - Map-reduce           : summarise each chunk, then combine the summaries
  - Structured output    : the LLM fills in a Pydantic schema (JSON), so Python
                           code can use the result reliably
  - Code + LLM together  : plain Python does the maths (scores), the LLM does
                           the language work
  - Guardrails           : code checks the LLM's output (quiz answers valid,
                           no invented numbers in the cover letter)


--------------------------------------------------------------------------------
1. FOLDER STRUCTURE
--------------------------------------------------------------------------------
AI WORKFLOW/
|-- readme.txt                 <- this file
|-- requirements.txt           <- Python packages for both apps
|-- youtube_notes/
|   `-- app.py                 <- Project 1: YouTube -> study notes
`-- resume_matcher/
    `-- app.py                 <- Project 2: resume matcher + cover letter

Each app is a single, self-contained file so it can be run or deployed on its
own.


--------------------------------------------------------------------------------
2. SETUP
--------------------------------------------------------------------------------
Step 1 - Install the packages (from the Practice folder, with the venv active):

    pip install -r "AI WORKFLOW/requirements.txt"

Step 2 - API key. Both apps read MISTRAL_API_KEY from a .env file. They search
upward from their own folder, so the existing file at Practice/.env is used:

    MISTRAL_API_KEY=your-key-here

    Never commit .env to Git. Never paste the key into the code.

Step 3 - Run an app:

    streamlit run "AI WORKFLOW/youtube_notes/app.py"
    streamlit run "AI WORKFLOW/resume_matcher/app.py"

    Streamlit opens the app in your browser at http://localhost:8501


--------------------------------------------------------------------------------
3. MISTRAL MODELS (IMPORTANT)
--------------------------------------------------------------------------------
Mistral subscriptions only allow some models. On the current API key:

    Model                    Requests/min   Status
    ministral-8b-latest          188        works  (DEFAULT)
    ministral-14b-latest          30        works  (better quality, slower limit)
    ministral-3b-latest          750        works  (fastest, lower quality)
    mistral-embed                 -         works  (embeddings, used in Project 2)
    mistral-small-latest           0        429 "Rate limit exceeded" - not usable
    mistral-medium-latest          0        429 - not usable
    mistral-large-latest           -        403 "not available in your subscription"

So both apps offer only the three "ministral" models in the sidebar.
NOTE: the older RAG app (Practice/RAG/RAG.py) uses mistral-large-latest, which
returns 403 on this plan - change it to ministral-8b-latest to make it work.

Both apps also retry automatically on HTTP 429 (temporary rate limit) with
exponential backoff: wait 2s, 4s, 8s, 16s, 32s, then give up and show an error.
See call_with_retry() in each app.py.


================================================================================
PROJECT 1 - YOUTUBE VIDEO -> STUDY NOTES GENERATOR
================================================================================

WHAT IT DOES
  Paste a YouTube link -> get:
    - Study notes in Markdown: summary, key points WITH TIMESTAMPS, key terms,
      takeaways
    - Flashcards (download as CSV - can be imported into Anki)
    - An interactive multiple-choice quiz with scoring and explanations
    - The full timestamped transcript
  Settings: model, notes language (English / Hindi / same as video), number of
  flashcards and quiz questions.

THE WORKFLOW (fixed steps)

  YouTube URL
      |
      v
  [1] extract_video_id()      regex -> 11-character video id
      |                       works for watch?v=, youtu.be/, shorts/, embed/
      v
  [2] fetch_transcript()      youtube-transcript-api -> [{start, text}, ...]
      |                       prefers English captions, else any language
      |                       cached with @st.cache_data (no refetch on rerun)
      v
  [3] chunk_transcript()      split into ~12,000-character chunks, each line
      |                       tagged "[mm:ss] text" so the LLM can keep
      |                       timestamps
      v
  [4] notes_for_chunk()       MAP: one Mistral call per chunk -> bullet notes
      |                       (skipped for short videos with only 1 chunk -
      |                        saves an API call)
      v
  [5] combine_notes()         REDUCE: one Mistral call merges all chunk notes
      |                       into one document with fixed sections
      v
  [6] make_study_material()   STRUCTURED OUTPUT: Mistral fills the StudyMaterial
      |                       Pydantic schema -> flashcards + quiz as JSON
      |                       guardrail: drop quiz questions whose
      |                       correct_index is out of range
      v
  Streamlit tabs: Notes | Flashcards | Quiz | Transcript

WHY CHUNKING? (map-reduce)
  A 1-hour video has ~60,000+ characters of transcript. Sending it all at once
  can exceed the model's context window and gives worse results. So:
    MAP    : summarise each chunk separately (small, focused calls)
    REDUCE : combine the chunk summaries into the final notes
  This is the standard pattern for summarising long documents.

WHY STRUCTURED OUTPUT?
  For flashcards and the quiz we need data the CODE can use (question, options,
  index of the correct answer), not free text. llm.with_structured_output(
  StudyMaterial) makes Mistral return JSON matching the Pydantic class:

      class QuizQuestion(BaseModel):
          question: str
          options: list[str]
          correct_index: int
          explanation: str

  The quiz tab then checks the user's answers against correct_index in Python.

API CALLS PER VIDEO
  number of chunks + 2   (e.g. an 18-minute video = 2 chunks = 4 calls)
  Tested: 18-minute video -> about 45 seconds end to end.

LIMITATIONS
  - Only works for videos that have captions (auto-generated ones count).
  - YouTube sometimes blocks transcript requests from cloud servers; works best
    when run locally.
  - Notes quality depends on caption quality.


================================================================================
PROJECT 2 - RESUME <-> JOB DESCRIPTION MATCHER + COVER LETTER WRITER
================================================================================

WHAT IT DOES
  Upload a resume (PDF/TXT or paste text) + paste a job description -> get:
    - Interview chance estimate (out of 100) with a breakdown of how it was
      calculated and which skills to prepare
    - Overall match score (%), required-skills coverage, semantic similarity,
      experience check
    - Matched / missing skills shown as coloured chips
    - Rewritten resume bullets tailored to the job (before / after / why)
    - A tailored cover letter (choose tone and length, rewrite on demand)
    - The structured data Mistral extracted, and a downloadable report

THE WORKFLOW (fixed steps)

  Resume (PDF/TXT/text) + Job description (text)
      |
      v
  [1] read_resume()            pypdf extracts text from the PDF
      v
  [2] extract_resume()         STRUCTURED OUTPUT -> ResumeProfile
      |                        (name, titles, years, skills, education,
      |                         achievements, experience bullets)
      v
  [3] extract_job()            STRUCTURED OUTPUT -> JobProfile
      |                        (title, company, required skills,
      |                         nice-to-have skills, min years, duties)
      v
  [4] semantic_similarity()    Mistral EMBEDDINGS (mistral-embed) of both full
      |                        texts -> cosine similarity
      v
  [5] analyse_gap()            STRUCTURED OUTPUT -> SkillGap
      |                        every JD skill goes into matched OR missing;
      |                        equivalents count (PostgreSQL ~ SQL)
      v
  [6] compute_scores()         PLAIN PYTHON (no LLM) -> match percentages
      |  interview_chance()    PLAIN PYTHON -> interview chance out of 100
      v
  [7] suggest_improvements()   STRUCTURED OUTPUT -> improved bullets + tips
      v
  [8] write_cover_letter()     free-text Mistral call -> cover letter
      |                        guardrail: invented_numbers() warns about any
      |                        number in the letter that is not in the resume
      |                        or the JD
      v
  Streamlit: metrics + tabs: Skills gap | Improve resume | Cover letter | Data

HOW THE SCORE IS CALCULATED (compute_scores)
  required  = matched required skills / all required skills
  nice      = matched nice-to-have   / all nice-to-have
  semantic  = cosine similarity of the two embeddings, stretched to 0-1:
                semantic = clip((cosine - 0.60) / 0.30, 0, 1)
              (mistral-embed gives ~0.6 for unrelated texts and ~0.9 for very
               similar ones, so 0.60-0.90 is mapped to 0-100%)

  overall   = 0.5 x required + 0.2 x nice + 0.3 x semantic
              (if the JD has no nice-to-have skills:
               overall = 0.6 x required + 0.4 x semantic)

  Example (tested): 5 of 7 required, 0 of 4 nice-to-have, cosine 0.832
    required = 0.714, nice = 0, semantic = 0.773
    overall  = 0.5(0.714) + 0.2(0) + 0.3(0.773) = 0.589 -> 59%

  The weights are a simple, explainable heuristic - you can tune them.

INTERVIEW CHANCE (interview_chance) - an ESTIMATE out of 100
  Shows how strong the profile looks for this job ON PAPER, built from the
  same analysis. It CANNOT predict how the candidate performs in the actual
  interview (preparation, communication and the interviewers matter too) -
  the app says this clearly next to the number.

  experience = 1.0 if resume years >= required minimum,
               else resume years / required minimum

  chance = 100 x ( 0.45 x required skills     <- must-haves matter most
                 + 0.10 x nice-to-have skills
                 + 0.20 x semantic similarity
                 + 0.25 x experience )

  Hard caps (big gaps in the basics limit the result):
    experience < 50% of the minimum      -> at most 40
    fewer than 50% of required skills    -> at most 45

  Bands:  75-100 High    50-74 Moderate    0-49 Low

  The app also lists the missing required skills under "To raise your chance".

  Example (tested): sample resume (Python, SQL, Snowflake, Airflow, 6 yrs) vs a
  GCP + Kafka + Spark + Snowflake job (4+ yrs):
    required 29%, nice 10%, similarity 71%, experience 100%
    raw = 100 x (0.45x0.29 + 0.10x0.10 + 0.20x0.71 + 0.25x1.0) = 53
    capped at 45 (fewer than half the required skills)  -> 45/100, Low
    to prepare: Kafka, Spark, PySpark, GCP (BigQuery, Pub/Sub, Dataproc ...)

  Note: if the job description lists many separate services (BigQuery, GCS,
  Pub/Sub, Dataproc ...) each one counts as a separate required skill, which
  lowers the required-skills ratio.

WHY EMBEDDINGS AND AN LLM?
  - Embeddings measure OVERALL closeness of the two documents (fast, cheap,
    numeric).
  - The LLM understands SKILL EQUIVALENTS ("PostgreSQL" counts as "SQL"),
    which keyword matching misses.
  Combining both gives a more balanced score than either alone.

GUARDRAILS AGAINST MADE-UP FACTS
  - Every prompt says: use only facts from the resume, never invent skills,
    numbers or experience. Missing metrics become placeholders like [X]%.
  - Small models sometimes ignore that. In testing, an early version of the
    cover letter claimed "reduced pipeline failures by 30%" - a number not in
    the resume. So invented_numbers() scans the letter and shows a warning
    listing any number that appears in neither the resume nor the JD.
  - Always read the letter before sending it.

API CALLS PER ANALYSIS
  5 chat calls + 1 embedding call (rewriting the letter = 1 more call)
  Tested: about 23 seconds end to end.

PRIVACY
  The resume text is sent to the Mistral API. Use your own resume or sample
  data; don't upload other people's personal data without consent.


--------------------------------------------------------------------------------
4. KEY CODE CONCEPTS (both apps)
--------------------------------------------------------------------------------
  ChatMistralAI(model=..., temperature=0.2)
      LangChain wrapper for Mistral chat models. Low temperature = more
      consistent, factual output.

  llm.invoke([SystemMessage(...), HumanMessage(...)])
      System message = instructions/rules, Human message = the data.

  llm.with_structured_output(PydanticClass)
      Returns an instance of the class instead of text (uses Mistral's
      function calling under the hood).

  MistralAIEmbeddings(model="mistral-embed")
      Turns text into a vector of 1,024 numbers; similar texts -> similar
      vectors.

  st.session_state
      Keeps results between Streamlit reruns (every click reruns the script).

  st.cache_data
      Caches the YouTube transcript so the same video isn't fetched twice.

  st.status(...)
      Shows each workflow step live while it runs.


--------------------------------------------------------------------------------
5. TROUBLESHOOTING
--------------------------------------------------------------------------------
  "MISTRAL_API_KEY not found"      -> add it to Practice/.env
  429 Rate limit exceeded          -> the model isn't allowed on your plan, or
                                      too many requests: pick another model in
                                      the sidebar or wait a minute
  403 not available in subscription -> use a ministral-* model
  "Could not get a transcript"     -> the video has no captions, or YouTube
                                      blocked the request
  "Couldn't read enough text"      -> the PDF is scanned (an image); paste the
                                      resume text instead
  ModuleNotFoundError              -> pip install -r "AI WORKFLOW/requirements.txt"


--------------------------------------------------------------------------------
6. IDEAS TO EXTEND
--------------------------------------------------------------------------------
  YouTube notes:
    - Clickable timestamps that jump to that moment in the video
    - Export notes to PDF / Notion
    - Playlist support (notes for every video in a course)
    - Ask questions about the video (add RAG over the transcript)
  Resume matcher:
    - Compare one resume against several job descriptions and rank them
    - Export an updated resume as .docx
    - Save past analyses to a small database
    - Evaluate scoring accuracy against hand-labelled examples


--------------------------------------------------------------------------------
7. RESUME LINES (replace [X] with numbers you actually measure)
--------------------------------------------------------------------------------
  YouTube Study Notes Generator | Python, Streamlit, Mistral AI, LangChain
  - Built an AI workflow that turns YouTube lectures into timestamped study
    notes, flashcards and interactive quizzes using map-reduce summarisation
    and structured LLM output; processes an 18-minute video in ~45 seconds.

  Resume-Job Matcher & Cover Letter Writer | Python, Streamlit, Mistral AI
  - Built a resume analysis tool combining Mistral embeddings (semantic
    similarity) with LLM skill-gap extraction to score resume-job fit, suggest
    tailored bullet rewrites and generate cover letters, with an automated
    guardrail that flags invented metrics.
================================================================================
