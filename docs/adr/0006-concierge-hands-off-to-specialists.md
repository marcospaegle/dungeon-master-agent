# A Concierge hands the conversation to Specialists

Supersedes [0005](0005-commands-only-start-agents.md).

The user no longer types `/char` to reach an Agent. They talk in plain
language to the Concierge, an Agent with one Tool, `hand_off`, that
decides which Specialist (today the Character Builder) should have the
conversation. The Tool only marks the Reply; the Chat starts the
Specialist and makes it the Active Agent, so Agents never know about
each other and the Chat still owns the flow. The Specialist's first
input is the user's own message plus the Concierge's brief. It hands
the conversation back when its task is done, when it calls its
`return_to_concierge` Tool, or when the user types `/exit`, and the
Concierge's thread gets a one-line outcome (transcripts stay
separate). If a Specialist cannot start, the Chat shows the error and
the Concierge stays active and is told. The Commands that remain are
the Chat's own: `/help`, `/exit` and `/quit`.

We chose a handoff over Deep Agents sub-agent delegation because
sub-agents are one-shot, while Character creation and the Adventure
creator planned next are long multi-turn conversations with their own
prompts and interrupts. Delegation would make the Concierge run every
such conversation and shrink the Specialists to helpers. We chose a
neutral Concierge over making the Dungeon Master the orchestrator
because the Dungeon Master runs a D&D session, and preparation tasks
should not blur that role. The Concierge uses the same model as the
other Agents; that can change later without touching this decision.

The Concierge also answers general questions about D&D 5.5e, with
the `search_rules` Tool and no other Tool besides `hand_off`, and
declines anything that is not about D&D. This replaces the first
version of this decision, where it had no rules Tools and a rules
question needed a Specialist. Its search needs the embedding key, so
the Concierge cannot start without it; a missing index is reported to
the Agent by the Tool, so handoffs still work.

It costs one extra model call to route a request.
