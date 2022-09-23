# https://en.bitcoin.it/wiki/List_of_address_prefixes
address_prefix = bytes([78])  # PrefixがYになるように
address_base_bytes = b"security mini camp yamanashi address"
block_time_span = 10
retarget_block_count = 5
retarget_time_span = block_time_span * retarget_block_count
min_bits = 0x1f00ffff
genesis_bits = 0x1f00ffff
genesis_message = "security mini camp yamanashi original blockchain"
miner_name = "security mini camp yamanashi"
