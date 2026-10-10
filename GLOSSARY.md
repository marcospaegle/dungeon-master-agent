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
