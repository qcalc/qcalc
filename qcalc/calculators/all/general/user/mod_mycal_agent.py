# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json

from calc import get_code
from calc.mod_cache import QMyCalAI
from calc.mod_openai import ask_gpt
from qconst import CODE_BLOCK_PATTERN
from qenv import PROJ_DIR
from qutil import css2strs, ensure_info_function, format_py_code

from .cal_mycal import validate_calculator_defaults, validate_calculator_info

_MAX_REFERENCE_CALS = 3
_MAX_REFERENCE_CODE_CHARS = 6000
_MAX_CONTEXT_TURNS = 6
_CREATION_SPEC_PATH = PROJ_DIR.path(
    'qcalc_res', 'train', 'qcalc-calculator-creation-spec.md'
)

with open(str(_CREATION_SPEC_PATH), encoding='utf-8') as _creation_spec_file:
    _CALCULATOR_CREATION_SPEC = _creation_spec_file.read().strip()


_AGENT_ACTIONS = {'answer', 'ask_user', 'propose_code'}


class AIGenerationError(ValueError):
    def __init__(self, message, prompt='', code=''):
        super().__init__(message)
        self.prompt = prompt
        self.code = code


class AgentResponse:
    def __init__(self, action, message='', code='', prompt='', validation_error=''):
        self.action = action
        self.message = message
        self.code = code
        self.prompt = prompt
        self.validation_error = validation_error


