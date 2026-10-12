# Commands only start Agents; Agents and the Chat own the flow

A Command (`/char`) does nothing but name the Agent to start. The
multi-step flow it used to hold, picking a saved Character and
confirming the save, moves into the Agent as Tools and interrupts.
The Chat holds the Active Command, routes text to its Agent and turns
an interrupt into a question for the user, so every Frontend behaves
the same.

We chose this over Commands that own their flow because a Command with
its own state machine duplicates what the Agent already does, and a
second Agent would need a second state machine. It costs a less
predictable flow: the Agent asks which Character to edit in words
instead of showing a numbered menu.
