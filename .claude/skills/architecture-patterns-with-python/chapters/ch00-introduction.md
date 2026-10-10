# Introduction: Encapsulation, Layering, and the Dependency Inversion Principle

## Core Idea
A big ball of mud is the natural state of software; preventing it takes energy and direction. The techniques are simple: encapsulate behavior behind abstractions, layer code with rules about who may call whom, and invert dependencies so business code never depends on infrastructure.

## Frameworks Introduced
- **Encapsulation and Abstraction**: encapsulate *behavior* by giving a task to a well-defined object or function (the abstraction). Responsibility-driven design: think in roles/responsibilities (behavior), not data or algorithms.
  - When to use: any time low-level detail clutters intent (urllib → requests → `duckduckgo.query('Sausages')`).
  - How: name the task, hide the mechanics, expose the smallest public API (a function name plus args is enough in Python).
- **Layered Architecture** (UI → business logic → database): divide code into roles and set rules on which may call which. Part I of the book "turns this model inside out".
- **Dependency Inversion Principle (DIP)**: (1) High-level modules should not depend on low-level modules; both depend on abstractions. (2) Abstractions should not depend on details; details depend on abstractions.
  - High-level = what the business cares about (patients, trades, payroll). Low-level = what it doesn't (filesystems, sockets, SMTP, HTTP, AMQP, cron vs Kubernetes).
  - "Depends on" means *knows about or needs*, not merely imports/calls.
  - Why: high-level code should change fast with the business; low-level code (a DB column rename = migration + deploy) changes slowly. An abstraction in between lets each change independently.
- **Domain Model** replaces the vague "business logic layer": one place for all business logic, kept free of low-level concerns.

## Key Concepts
- **Ball of mud**: dependency graph out of control; changing one node ripples everywhere.
- **Abstraction**: simplified interface that encapsulates behavior.
- **ABC vs duck typing**: ABCs are optional in Python; "the public API of the thing you're using" is enough.
- **SOLID**: Robert Martin's five OO principles; DIP is the D.
- **Behavior first**: behavior should drive storage requirements, not the reverse.

## Mental Models
- Use abstraction when you can name a task and hide how it is done.
- Think of business logic scattered across layers as the primary cause of bad designs.
- "All problems in computer science can be solved by another level of indirection" (Wheeler) — but each layer has a cost (see trade-off questions in later chapters).

## Anti-patterns
- **Schema-first design**: building the DB schema first and treating the object model as an afterthought.
- **Business logic leaking across layers**: hard to find, understand, change.

## Key Takeaways
1. Apply DIP everywhere: domain code depends on nothing infrastructural.
2. Part I patterns: Repository (storage abstraction), Service Layer (use case boundary), Unit of Work (atomic operations), Aggregate (data integrity).
3. Always ask of every pattern: what do we get, and what does it cost?

## Connects To
- **Ch 1**: building the domain model. **Ch 3**: heuristics for choosing abstractions. **Ch 4**: concrete DIP example.
