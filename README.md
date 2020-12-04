# poker-ml

Repo for a brief foray into the world of poker math. Strategies for agent
design might include:
  - Q learning (Reinforcement Learning)
  - Bayesian Inference
  - RNN / Neural structure

TODO:

Create methods for:
  - Pot Odds: current bet / (pot + current bet)
  - Implied Odds: current bet + later bets + (pot + current bet + later pot)
  - Call Frequency: how often a given player calls bets.
  - Raise Frequency: how often raises
  - Re-Raise Frequency: all re-raises (3, 4, 5 bets)
  - All in Frequency: all ins
  - Bluff Frequency:
  -   only freq. that is unknown.
  -   Can be approximated with bet sizing on known hands
  -   Called bluffs.
