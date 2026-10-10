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

**Chat**:
The running conversation between the user and the program, started by
`dungeon chat`. Lives only as long as the program runs. Not a D&D
game session.

**Command**:
A chat input starting with `/` that selects what the chat does, such
as `/char`. Text that is not a Command is addressed to the active
Command, if any.

**Character**:
A player character: the choices that define it (race, class,
abilities, background and so on) and the numbers derived from them. It
is the single source for the Character sheet.

**Character sheet**:
The printable form a Character is written onto. The blank form is the
template; the filled-in copy is the output.

**Character creation**:
The Command (`/char`) in which the user builds a new Character or
edits an existing one with the help of an agent, which is limited to
that task. Ends with the user confirming the Character, which produces
its Character sheet.
