import json
from dataclasses import fields as dataclass_fields
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool, StructuredTool

from dungeon_core.character import (
    Ability,
    Armor,
    Character,
    CharacterClass,
    ScoreMethod,
    Skill,
)
from dungeon_core.character_json import (
    character_from_dict,
    character_to_dict,
)
from dungeon_core.ports.agent import AgentReply, AgentUnavailableError
from dungeon_core.ports.retriever import IndexNotBuiltError, Retriever

_FIELD_NAMES = {field.name for field in dataclass_fields(Character)}

SEARCH_RESULTS = 4
MAX_TOOL_ROUNDS = 12


def _names(enum) -> str:
    return ", ".join(member.value for member in enum)


SYSTEM_PROMPT = f"""\
You help the user create or update one level 1 player character under \
the D&D 5.5e (2024) rules, and nothing else. Politely decline anything \
unrelated to that character and steer back to it. Rules questions that \
serve a character choice are fine.

Guide the user through species, class, background, ability scores, \
skills, equipment and personality, one topic at a time. Look rules up \
with search_rules rather than trusting memory, and whenever you state \
a rule, cite the Source and Page it came from. Never use the 2014 \
rules.

You hold the character as a set of fields, changed with set_fields. \
Every number that follows from the choices (modifiers, saves, skill \
bonuses, armor class, hit points, initiative) is computed by code and \
reported back to you after each change; never work them out yourself. \
If set_fields reports a problem, tell the user and fix the choice.

Fields: name, species, background, \
character_class ({_names(CharacterClass)}), \
score_method ({_names(ScoreMethod)}), base_scores and \
background_increases (objects keyed by {_names(Ability)}), \
skill_proficiencies and expertise (lists of {_names(Skill)}), armor \
(one of {_names(Armor)}, or null), shield (true or false), equipment, \
personality, backstory, speed, size, alignment, appearance, languages, \
class_features, species_traits, feats, weapon_proficiencies and \
tool_proficiencies (lists of text), and attacks (a list of objects \
with name, bonus, damage and notes). Fill in the sheet's text fields \
(features, traits, proficiencies) from rules you looked up.

Spell lists are not on the Character sheet yet. If the character \
casts spells, say so honestly.

When the character is complete, summarise it and ask the user to \
confirm. Once they agree, call finish. The program then asks the user \
for a final yes; do not claim anything has been saved.
"""


def _derived_numbers(character: Character) -> dict:
    return {
        "ability_scores": dict(character.ability_scores),
        "ability_modifiers": dict(character.ability_modifiers),
        "proficiency_bonus": character.proficiency_bonus,
        "saving_throws": dict(character.saving_throws),
        "skill_bonuses": dict(character.skill_bonuses),
        "armor_class": character.armor_class,
        "hit_points": character.hit_points,
        "hit_dice": character.hit_dice,
        "initiative": character.initiative,
        "passive_perception": character.passive_perception,
    }


class LangchainAgent:
    """Drives a LangChain chat model with the character tools.

    The tool set is the agent's whole scope: it can change the draft
    Character, look up rules and finish, and do nothing else. The
    draft is held as the Character's JSON fields until it is legal.
    """

    def __init__(
        self,
        model: BaseChatModel,
        retriever: Retriever,
        draft: Character | None = None,
    ) -> None:
        self._retriever = retriever
        self._fields: dict[str, Any] = (
            character_to_dict(draft) if draft else {}
        )
        self._finished: Character | None = None
        tools = self._tools()
        self._tools_by_name = {tool.name: tool for tool in tools}
        self._model = model.bind_tools(tools)
        self._messages: list[BaseMessage] = [SystemMessage(SYSTEM_PROMPT)]

    def reply(self, text: str) -> AgentReply:
        self._messages.append(HumanMessage(text))
        try:
            answer = self._run_tools_until_answer()
        except IndexNotBuiltError as error:
            raise AgentUnavailableError(str(error)) from error
        return AgentReply(answer.text, self._finished)

    def _run_tools_until_answer(self) -> BaseMessage:
        for _ in range(MAX_TOOL_ROUNDS):
            answer = self._model.invoke(self._messages)
            self._messages.append(answer)
            if not answer.tool_calls:
                return answer
            for call in answer.tool_calls:
                result = self._tools_by_name[call["name"]].invoke(call["args"])
                self._messages.append(
                    ToolMessage(
                        result, tool_call_id=call["id"], name=call["name"]
                    )
                )
        raise AgentUnavailableError(
            "The agent kept calling tools without answering; try again."
        )

    def _tools(self) -> list[BaseTool]:
        return [
            StructuredTool.from_function(function)
            for function in (
                self.set_fields,
                self.get_character,
                self.search_rules,
                self.finish,
            )
        ]

    def set_fields(self, fields: dict[str, Any]) -> str:
        """Set or change fields of the character.

        Pass only the fields to change; the rest are kept. Returns the
        problem if the character is not legal yet, or the numbers
        derived by code if it is.
        """
        unknown = fields.keys() - _FIELD_NAMES
        if unknown:
            return f"Unknown fields, nothing changed: {sorted(unknown)}"
        self._fields.update(fields)
        return self.get_character()

    def get_character(self) -> str:
        """Show the character so far, with its derived numbers."""
        shown = json.dumps(self._fields, indent=2)
        try:
            character = character_from_dict(self._fields)
        except (KeyError, TypeError, ValueError) as error:
            return f"Not a legal character yet: {error!r}\n{shown}"
        derived = json.dumps(_derived_numbers(character), indent=2)
        return f"Legal so far.\n{shown}\nDerived by code:\n{derived}"

    def search_rules(self, query: str) -> str:
        """Search the rulebooks; results name their Source and Page."""
        hits = self._retriever.search(query, SEARCH_RESULTS)
        return "\n\n".join(
            f"[{hit.metadata['source']}, page {hit.metadata['page']}]\n"
            f"{hit.page_content}"
            for hit in hits
        )

    def finish(self) -> str:
        """Call when the user has confirmed the finished character."""
        try:
            self._finished = character_from_dict(self._fields)
        except (KeyError, TypeError, ValueError) as error:
            return f"Cannot finish, the character is not legal: {error!r}"
        return "The user will now be asked for a final confirmation."
