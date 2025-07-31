# Blockchain Node Configuration
NODE_PORT = 8765

# Mining Parameters
DIFFICULTY = 2 # Number of leading zeros required for block hash (e.g., "00")
BLOCK_REWARD = 50 # PHN per block

# Token Supply (conceptual total)
TOTAL_SUPPLY = 100_000_000 # 100 million PHN

# Owner Allocation at Genesis (10% of TOTAL_SUPPLY)
OWNER_ALLOCATION = int(TOTAL_SUPPLY * 0.10) # 10 million PHN

# Minable Supply (remaining after owner allocation)
MINABLE_SUPPLY = TOTAL_SUPPLY - OWNER_ALLOCATION
