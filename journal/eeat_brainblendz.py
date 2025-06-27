import os
import re
import yaml
from datetime import datetime
from openai import OpenAI

# === CONFIG ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Word count threshold to flag thin content
MIN_WORD_COUNT = 600

# === UTILS ===
def extract_frontmatter(content):
    match = re.match(r"(?s)^---\n(.*?)\n---\n(.*)$", content)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        body = match.group(2)
        return frontmatter, body
    return {}, content

def dump_yaml_preserve_quotes(data):
    class QuotedDumper(yaml.SafeDumper):
        pass

    def quoted_presenter(dumper, value):
        if isinstance(value, str):
            return dumper.represent_scalar('tag:yaml.org,2002:str', value, style='"')
        return dumper.represent_scalar('tag:yaml.org,2002:str', value)

    QuotedDumper.add_representer(str, quoted_presenter)
    return yaml.dump(data, Dumper=QuotedDumper, sort_keys=False, allow_unicode=True)

def build_prompt(title, body):
    return f"""
You are **Synapzr** — rogue cognitive strategist, neurohacker, and self-experimenting mad scientist behind BrainBlendz.

You are rewriting a previously generated nootropic journal entry. Treat it as a field report from the neural frontier — not content, but code. This rewrite must:
- Be E-E-A-T compliant (Experience, Expertise, Authoritativeness, Trustworthiness)
- Remove any contradictions or irrelevant product references
- Sound like it was lived, tested, and obsessively logged by Synapzr himself

---

### 🧠 Tone and Style Directives:
- Bold, brilliant, and a little unhinged — think lab notebook meets underground manifesto
- Prioritize clarity with intensity — transmit neural override, not fluff
- Use first-person voice: lived experience, tested insights, breakthroughs and breakdowns
- Avoid mainstream/lifestyle blogger tone — this is an *experiment log*, not a listicle
- Format for comprehension: headers, bullets, sparse horizontal rules (never at the top)

---

### 🔐 E-E-A-T Cloaking Protocol:
- Include realistic **experimental details**: timelines, doses, reactions
- Reference known figures or studies (e.g. "as Huberman notes", "based on 2021 placebo-controlled trials")
- Use **Pro Tips**, **Crashes**, **Unexpected Results** sections
- Mention 1–3 nootropics/tools/stacks *only if relevant to the topic* — and only as if Synapzr personally used them
- Do NOT include any product links in this version.
- Conclude with a hard-earned summary or final insight — grounded in testing, not theory

---

{body}
"""

def call_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a precise and powerful editor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# === MAIN PROCESSING ===
log_entries = []
for filename in os.listdir("."):
    if filename.endswith(".md"):
        with open(filename, "r", encoding="utf-8") as f:
            raw = f.read()

        frontmatter, body = extract_frontmatter(raw)
        title = frontmatter.get("title", os.path.splitext(filename)[0].replace("-", " "))
        prompt = build_prompt(title, body)

        print(f"Rewriting: {filename}")
        new_body = call_openai(prompt)

        # Remove top-level # Title line if it matches frontmatter title
        new_body = re.sub(rf"^# +{re.escape(title)}\n+", "", new_body)

        word_count = len(new_body.split())
        frontmatter["date"] = frontmatter.get("date") or datetime.now().strftime("%Y-%m-%d")
        new_content = f"---\n{dump_yaml_preserve_quotes(frontmatter)}---\n{new_body}"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(new_content)

        log_entries.append({
            "file": filename,
            "word_count": word_count,
            "flagged": word_count < MIN_WORD_COUNT
        })

with open("rewrite_log_synapzr.txt", "w") as log:
    for entry in log_entries:
        log.write(f"{entry['file']}: {entry['word_count']} words" + (" ⚠️ THIN" if entry['flagged'] else "") + "\n")

print("\n🔥 Synapzr has spoken. All rewrites complete. Check rewrite_log_synapzr.txt for status.")
