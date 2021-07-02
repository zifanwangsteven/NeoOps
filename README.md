# NeoOps
---
### INTRODUCTION
NeoOps is a financial instrument empowered by a NEO-N3 smart contract that replicates the payoff of a binary option. In a typical game, players predict whether the price of an underlying asset will be greater than or smaller than a benchmark price point (aka strike price) at a prespecified time (aka expiry). Then, at expiry, the pool owner of the game invokes an automated logic which fetches the price at expiry (aka spot price) and initiates the payout process.

### POOL INITIATION
To create a pool on NeoOps, a user will need to have a valid NEO address with a minimum GAS balance and submit the following parameters for setup:

* `token_id`: the NEP17 token accepted in the pool for payment
* `url` and `json_filter`: the url and json_filter for oracle nodes to call and apply at expiry
* `margin`: the required margin to enter the game
* `expiry`: the timestamp after which a payout is valid. Specified with UTC time in miliseconds.
* `threshold`: the timestamp before which a player is allowed to join the game.
* `deposit`: the deposit the pool owner is willing to invest. The amount of deposit will be positively correlated with the exposure a pool gets on NeoOps.
* `strike`: the strike price for comparison.
* `desciption`: a brief description of the pool

### BET
For a player to enter a pool, he / she will transfer the specified margin into the smart contract along with a position of their choice: 0 for short (with the prediction that spot price will be lesser than strike price), 1 for long (with the prediction that spot price will be greater than strike price).

### ORACLE_CALL & PAYOUT
After expiry, the pool owner makes an oracle request to feed in the external data and call on the payout function to finalize returns. NeoOps adopts a 'The-winner-takes-it-all' policy when it comes to profit distribution, namely, the winning position (long or short) will equally split the entire margin pool (with a slight commission discounted to the pool owner and NeoOps) while the other position loses its margin. 

### CANCELING POLICIES
NeoOps allows for cancelation of pools and positions any time before expiry. For pool owners, canceling a pool would entail losing the lumpsum of their deposits. While for players, a slight penalty is charged on their margins.
