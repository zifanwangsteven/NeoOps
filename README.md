See it live on [NeoOps](https://www.n3-neoops.com/)
---

## Smart Contract
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

### BINANCE API, ORACLE CALL & PAYOUT
NeoOps uses binance API as its external price data source. The url and jsonPath filter we use to retrieve the price at expiry is `https://api.binance.com/api/v3/aggTrades?symbol=${symbol}&startTime=${expiry - 1000}&endTime=${expiry}` and `$[-1:]..p`, namely, we retrieve the trade information of the symbol on the last second before expiry and extract the last trade available to us as the spot price. After expiry, the pool owner makes an oracle request to feed in the external data and call on the payout function to finalize returns. NeoOps adopts a 'The-winner-takes-it-all' policy when it comes to profit distribution, namely, the winning position (long or short) will equally split the entire margin pool (with a slight commission discounted to the pool owner and NeoOps) while the other position loses its margin. 

### COMMISSIONS AND PENALTIES
NeoOps requires a minimum of 10 GAS tokens deposits to be put down as good faith money from pool owners. This deposit will be charged a 0.2% commision by NeoOps if the pool executes the payout function susccessfully. This deposit will be forfeited should the owner cancel on the pool before expiry. A player will be charged a 0.3% penalty on his / her margins on cancellation.On payout, NeoOps and the pool owner is entitled to respectively a 0.1% commission and 0.2% commission. In the event that there are no winning positions settled, NeoOps and the pool manager will split the total margin.
## Frontend
NeoOps also provides a friendly frontend interface as an entry point for our less tech-savy users. The frontend interface is build with Element UI on Vue.js and NeoLine dAPI. To be able to use our frontend interface, make sure you are using Chrome as your browser and have NeoLine installed.

When creating pools, please input values as in NUM * 10 ^ Decimal. (e.g. for GAS tokens: 10 * 10 ^ 8)
