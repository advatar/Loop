Claude Code's creator fired himself from prompting. 2 agents now ship his code while he sleeps.
On June 8, 2026, at 12:28 AM, Peter Steinberger — creator of OpenClaw, now at OpenAI — posted 2 sentences that hit 6.5 million views: "You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents." That was it.
2 agents work through the night on Boris Cherny's codebase.
1 hunts for architecture improvements. 1 finds duplicated abstractions and unifies them. Both file pull requests on their own.
They never stop, because the codebase never stops changing.
Cherny built Claude Code as a side project in September 2024. Today it sits behind close to 4% of all public commits on GitHub.
His own job now, in his words: "I don't prompt Claude anymore. I have loops running that prompt Claude and figuring out what to do. My job is to write loops."
The man who built the prompt box fired himself from the prompt box.
That move has a name now. And a market.
Part 1: The money on the table

Cursor hit $300 million ARR in 2 years. Valuation: $2.5 billion to $30 billion in 2025.
Every dollar of that is agents running cycles someone designed once.
Meanwhile, developers still typing prompts one at a time are leaving 90% of the value on the table. The bottleneck moved from model capability to orchestration design.
90%. That's the spread between the prompt writer and the loop writer.
On June 8, Peter Steinberger — creator of OpenClaw, now at OpenAI — posted 2 sentences:
"You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents."
No diagram. No repo link. 6.5 million views.
Part 2: What a loop actually is

A cycle the agent repeats on its own: build, test, revise, continue. You define the goal and the check. It iterates until the check passes.

Image

0:07 / 41:05
Cherny at Meta's @Scale: 'As big as the step from source code to agents was, loops are just as big a step.' At 32:00 — the 2 agents from the top of this article.
Part 3: The 3 loops (Andrew Ng's map)

June 30, The Batch: 3 nested loops, 3 different clocks.
Image
His worked example: a typing app for his daughter, built over a weekend.
A weekend. Not a quarter.
Part 4: The 1 part that pays

Every loop has 5 parts: trigger, state, executor, verifier, stop condition.
The verifier is the whole game.
The model runs cheaply over and over. The verifier decides if any of it ships.
Weak verifier: expensive noise. Strong verifier: pull requests waiting at 7 AM.
Part 5: Your first 30 days

Week 1: 1 agent, 1 task, 1 test as the stop condition. Review every run by hand.
Week 2: Add a checker agent that rejects weak output. 1 does the work, 1 rejects the weak parts.
Week 3: Nightly schedule, morning review. Set a hard token cap — loops have no spending ceiling.
Week 4: Point it at work people pay for: maintenance, security patching, refactors. This is where a loop stops being a demo and starts being a service.
Free starter kit: the loop-engineering repo on GitHub — patterns, templates, 3 CLI tools. Link in reply.
2 years ago, people wrote code by hand. Then agents wrote the code. Now agents prompt agents that write the code.
Each shift paid the people who moved first. This one is 6 weeks old.
You build your own life — so choose the right path.
The loop runs while you sleep. So does the money.
If this was useful — follow.
