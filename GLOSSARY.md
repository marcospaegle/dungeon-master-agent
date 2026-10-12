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
tools: today the Character Builder, later a Dungeon Master that runs a
D&D session. An Agent is limited to its task and turns the user's
messages into replies.

**Tool**:
Something an Agent can call to look up or change something, such as
searching the rules or saving a Character. Tools are shared: any
Agent can be given any Tool, and an Agent has only the Tools it is
given.

**Chat**:
A running conversation between one user and the program in a
Frontend. It routes the user's text to the Active Command's Agent.
Lives only as long as the program runs. Not a D&D game session.

**Command**:
A chat input starting with `/` that only starts something, such as
`/char` starting the Character Builder. It does no work itself: the
work belongs to the Agent it starts. It does not depend on the
Frontend that runs it.

**Active Command**:
The Command whose Agent receives text that is not a Command, from
when it starts until it finishes or the user leaves it with `/exit`.

**Character**:
A player character: the choices that define it (race, class,
abilities, background and so on) and the numbers derived from them. It
is the single source for the Character sheet.

**Character sheet**:
The printable form a Character is written onto. The blank form is the
template; the filled-in copy is the output.

**Character creation**:
The Command (`/char`) in which the user builds a new Character or
edits an existing one with the Character Builder. Ends with the user
confirming the Character, which produces its Character sheet.

**Character Builder**:
The Agent that guides the user through Character creation and does
nothing else.

**Eval**:
A scripted scenario that scores the Character creation agent: the
runner plays fixed user replies against it and applies checks to the
saved Character, and a judge model (set apart from the model under
test) that grades the transcript against a rubric. Run with
`uv run python -m evals`, never by pytest, because it calls a real
model.

**Judge**:
The model that grades an Eval's transcript against the Rubric, set
apart from the model under test (`EVAL_JUDGE_MODEL`). It sees only the
transcript text, so it can judge whether a cited Page is plausible but
not whether it exists.

**Rubric**:
The Criteria a Judge grades a transcript on: a common set for every
Eval plus those of the case. Each Criterion's verdict is a check in
the run's results.