class MyCalAgent:
    @staticmethod
    def _extract_python_code(text):
        if not isinstance(text, str):
            raise ValueError('AI response is not text')

        stripped = text.strip()
        match = CODE_BLOCK_PATTERN.search(stripped)
        if match:
            stripped = match.group(1).strip()

        if stripped == '':
            raise ValueError('AI response did not contain Python code')
        return stripped

    @classmethod
    def _parse_agent_response(cls, text):
        if not isinstance(text, str):
            raise ValueError('AI response is not text')

        stripped = text.strip()
        if stripped.startswith('```'):
            lines = stripped.splitlines()
            if lines and lines[-1].strip() == '```':
                lines = lines[1:-1]
                stripped = '\n'.join(lines).strip()

        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            if 'def ' in stripped or stripped.startswith(('import ', 'from ')):
                return AgentResponse('propose_code', code=cls._extract_python_code(text))
            return AgentResponse('answer', message=stripped)

        if not isinstance(payload, dict):
            return AgentResponse('answer', message=stripped)

        action = str(payload.get('action', '')).strip()
        message = str(payload.get('message', '') or '').strip()
        code_value = (
            payload.get('code')
            or payload.get('calculator_code')
            or payload.get('python_code')
            or ''
        )
        code = str(code_value).strip()

        if action not in _AGENT_ACTIONS:
            action = 'answer'

        if action == 'propose_code' and not code:
            if 'def ' in message or message.startswith(('import ', 'from ', '```python')):
                code = cls._extract_python_code(message)
                message = ''
            else:
                return AgentResponse(
                    'answer',
                    message=message or (
                        'I could not produce calculator code in this response. '
                        'Please use Continue with AI to try again or clarify the request.'
                    ),
                )

        if action != 'propose_code' and code:
            message = '\n\n'.join(part for part in (message, code) if part)
            code = ''
        elif action != 'propose_code':
            code = ''
        if not message and not code:
            return AgentResponse(
                'answer',
                message='The agent returned an empty response. Please use Continue with AI to try again.',
            )
        return AgentResponse(action, message=message, code=code)

    @staticmethod
    def _validate_code(code):
        validate_calculator_info(code)
        validate_calculator_defaults(code)

    @staticmethod
    def _load_reference_context(reference_cals):
        names = list(dict.fromkeys(css2strs(reference_cals)))[:_MAX_REFERENCE_CALS]
        if not names:
            return ''

        blocks = []
        missing = []
        for cal_name in names:
            code = get_code(cal_name, show_meta=True)
            if not code:
                missing.append(cal_name)
                continue
            clipped = code[:_MAX_REFERENCE_CODE_CHARS].strip()
            blocks.append(f'# Reference calculator: {cal_name}\n{clipped}')

        if not blocks:
            missing_text = ', '.join(missing) if missing else ', '.join(names)
            return f'Reference calculators requested but not found: {missing_text}'

        context = '\n\n'.join(blocks)
        if missing:
            context += f"\n\n# Missing reference calculators: {', '.join(missing)}"
        return context

    @staticmethod
    def _conversation_context(state):
        turns = state.get('turns', [])[-_MAX_CONTEXT_TURNS:]
        if not turns:
            return ''

        messages = []
        for turn in turns:
            user_prompt = turn.get('user_prompt', '').strip()
            assistant_message = turn.get('assistant_message', '').strip()
            action = turn.get('action', 'answer')
            validation_error = turn.get('validation_error', '').strip()
            if turn.get('kind') == 'continue' and user_prompt:
                messages.append(f'User: {user_prompt}')
            if assistant_message:
                messages.append(f'Assistant ({action}): {assistant_message}')
            if validation_error:
                messages.append(f'Validation: {validation_error}')

        if not messages:
            return ''

        return f"""
Recent conversation in this calculator task:
{chr(10).join(messages)}
""".strip()

    @classmethod
    def _build_prompt(cls, user_prompt, current_code, validation_error='',
                      reference_context='', state=None, mode='draft'):
        state = state or {}
        reference_section = ''
        if reference_context.strip():
            reference_section = f"""
Reference implementations (style and structure only):
{reference_context}
""".strip()

        continuation_section = ''
        if mode == 'continue':
            original_request = state.get('original_prompt', '').strip()
            previous_code = state.get('latest_code', '').strip()
            conversation = cls._conversation_context(state)
            continuation_section = f"""
Original calculator request:
{original_request}

{conversation}

Previous AI-generated code:
{previous_code}

Continuation rules:
- Treat the current editor code as authoritative because the user may have edited it.
- Preserve the original intent and prior accepted instructions.
- Make the smallest changes needed for the current instruction.
- Preserve unrelated behavior, inputs, outputs, and metadata.
""".strip()

        return f"""
You are generating Python calculator code for a qCalc FRONTEND calculator edited in mycal() or mycal2().
Follow frontend requirements in the specification and ignore backend-only implementation details.

qCalc calculator creation specification:
{_CALCULATOR_CREATION_SPEC}

Choose exactly one action:
- answer: answer the user's question without changing code.
- ask_user: ask one focused clarification needed before changing code.
- propose_code: create, enhance, or repair calculator code.

Return ONLY one JSON object with this shape:
{{
  "action": "answer | ask_user | propose_code",
  "message": "The complete conversational response in Markdown",
  "code": "Complete Python calculator code, or an empty string"
}}

Response rules:
- For answer or ask_user, put the entire response in message and leave code empty.
- The message may contain explanations, equations, lists, inline code, or fenced code examples.
- For propose_code, code MUST contain the complete calculator code.
- Never put explanatory examples or partial code snippets in code.
- Do not wrap the JSON or code in Markdown fences.
- Code must define one main calculator function and matching __info function.
- Allowed meta functions: __info, __input, __modify, __command, __help.
- Keep function defaults runnable without required arguments.
- __info must return a dict and include at least 'title'.
- Ask for clarification instead of guessing when a missing decision materially affects behavior.
- In conversational messages, format math as LaTeX using $...$ inline or $$...$$ for display.

{continuation_section}

Current user instruction:
{user_prompt}

{reference_section}

Current editor code:
{current_code}

Validation error:
{validation_error}
""".strip()

    @classmethod
    def _generate_response(cls, user_prompt, current_code, cal_name_hint='',
                           max_attempts=1, reference_context='', state=None,
                           mode='draft'):
        prompt = user_prompt.strip()
        if prompt == '':
            raise ValueError('Please provide AI prompt')

        draft = current_code
        last_error = ''
        last_prompt = ''
        last_response = None
        for _ in range(max_attempts):
            ai_prompt = cls._build_prompt(
                prompt,
                draft,
                last_error,
                reference_context=reference_context,
                state=state,
                mode=mode,
            )
            last_prompt = ai_prompt
            try:
                generated = ask_gpt(ai_prompt, temperature=0.2)
                response = cls._parse_agent_response(generated)
                response.prompt = ai_prompt
                last_response = response
                if response.action != 'propose_code':
                    return response

                draft = cls._extract_python_code(response.code)
                response.code = draft
                draft, _functions = ensure_info_function(draft, cal_name_hint)
                response.code = draft
                draft = format_py_code(draft)
                response.code = draft
                cls._validate_code(draft)
                return response
            except Exception as e:
                last_error = str(e)
                if last_response is not None:
                    last_response.validation_error = last_error

        if last_response is not None:
            last_response.prompt = last_prompt
            return last_response

        raise AIGenerationError(
            f'AI did not return usable code after {max_attempts} attempt(s): {last_error}',
            prompt=last_prompt,
        )

    @staticmethod
    def _save_turn(state, user_prompt, response, kind='continue'):
        turns = state.get('turns', [])
        turns.append({
            'kind': kind,
            'user_prompt': user_prompt,
            'action': response.action,
            'assistant_message': response.message,
            'response_code': response.code,
            'validation_error': response.validation_error,
        })
        latest_code = response.code or state.get('latest_code', '')
        state.update({
            'latest_code': latest_code,
            'latest_error': response.validation_error,
            'turns': turns,
            'iteration': state.get('iteration', 0) + 1,
        })
        QMyCalAI.setp(state)

    @staticmethod
    def get_history():
        state = QMyCalAI.getp({})
        return list(state.get('turns', []))

    @staticmethod
    def reset():
        QMyCalAI.clear()

    @classmethod
    def send(cls, user_prompt, current_code, cal_name_hint='',
             reference_cals='', max_attempts=1):
        if user_prompt.strip() == '':
            raise ValueError('Please enter an agent message')

        if QMyCalAI.getp({}):
            return cls.continue_task(
                user_prompt,
                current_code,
                cal_name_hint=cal_name_hint,
                reference_cals=reference_cals,
                max_attempts=max_attempts,
            )

        return cls.draft(
            user_prompt,
            current_code,
            cal_name_hint=cal_name_hint,
            reference_cals=reference_cals,
            max_attempts=max_attempts,
        )

    @classmethod
    def draft(cls, user_prompt, current_code, cal_name_hint='',
              reference_cals='', max_attempts=1):
        prompt = user_prompt.strip()
        if prompt == '':
            raise ValueError('Please provide AI prompt')

        QMyCalAI.clear()
        state = {
            'original_prompt': prompt,
            'reference_cals': reference_cals,
            'latest_code': '',
            'latest_error': '',
            'turns': [],
            'iteration': 0,
        }
        QMyCalAI.setp(state)
        reference_context = cls._load_reference_context(reference_cals)

        try:
            response = cls._generate_response(
                prompt,
                current_code,
                cal_name_hint=cal_name_hint,
                max_attempts=max_attempts,
                reference_context=reference_context,
                state=state,
                mode='draft',
            )
            cls._save_turn(state, prompt, response, kind='draft')
            return response
        except AIGenerationError as e:
            raise

    @classmethod
    def continue_task(cls, user_prompt, current_code, cal_name_hint='',
                      reference_cals='', max_attempts=1):
        state = QMyCalAI.getp({})
        prompt = user_prompt.strip()
        history_prompt = prompt
        if prompt == '':
            try:
                cls._validate_code(current_code)
                response = AgentResponse(
                    'answer',
                    message='Code is already valid',
                )
                cls._save_turn(state, history_prompt, response)
                return response
            except Exception as e:
                prompt = (
                    'Fix this qCalc calculator code without changing the intended '
                    f'behavior. Current validation error: {e}'
                )

        if not state:
            state = {
                'original_prompt': prompt,
                'reference_cals': reference_cals,
                'latest_code': current_code,
                'latest_error': '',
                'turns': [],
                'iteration': 0,
            }
            QMyCalAI.setp(state)

        effective_references = reference_cals or state.get('reference_cals', '')
        reference_context = cls._load_reference_context(effective_references)
        state['reference_cals'] = effective_references

        try:
            response = cls._generate_response(
                prompt,
                current_code,
                cal_name_hint=cal_name_hint,
                max_attempts=max_attempts,
                reference_context=reference_context,
                state=state,
                mode='continue',
            )
            cls._save_turn(state, history_prompt, response)
            return response
        except AIGenerationError as e:
            raise
