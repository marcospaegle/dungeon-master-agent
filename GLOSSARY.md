# Glossary

**Indexing**:
Preparing source material for retrieval: loading it, splitting it into
chunks, embedding the chunks and storing them. Consuming the index is a
separate, later concern.

**Chunk**:
A piece of a document small enough to embed and retrieve on its own.

**Document**:
One page of a Source, as loaded and before splitting.

**Source**:
A PDF file the index is built from.

**Page**:
A position in a Source, counted from 1 as a PDF viewer shows it. It
can differ from the number printed on the page.

**Source folder**:
The single directory whose top-level PDFs are the Sources. Subfolders
are not read.

**Storage folder**:
The directory that holds the Sources, the vector store and the logs.

**Rebuild**:
Indexing from scratch, discarding everything already indexed. Needed
when the Sources, the chunking or the embedding model change.
Otherwise indexing only adds the Chunks not yet indexed, which is how
an interrupted run is finished.

**Frontend**:
A way of talking to the program: the terminal chat, a web API or a
Discord bot. Every Frontend is a thin layer over the same Core and
holds no rules of its own.

**Core**:
Everything the Frontends share: the Agents, the Characters, the
knowledge from the Sources and the Chat routing. It knows nothing
about any Frontend.

**Agent**:
A worker that does one task very well, with its own instructions and
tools: the Concierge or a Specialist. An Agent is limited to its task
and turns the user's messages into replies.

**Tool**:
Something an Agent can call to look up or change something, such as
searching the rules or saving a Character. Tools are shared: any
Agent can be given any Tool, and an Agent has only the Tools it is
given.

**Chat**:
A running conversation between one user and the program in a
Frontend. It routes the user's text to the Active Agent. Lives only as
long as the program runs. Not a D&D game session.

**Concierge**:
The Agent the user talks to by default. It understands what the user
wants and hands the conversation to the Specialist that does it. It
does no specialist work itself.

**Specialist**:
An Agent that does one task and is reached through a Handoff from the
Concierge: today the Character Builder, later an Adventure creator and
a Dungeon Master.

**Handoff**:
The Concierge giving the conversation to a Specialist, because of what
the user said and not because of a Command. The Specialist has the
conversation until it finishes, gives it back because the user asked
for something outside its task, or the user leaves with `/exit`. Then
the Concierge has it again.

**Outcome**:
One line a Specialist leaves with the Concierge when the conversation
comes back, such as a Character being saved or the user leaving
without finishing. The Concierge hears it with the user's next
message. A Specialist that cannot start or stops is reported the same
way.

**Active Agent**:
The Agent that receives the user's text that is not a Command: the
Specialist after a Handoff, otherwise the Concierge.

**Command**:
A chat input starting with `/` that the Chat answers itself: `/help`,
`/exit` and `/quit`. A Command never starts an Agent. It does not
depend on the Frontend that runs it.

**Character**:
A player character: the choices that define it (race, class,
abilities, background and so on) and the numbers derived from them. It
is the single source for the Character sheet.

**Character sheet**:
The printable form a Character is written onto. The blank form is the
template; the filled-in copy is the output.

**Character creation**:
The task in which the user builds a new Character or edits an
existing one with the Character Builder, reached by a Handoff. Ends
with the user confirming the Character, which produces its Character
sheet.

**Character Builder**:
The Agent that guides the user through Character creation and does
nothing else.
