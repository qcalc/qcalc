# AI Agent Token Cost Estimator

## Purpose

`token_cost()` estimates the input, output, and total API cost of an AI agent
over multiple calls or rounds.

It supports two common request patterns:

- **Full history resent**: each call includes the growing conversation history.
- **Only current input**: each call includes the initial context and only that
  round's new input.

The estimate assumes the same number of new input and output tokens in every
round.

---

## Inputs

- **Number of rounds**: The number of API calls.

- **Initial context tokens**: Tokens sent as fixed context on every call, such as the system prompt, instructions, tool definitions, or other unchanged context.

- **New input tokens per round**: New user, tool, or other input tokens added during each round. 

- **Output tokens per round**: Assistant output tokens generated during each round.

- **Input price per million**: The provider's price for one million input tokens. 

- **Output price per million**: The provider's price for one million output tokens.

- **Input mode**: a) `Full history resent` (default) - each request includes the initial
  context, all inputs through the current round, and all earlier assistant
  outputs. b) `Only current input` - each request includes the initial context
  and only the current round's new input.

---

## Results

The calculator returns:

- **Cumulative Input Tokens**
- **Cumulative Output Tokens**
- **Input Cost**
- **Output Cost**
- **Total Estimated Cost**

Costs are returned in USD.

---

## How the Estimate Is Calculated

Let:

- `n` = number of rounds
- `S` = initial context tokens
- `u` = new input tokens per round
- `v` = output tokens per round
- `P_i` = input price per million tokens
- `P_o` = output price per million tokens

### Only current input

\[
I_{\text{total}} = n(S + u)
\]

### Full history resent

At round `k`, the request contains:

\[
I_k = S + ku + (k-1)v
\]

Therefore:

\[
I_{\text{total}} =
n(S+u) + \frac{n(n-1)}{2}(u+v)
\]

For either mode:

\[
O_{\text{total}} = nv
\]

\[
C =
\frac{P_i I_{\text{total}} + P_o O_{\text{total}}}{10^6}
\]

The current-input estimate grows linearly with the number of rounds. The
full-history estimate has a quadratic input component because earlier messages
are billed again when resent.

---

## Example

With the defaults, `full` mode estimates `227,500` input tokens, `10,000`
output tokens, and a total cost of `1.11 USD`. Using `current` mode reduces the
input total to `85,000` tokens and the estimated cost to `0.54 USD`.

---

## Notes and Limitations

- The calculator uses fixed token counts per round; actual conversations
  usually vary by call.
- Prompt caching, cached-input discounts, batch pricing, tool charges, and
  other provider-specific pricing are not included.
- In full-history mode, all resent input is priced at the standard input rate,
  so the result is an uncached baseline.
- Use token counts reported by the API for the most accurate final cost.
