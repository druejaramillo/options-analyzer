# Options Analysis

## Table of Contents

- [Overview](#overview)
- [Options Strategies Analysis](#options-strategies-analysis)
    - [Common Strategies](#common-strategies)
        - [Bullish](#bullish)
        - [Neutral](#neutral)
        - [Bearish](#bearish)
    - [Analysis Process](#analysis-process)
- [Main Scripts](#main-scripts)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
- [Usage](#usage)

## Overview

Options provide a trading avenue that requires a lower initial investment than traditional stock investing and allows for more advanced trading strategies that are both directional and volatility-based. There is a particular set of options strategies that are widely known and tested. However, for the average trader, the process of setting up a potential trade, analyzing its properties (specifically, its statistical properties), and evaluating it in the context of other possible trades can be extremely time-consuming and tedious.

This project aims to alleviate this burden (at least for myself). By automating the generation, analysis, and evaluation of potential trades, the trader only has to take the time to execute the trades and manage the overall portfolio. This also helps take the trader's emotions out of the trades. The end goal is to achieve more consistent profitability.

## Options Strategies Analysis

### Common Strategies

The following is a description of some of the most common options strategies (specifically, the ones analyzed in this project). For more in-depth explanations and analyses, see [Option Alpha](https://optionalpha.com/) and [tastylive](https://www.tastylive.com/).

Note the following terms:
- ITM: "in the money," referring to options whose strike price is either above the current stock price (for put options) or below the current stock price (for call options).
- ATM: "at the money," referring to options whose strike price is (roughly) equal to the current stock price.
- OTM: "out (of) the money," referring to options whose strike price is either below the current stock price (for put options) or above the current stock price (for call options).
- DTE: "days to expiration," referring to the number of days until the option contract expires.

#### Bullish

- Jade Lizard (Custom Naked Put)
    - Sell 1 OTM put
    - Sell 1 OTM call
    - Buy 1 OTM call (at a higher strike)
    - All options have the same expiration (30-60 DTE)

- Put Broken Wing Butterfly (Put BWB)
    - Buy 1 ITM put (near ATM)
    - Sell 2 OTM puts (just below ATM)
    - Skip the next strike price
    - Buy 1 OTM put
    - All options have the same expiration (30-60 DTE)

- Put Credit Spread
    - Sell 1 OTM put
    - Buy 1 OTM put (at a lower strike)
    - All options have the same expiration (30-60 DTE)

- Short Naked Put
    - Sell 1 OTM put
    - All options have the same expiration (30-60 DTE)

- Call Backspread
    - Sell 1 ATM call (or just below ATM)
    - Buy 2 OTM calls (at a higher strike but near ATM)
    - All options have the same expiration (60-90 DTE)

- Call Calendar Spread
    - Sell 1 OTM call (with shorter expiration)
    - Buy 1 OTM call (with longer expiration)
    - All options have the same strike price
    - Shorter expiration is 20-45 DTE
    - Longer expiration = shorter expiration + 30 DTE

- Call Debit Spread
    - Buy 1 ITM call
    - Sell 1 OTM call (at a higher strike)
    - All options have the same expiration (60-90 DTE)

- Put Diagonal Spread
    - Sell 1 OTM put (with shorter expiration)
    - Buy 1 OTM put (at a lower strike, with longer expiration)
    - Shorter expiration is 20-45 DTE
    - Longer expiration = shorter expiration + 30 DTE

#### Neutral

- Iron Butterfly
    - Sell 1 ATM put
    - Buy 1 OTM put (at a lower strike)
    - Sell 1 ATM call
    - Buy 1 OTM call (at a higher strike)
    - All options have the same expiration (30-60 DTE)

- Iron Condor
    - Sell 1 OTM put
    - Buy 1 OTM put (at a lower strike)
    - Sell 1 OTM call
    - Buy 1 OTM call (at a higher strike)
    - All options have the same expiration (30-60 DTE)

- Short Straddle
    - Sell 1 ATM put
    - Sell 1 ATM call
    - All options have the same expiration (30-60 DTE)

- Short Strangle
    - Sell 1 OTM put
    - Sell 1 OTM call
    - All options have the same expiration (30-60 DTE)

#### Bearish

- Reverse Jade Lizard (Custom Naked Call)
    - Sell 1 OTM call
    - Sell 1 OTM put
    - Buy 1 OTM put (at a lower strike)
    - All options have the same expiration (30-60 DTE)

- Call Broken Wing Butterfly (Call BWB)
    - Buy 1 ITM call (near ATM)
    - Sell 2 OTM calls (just above ATM)
    - Skip the next strike price
    - Buy 1 OTM call
    - All options have the same expiration (30-60 DTE)

- Call Credit Spread
    - Sell 1 OTM call
    - Buy 1 OTM call (at a higher strike)
    - All options have the same expiration (30-60 DTE)

- Short Naked Call
    - Sell 1 OTM call
    - All options have the same expiration (30-60 DTE)

- Put Backspread
    - Sell 1 ATM put (or just above ATM)
    - Buy 2 OTM puts (at a lower strike but near ATM)
    - All options have the same expiration (60-90 DTE)

- Put Calendar Spread
    - Sell 1 OTM put (with shorter expiration)
    - Buy 1 OTM put (with longer expiration)
    - All options have the same strike price
    - Shorter expiration is 20-45 DTE
    - Longer expiration = shorter expiration + 30 DTE

- Put Debit Spread
    - Buy 1 ITM put
    - Sell 1 OTM put (at a lower strike)
    - All options have the same expiration (60-90 DTE)

- Call Diagonal Spread
    - Sell 1 OTM call (with shorter expiration)
    - Buy 1 OTM call (at a higher strike, with longer expiration)
    - Shorter expiration is 20-45 DTE
    - Longer expiration = shorter expiration + 30 DTE

### Analysis Process

The analysis occurs in the following steps:
1. The user inputs a comma-separated list of ticker symbols.
2. The `IV_Solver` script is called to solve for the implied volatility of each ticker.
3. Some basic account information is fetched (used for position sizing).
4. Expiration dates are calculated.
5. For each ticker, the following is performed:
    1. The current price and market beta are fetched.
    2. The options chain is fetched (lists all options & their details for each expiration).
    3. All possible spreads are constructed (using the types given above).
    4. The `Metrics` script is called to analyze each spread.
    5. The spreads are filtered to meet certain requirements.
6. The best spreads are written to a file, which is opened automatically for the user.

## Main Scripts
1. `IV_Solver`
    - Solves for the implied volatility of a particular stock.
    - Based on the Black-Scholes formula.

2. `Metrics`
    - Used to evaluate potential spreads to find the best trades.
    - Calculates the following metrics for a particular options spread:
        - Maximum profit
        - Expected payoff
        - Probability of profit
        - Total delta
        - Total theta
        - Beta-weighted delta
        - Break-even price(s)
        - Maximum risk
        - Return on capital per day
        - Theta efficiency

3. `Options Analysis`
    - This is the main script.
    - Takes user input, calls scripts to perform analysis, and writes outputs to a file.

4. `Spread_Constructor`
    - For each type of options strategy, it constructs all the possible trades.

## Getting Started

### Prerequisites

The following non-standard Python libraries are required to run this project:
1. `tda`
2. `scipy`

## Usage

To run the project, simply open the command line, navigate to the directory containing the project files, and run the following command:

        python3 "Options Analysis".py